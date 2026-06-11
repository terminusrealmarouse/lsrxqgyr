"""相位提取人工神经网络实验 (PyTorch)

实验内容:
    测量信号中,相位 x 与强度信号 y 存在理论对应关系:
        y = 0.5 + 0.3 * cos(x) + eps,  x in (0, pi)
    其中 eps 为高斯噪声。

    由于 cos(x) 在 (0, pi) 上严格单调递减, 因此 y -> x 是良定义的单射映射,
    适合用神经网络拟合。本脚本以强度 y 为输入, 相位 x 为目标输出, 训练一个
    多层感知机 (MLP) 实现 "输入强度 y, 提取相位 x" 的映射模型。

实验步骤:
    1. 导入(生成)数据: 输入数据 y 与目标输出数据 x;
    2. 创建神经网络模型;
    3. 训练、测试网络;
    4. 应用网络并输出结果(可视化保存为图片)。
"""

import os

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

import matplotlib

matplotlib.use("Agg")  # 无显示环境下保存图片
import matplotlib.pyplot as plt


# ----------------------------- 全局参数设置 ----------------------------- #
SEED = 42
N_SAMPLES = 2000        # 样本数量
NOISE_STD = 0.02        # 噪声标准差 (eps ~ N(0, NOISE_STD^2))
TEST_RATIO = 0.2        # 测试集比例
BATCH_SIZE = 64
EPOCHS = 300
LR = 1e-3               # 学习率
HIDDEN = 64             # 隐藏层神经元数
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


# ----------------------------- 1. 数据生成 ----------------------------- #
def generate_data(n_samples: int, noise_std: float):
    """生成符合 y = 0.5 + 0.3*cos(x) + eps, x in (0, pi) 的数据集。

    返回:
        x: 相位 (目标输出), shape (n, 1)
        y: 强度 (网络输入), shape (n, 1)
    """
    # x 在 (0, pi) 区间均匀采样, 避开端点 0 和 pi
    x = np.random.uniform(low=1e-3, high=np.pi - 1e-3, size=(n_samples, 1))
    eps = np.random.normal(loc=0.0, scale=noise_std, size=(n_samples, 1))
    y = 0.5 + 0.3 * np.cos(x) + eps
    return x.astype(np.float32), y.astype(np.float32)


# ----------------------------- 2. 网络模型 ----------------------------- #
class PhaseNet(nn.Module):
    """以强度 y 为输入, 预测相位 x 的多层感知机。"""

    def __init__(self, hidden: int = HIDDEN):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ----------------------------- 3. 训练与测试 ---------------------------- #
