"""基于卷积神经网络(CNN)的 MNIST 手写数字识别。

实验流程：
    1. 读取数据（输入数据与目标输出数据）
    2. 创建卷积神经网络模型
    3. 训练网络
    4. 测试网络
    5. 结果输出与分析（损失/精度曲线、混淆矩阵、预测示例、模型保存）

用法：
    python train_mnist_cnn.py --epochs 10 --batch-size 64 --lr 0.001
"""

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class CNN(nn.Module):
    """一个用于 MNIST(28x28 单通道) 的简单卷积神经网络。

    结构：
        Conv(1->32,3x3) -> ReLU -> MaxPool(2x2)   28x28 -> 14x14
        Conv(32->64,3x3) -> ReLU -> MaxPool(2x2)  14x14 -> 7x7
        Flatten -> FC(64*7*7->128) -> ReLU -> Dropout(0.5)
        FC(128->10)
    """

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)


def get_dataloaders(data_dir: str, batch_size: int):
    """读取 MNIST 数据集，返回训练/测试 DataLoader。"""
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),  # MNIST 全局均值/方差
        ]
    )
    train_ds = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    test_ds = datasets.MNIST(data_dir, train=False, download=True, transform=transform)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=1000, shuffle=False)
    return train_loader, test_loader, test_ds


def train_one_epoch(model, device, loader, optimizer, criterion):
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    for images, targets in loader:
        images, targets = images.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        correct += (outputs.argmax(1) == targets).sum().item()
        total += targets.size(0)
    return running_loss / total, correct / total


@torch.no_grad()
def evaluate(model, device, loader, criterion):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    all_preds, all_targets = [], []
    for images, targets in loader:
        images, targets = images.to(device), targets.to(device)
        outputs = model(images)
        loss = criterion(outputs, targets)

        running_loss += loss.item() * images.size(0)
        preds = outputs.argmax(1)
        correct += (preds == targets).sum().item()
        total += targets.size(0)
        all_preds.append(preds.cpu())
        all_targets.append(targets.cpu())
    preds = torch.cat(all_preds)
    targets = torch.cat(all_targets)
    return running_loss / total, correct / total, preds, targets


def plot_curves(history, out_path: Path):
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(epochs, history["train_loss"], "o-", label="Train")
    ax1.plot(epochs, history["test_loss"], "s-", label="Test")
    ax1.set_title("Loss vs Epoch")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(epochs, [a * 100 for a in history["train_acc"]], "o-", label="Train")
    ax2.plot(epochs, [a * 100 for a in history["test_acc"]], "s-", label="Test")
    ax2.set_title("Accuracy vs Epoch")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy (%)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_confusion_matrix(preds, targets, out_path: Path, num_classes: int = 10):
    cm = torch.zeros(num_classes, num_classes, dtype=torch.int64)
    for t, p in zip(targets, preds):
        cm[t.item(), p.item()] += 1
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax)
    ax.set_title("Confusion Matrix (Test Set)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_xticks(range(num_classes))
    ax.set_yticks(range(num_classes))
    thresh = cm.max().item() / 2
    for i in range(num_classes):
        for j in range(num_classes):
            ax.text(
                j,
                i,
                int(cm[i, j].item()),
                ha="center",
                va="center",
                color="white" if cm[i, j].item() > thresh else "black",
                fontsize=7,
            )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return cm


def plot_sample_predictions(model, device, test_ds, out_path: Path, n: int = 12):
    model.eval()
    fig, axes = plt.subplots(3, 4, figsize=(8, 6))
    for ax, idx in zip(axes.ravel(), range(n)):
        image, label = test_ds[idx]
        with torch.no_grad():
            pred = model(image.unsqueeze(0).to(device)).argmax(1).item()
        ax.imshow(image.squeeze(0).numpy(), cmap="gray")
        color = "green" if pred == label else "red"
        ax.set_title(f"pred={pred}, true={label}", color=color, fontsize=9)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="CNN for MNIST handwritten digit recognition")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--data-dir", type=str, default="./data")
    parser.add_argument("--out-dir", type=str, default="./outputs")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    out_dir = Path(args.out_dir)
    fig_dir = Path("report/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print(f"Device: {device}")
    train_loader, test_loader, test_ds = get_dataloaders(args.data_dir, args.batch_size)

    model = CNN().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(model)
    print(f"Trainable parameters: {n_params:,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    history = {"train_loss": [], "train_acc": [], "test_loss": [], "test_acc": []}
    best_acc = 0.0
    start = time.time()
    for epoch in range(1, args.epochs + 1):
        tr_loss, tr_acc = train_one_epoch(model, device, train_loader, optimizer, criterion)
        te_loss, te_acc, preds, targets = evaluate(model, device, test_loader, criterion)
        history["train_loss"].append(tr_loss)
        history["train_acc"].append(tr_acc)
        history["test_loss"].append(te_loss)
        history["test_acc"].append(te_acc)
        best_acc = max(best_acc, te_acc)
        print(
            f"Epoch {epoch:2d}/{args.epochs} | "
            f"train_loss={tr_loss:.4f} train_acc={tr_acc*100:.2f}% | "
            f"test_loss={te_loss:.4f} test_acc={te_acc*100:.2f}%"
        )
    elapsed = time.time() - start

    # 最终评估与结果输出
    final_loss, final_acc, preds, targets = evaluate(model, device, test_loader, criterion)
    print("=" * 60)
    print(f"Final test accuracy: {final_acc*100:.2f}%  (best: {best_acc*100:.2f}%)")
    print(f"Total training time: {elapsed:.1f}s on {device}")
    print("=" * 60)

    plot_curves(history, fig_dir / "training_curves.png")
    plot_confusion_matrix(preds, targets, fig_dir / "confusion_matrix.png")
    plot_sample_predictions(model, device, test_ds, fig_dir / "sample_predictions.png")

    torch.save(model.state_dict(), out_dir / "mnist_cnn.pt")
    summary = {
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "optimizer": "Adam",
        "loss": "CrossEntropyLoss",
        "device": str(device),
        "trainable_params": n_params,
        "final_test_acc": final_acc,
        "best_test_acc": best_acc,
        "final_test_loss": final_loss,
        "train_time_sec": elapsed,
        "history": history,
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Saved model -> {out_dir/'mnist_cnn.pt'}")
    print(f"Saved figures -> {fig_dir}")
    print(f"Saved summary -> {out_dir/'summary.json'}")


if __name__ == "__main__":
    main()
