"""Train and evaluate a convolutional neural network for MNIST image denoising.

Pipeline (mirrors the experiment steps):
    1. Read data        -> clean MNIST images (target) + Gaussian-noised copies (input)
    2. Build model      -> convolutional autoencoder (see model.py)
    3. Train network    -> Adam optimiser, MSE loss
    4. Test network     -> MSE / PSNR / SSIM on the held-out test set
    5. Output & analyse -> loss curve, before/after comparison grid, metrics file

Example:
    python src/main.py --epochs 10 --batch-size 128 --lr 1e-3 --noise-factor 0.5
"""
from __future__ import annotations

import argparse
import json
import os
import time

import sys

# Ensure sibling modules are importable even when the interpreter runs with
# safe-path enabled (which skips adding the script directory to sys.path).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib

matplotlib.use("Agg")  # headless backend so figures save without a display
import matplotlib.pyplot as plt
import torch
from torch import nn

from data import add_gaussian_noise, get_mnist_loaders
from metrics import batch_mse, batch_psnr, batch_ssim
from model import DenoisingCNN


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MNIST CNN image denoising")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--noise-factor", type=float, default=0.5)
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--output-dir", type=str, default="outputs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    return parser.parse_args()


def train(args: argparse.Namespace, model: nn.Module, train_loader, device) -> list[float]:
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    epoch_losses: list[float] = []
    model.train()
    for epoch in range(1, args.epochs + 1):
        running_loss, n_batches = 0.0, 0
        start = time.time()
        for clean, _ in train_loader:
            clean = clean.to(device)
            noisy = add_gaussian_noise(clean, args.noise_factor)

            optimizer.zero_grad()
            output = model(noisy)
            loss = criterion(output, clean)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            n_batches += 1

        avg_loss = running_loss / n_batches
        epoch_losses.append(avg_loss)
        print(
            f"Epoch {epoch:2d}/{args.epochs} | train MSE {avg_loss:.6f} "
            f"| {time.time() - start:.1f}s"
        )
    return epoch_losses


@torch.no_grad()
def evaluate(args: argparse.Namespace, model: nn.Module, test_loader, device) -> dict:
    model.eval()
    mse_sum = psnr_sum = ssim_sum = 0.0
    noisy_psnr_sum = 0.0
    n = 0
    for clean, _ in test_loader:
        clean = clean.to(device)
        noisy = add_gaussian_noise(clean, args.noise_factor)
        output = model(noisy)

        mse_sum += batch_mse(output, clean)
        psnr_sum += batch_psnr(output, clean)
        ssim_sum += batch_ssim(output, clean)
        noisy_psnr_sum += batch_psnr(noisy, clean)  # baseline: noisy vs clean
        n += 1

    return {
        "test_mse": mse_sum / n,
        "test_psnr": psnr_sum / n,
        "test_ssim": ssim_sum / n,
        "noisy_input_psnr": noisy_psnr_sum / n,
    }


@torch.no_grad()
def save_comparison_grid(args, model, test_loader, device, n_show: int = 8) -> str:
    model.eval()
    clean, _ = next(iter(test_loader))
    clean = clean[:n_show].to(device)
    noisy = add_gaussian_noise(clean, args.noise_factor)
    denoised = model(noisy)

    clean = clean.cpu().numpy()
    noisy = noisy.cpu().numpy()
    denoised = denoised.cpu().numpy()

    rows = [("Clean (target)", clean), ("Noisy (input)", noisy), ("Denoised (output)", denoised)]
    fig, axes = plt.subplots(3, n_show, figsize=(n_show * 1.4, 4.6))
    for r, (label, batch) in enumerate(rows):
        for c in range(n_show):
            ax = axes[r, c]
            ax.imshow(batch[c, 0], cmap="gray", vmin=0.0, vmax=1.0)
            ax.set_xticks([])
            ax.set_yticks([])
            if c == 0:
                ax.set_ylabel(label, fontsize=10)
    fig.suptitle("MNIST denoising: clean vs noisy vs denoised", fontsize=12)
    fig.tight_layout()
    path = os.path.join(args.output_dir, "denoise_samples.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def save_loss_curve(args, losses: list[float]) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(range(1, len(losses) + 1), losses, marker="o")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Training MSE loss")
    ax.set_title("Training loss curve")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = os.path.join(args.output_dir, "training_loss.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    os.makedirs(args.output_dir, exist_ok=True)

    device = torch.device(args.device)
    print(f"Using device: {device}")

    train_loader, test_loader = get_mnist_loaders(args.data_dir, args.batch_size)

    model = DenoisingCNN().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {n_params:,}")

    losses = train(args, model, train_loader, device)
    metrics = evaluate(args, model, test_loader, device)

    print("\n=== Test results ===")
    print(f"Noisy input PSNR (baseline): {metrics['noisy_input_psnr']:.2f} dB")
    print(f"Denoised MSE : {metrics['test_mse']:.6f}")
    print(f"Denoised PSNR: {metrics['test_psnr']:.2f} dB")
    print(f"Denoised SSIM: {metrics['test_ssim']:.4f}")

    loss_path = save_loss_curve(args, losses)
    grid_path = save_comparison_grid(args, model, test_loader, device)
    model_path = os.path.join(args.output_dir, "denoising_cnn.pth")
    torch.save(model.state_dict(), model_path)

    summary = {
        "hyperparameters": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.lr,
            "noise_factor": args.noise_factor,
            "optimizer": "Adam",
            "loss": "MSELoss",
            "device": str(device),
        },
        "num_parameters": n_params,
        "epoch_losses": losses,
        "metrics": metrics,
        "artifacts": {
            "loss_curve": loss_path,
            "comparison_grid": grid_path,
            "model_weights": model_path,
        },
    }
    with open(os.path.join(args.output_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nSaved loss curve     -> {loss_path}")
    print(f"Saved comparison grid-> {grid_path}")
    print(f"Saved model weights  -> {model_path}")
    print(f"Saved metrics json   -> {os.path.join(args.output_dir, 'metrics.json')}")


if __name__ == "__main__":
    main()
