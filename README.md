# 实验三：基于卷积神经网络的 MNIST 手写数字图片噪声处理

使用 PyTorch 搭建一个**卷积去噪自编码器（Convolutional Denoising Autoencoder）**，
对 MNIST 手写数字图像进行去噪：以加噪图像为网络输入，以原始干净图像为目标输出，
通过卷积神经网络学习从噪声图像到干净图像的映射。

## 目录结构

```
.
├── src/
│   ├── data.py      # 读取 MNIST，添加高斯噪声（输入数据与目标输出数据）
│   ├── model.py     # 卷积去噪自编码器网络结构
│   ├── metrics.py   # 评价指标：MSE / PSNR / SSIM
│   └── main.py      # 训练、测试、结果输出（损失曲线、对比图、指标）
├── report/
│   ├── 实验报告.md   # 实验报告
│   └── figures/     # 报告所用图（损失曲线、去噪对比图、指标）
├── requirements.txt
└── README.md
```

## 环境依赖

```bash
pip install -r requirements.txt
```

主要依赖：`torch`、`torchvision`、`numpy`、`matplotlib`、`scikit-image`。

## 运行

```bash
python src/main.py --epochs 15 --batch-size 128 --lr 1e-3 --noise-factor 0.5
```

常用参数：

| 参数 | 含义 | 默认值 |
| --- | --- | --- |
| `--epochs` | 训练迭代轮数 | 10 |
| `--batch-size` | 批大小 | 128 |
| `--lr` | 学习率（Adam 优化器） | 1e-3 |
| `--noise-factor` | 高斯噪声强度 | 0.5 |
| `--data-dir` | MNIST 下载/缓存目录 | `data` |
| `--output-dir` | 结果输出目录 | `outputs` |

运行后会在 `outputs/` 下生成：

- `training_loss.png`：训练损失曲线
- `denoise_samples.png`：干净 / 加噪 / 去噪对比图
- `metrics.json`：超参数与测试指标
- `denoising_cnn.pth`：训练好的模型权重

> 首次运行会自动通过 `torchvision` 下载 MNIST 数据集到 `data/` 目录。

## 实验结果（15 epochs，noise_factor=0.5，CPU）

| 指标 | 加噪输入（基线） | 去噪输出 |
| --- | --- | --- |
| PSNR | 9.38 dB | **19.48 dB** |
| SSIM | — | **0.831** |
| MSE | — | 0.0121 |

详见 [实验报告](report/实验报告.md)。
