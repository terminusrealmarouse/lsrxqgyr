"""生成报告用的网络结构示意图和测试精度结果面板。

依赖 train_mnist_cnn.py 运行后产生的 outputs/summary.json。

用法：
    python make_diagrams.py
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FIG_DIR = Path("report/figures")


def draw_architecture(out_path: Path):
    layers = [
        ("Input\n1x28x28", "#cfe8ff"),
        ("Conv 3x3\n1->32\nReLU", "#ffd9b3"),
        ("MaxPool 2x2\n32x14x14", "#d6f5d6"),
        ("Conv 3x3\n32->64\nReLU", "#ffd9b3"),
        ("MaxPool 2x2\n64x7x7", "#d6f5d6"),
        ("Flatten\n3136", "#eeeeee"),
        ("FC 3136->128\nReLU\nDropout 0.5", "#ffe0e0"),
        ("FC 128->10", "#ffe0e0"),
        ("Output\n10 classes", "#cfe8ff"),
    ]
    fig, ax = plt.subplots(figsize=(15, 3.2))
    box_w, box_h, gap = 1.4, 1.4, 0.45
    x = 0
    centers = []
    for text, color in layers:
        box = FancyBboxPatch(
            (x, 0),
            box_w,
            box_h,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            linewidth=1.2,
            edgecolor="#444",
            facecolor=color,
        )
        ax.add_patch(box)
        ax.text(x + box_w / 2, box_h / 2, text, ha="center", va="center", fontsize=8.5)
        centers.append(x + box_w)
        x += box_w + gap

    for i in range(len(layers) - 1):
        arrow = FancyArrowPatch(
            (centers[i], box_h / 2),
            (centers[i] + gap, box_h / 2),
            arrowstyle="-|>",
            mutation_scale=12,
            color="#444",
        )
        ax.add_patch(arrow)

    ax.set_xlim(-0.3, x)
    ax.set_ylim(-0.3, box_h + 0.3)
    ax.axis("off")
    ax.set_title("CNN Architecture for MNIST", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def draw_results_panel(summary: dict, out_path: Path):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axis("off")

    lines = [
        "MNIST CNN -- Training & Test Results",
        "=" * 52,
        f"Optimizer        : {summary['optimizer']}",
        f"Loss function    : {summary['loss']}",
        f"Learning rate    : {summary['lr']}",
        f"Batch size       : {summary['batch_size']}",
        f"Epochs           : {summary['epochs']}",
        f"Trainable params : {summary['trainable_params']:,}",
        f"Device           : {summary['device']}",
        f"Train time (s)   : {summary['train_time_sec']:.1f}",
        "-" * 52,
    ]
    hist = summary["history"]
    for i in range(summary["epochs"]):
        lines.append(
            f"Epoch {i+1:2d}/{summary['epochs']} | "
            f"train_loss={hist['train_loss'][i]:.4f} "
            f"train_acc={hist['train_acc'][i]*100:5.2f}% | "
            f"test_loss={hist['test_loss'][i]:.4f} "
            f"test_acc={hist['test_acc'][i]*100:5.2f}%"
        )
    lines.append("=" * 52)
    lines.append(
        f">>> Final test accuracy : {summary['final_test_acc']*100:.2f}%   "
        f"(best: {summary['best_test_acc']*100:.2f}%)"
    )

    ax.text(
        0.01,
        0.99,
        "\n".join(lines),
        ha="left",
        va="top",
        family="monospace",
        fontsize=10,
        transform=ax.transAxes,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    draw_architecture(FIG_DIR / "architecture.png")
    with open("outputs/summary.json", encoding="utf-8") as f:
        summary = json.load(f)
    draw_results_panel(summary, FIG_DIR / "results_panel.png")
    print(f"Saved architecture.png and results_panel.png to {FIG_DIR}")


if __name__ == "__main__":
    main()
