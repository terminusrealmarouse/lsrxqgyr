# 基于人工神经网络的相位提取实验 (PyTorch)

根据强度信号 `y` 反推相位 `x` 的人工神经网络映射模型。数据集服从:

```
y = 0.5 + 0.3 * cos(x) + ε ,   x ∈ (0, π)
```

其中 `ε` 为高斯噪声。由于 `cos(x)` 在 `(0, π)` 上严格单调,`y → x` 是良定义的单射映射,
可用神经网络拟合。网络输入强度 `y`,输出提取出的相位 `x`。

## 环境依赖

```bash
pip install -r requirements.txt
```

- Python 3.12
- PyTorch (CPU 版即可)
- NumPy
- Matplotlib

## 运行

```bash
python phase_retrieval.py
```

脚本会:

1. 生成数据集(输入 `y`、目标 `x`),并按 8:2 划分训练/测试集;
2. 构建一个 MLP (1-64-64-1, Tanh 激活);
3. 用 Adam + MSE 训练 300 个 epoch,并在测试集上评估;
4. 应用网络提取相位,把结果图保存到 `results/`。

## 输出结果

| 文件 | 说明 |
| --- | --- |
| `results/01_dataset.png` | 数据集分布与理论曲线 |
| `results/02_loss.png` | 训练/测试损失曲线 |
| `results/03_pred_vs_true.png` | 测试集 预测相位 vs 真实相位 |
| `results/04_inverse_mapping.png` | 网络学到的反映射 `x = f(y)` |

完整实验报告见 [`实验报告.md`](实验报告.md)。