def train(model, train_loader, x_test_t, y_test_t, epochs, lr):
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    train_hist, test_hist = [], []
    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0
        for yb, xb in train_loader:
            optimizer.zero_grad()
            pred = model(yb)
            loss = criterion(pred, xb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * yb.size(0)
        epoch_loss /= len(train_loader.dataset)

        # 测试集评估
        model.eval()
        with torch.no_grad():
            test_pred = model(y_test_t)
            test_loss = criterion(test_pred, x_test_t).item()

        train_hist.append(epoch_loss)
        test_hist.append(test_loss)

        if epoch % 20 == 0 or epoch == 1:
            print(f"Epoch {epoch:4d}/{epochs} | train MSE: {epoch_loss:.6f} | test MSE: {test_loss:.6f}")

    return train_hist, test_hist


# ----------------------------- 4. 结果可视化 ---------------------------- #
def plot_results(x_all, y_all, x_test, y_test, x_pred, train_hist, test_hist, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    # 图1: 数据集分布 (相位 x vs 强度 y)
    plt.figure(figsize=(6, 4.5))
    plt.scatter(x_all, y_all, s=6, alpha=0.4, label="noisy samples")
    xs = np.linspace(1e-3, np.pi - 1e-3, 300)
    plt.plot(xs, 0.5 + 0.3 * np.cos(xs), "r-", lw=2, label="theory: y=0.5+0.3cos(x)")
    plt.xlabel("phase x")
    plt.ylabel("intensity y")
    plt.title("Dataset: y = 0.5 + 0.3 cos(x) + eps")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "01_dataset.png"), dpi=150)
    plt.close()

    # 图2: 训练/测试损失曲线
    plt.figure(figsize=(6, 4.5))
    plt.plot(train_hist, label="train MSE")
    plt.plot(test_hist, label="test MSE")
    plt.xlabel("epoch")
    plt.ylabel("MSE loss")
    plt.yscale("log")
    plt.title("Training / Test Loss")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "02_loss.png"), dpi=150)
    plt.close()

    # 图3: 测试集上 预测相位 vs 真实相位
    order = np.argsort(y_test.ravel())
    plt.figure(figsize=(6, 4.5))
    plt.scatter(x_test, x_pred, s=10, alpha=0.5, label="pred vs true")
    lo = min(x_test.min(), x_pred.min())
    hi = max(x_test.max(), x_pred.max())
    plt.plot([lo, hi], [lo, hi], "r--", lw=2, label="ideal y=x")
    plt.xlabel("true phase x")
    plt.ylabel("predicted phase x")
    plt.title("Test set: predicted vs true phase")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "03_pred_vs_true.png"), dpi=150)
    plt.close()

    # 图4: 网络学到的反映射 x = f(y)
    plt.figure(figsize=(6, 4.5))
    plt.scatter(y_test, x_test, s=8, alpha=0.3, label="true (y, x)")
    plt.scatter(y_test[order], x_pred[order], s=8, c="orange", alpha=0.6, label="network pred x=f(y)")
    plt.xlabel("intensity y (network input)")
    plt.ylabel("phase x (retrieved)")
    plt.title("Learned inverse mapping x = f(y)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "04_inverse_mapping.png"), dpi=150)
    plt.close()

    print(f"\n[OK] result figures saved to: {out_dir}")


def main():
    set_seed(SEED)

    # ---- 1. 数据 ----
    x_all, y_all = generate_data(N_SAMPLES, NOISE_STD)
    n_test = int(N_SAMPLES * TEST_RATIO)
    idx = np.random.permutation(N_SAMPLES)
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    x_train, y_train = x_all[train_idx], y_all[train_idx]
    x_test, y_test = x_all[test_idx], y_all[test_idx]

    # 转为张量: 网络输入为强度 y, 目标输出为相位 x
    y_train_t = torch.from_numpy(y_train)
    x_train_t = torch.from_numpy(x_train)
    y_test_t = torch.from_numpy(y_test)
    x_test_t = torch.from_numpy(x_test)

    train_loader = DataLoader(
        TensorDataset(y_train_t, x_train_t), batch_size=BATCH_SIZE, shuffle=True
    )

    # ---- 2. 模型 ----
    model = PhaseNet(HIDDEN)
    print(model)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Trainable parameters: {n_params}\n")

    # ---- 3. 训练与测试 ----
    train_hist, test_hist = train(model, train_loader, x_test_t, y_test_t, EPOCHS, LR)

    # ---- 4. 应用网络: 提取相位 ----
    model.eval()
    with torch.no_grad():
        x_pred = model(y_test_t).numpy()

    mae = np.mean(np.abs(x_pred - x_test))
    rmse = np.sqrt(np.mean((x_pred - x_test) ** 2))
    print(f"\n[Test set] MAE = {mae:.4f} rad,  RMSE = {rmse:.4f} rad")
    print(f"[Final]    train MSE = {train_hist[-1]:.6f},  test MSE = {test_hist[-1]:.6f}")

    # 演示: 给定若干强度值, 提取对应相位
    demo_y = np.array([[0.2], [0.5], [0.8]], dtype=np.float32)
    with torch.no_grad():
        demo_x = model(torch.from_numpy(demo_y)).numpy()
    print("\nApplication demo (input intensity y -> retrieved phase x):")
    for yi, xi in zip(demo_y.ravel(), demo_x.ravel()):
        true_x = np.arccos((yi - 0.5) / 0.3) if -0.3 <= (yi - 0.5) <= 0.3 else float("nan")
        print(f"  y = {yi:.3f}  ->  pred x = {xi:.4f} rad  (analytic x = {true_x:.4f} rad)")

    plot_results(x_all, y_all, x_test, y_test, x_pred, train_hist, test_hist, OUT_DIR)


if __name__ == "__main__":
    main()
