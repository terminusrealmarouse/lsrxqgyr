# 基于卷积神经网络的 MNIST 手写数字识别

使用 PyTorch 搭建卷积神经网络（CNN）完成 MNIST 手写数字（0~9）识别任务。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `train_mnist_cnn.py` | 主程序：读取数据 → 创建模型 → 训练 → 测试 → 输出结果与图表 |
| `make_diagrams.py` | 生成网络结构示意图与测试结果面板（供报告使用） |
| `report/MNIST_CNN_实验报告.md` | 实验报告（网络结构、参数设置、结果分析、精度截图） |
| `report/figures/` | 报告中使用的全部图表 |
| `requirements.txt` | 依赖列表 |

## 快速开始

```bash
pip install -r requirements.txt
# CPU/GPU 自动识别；首次运行会自动下载 MNIST 数据集
python train_mnist_cnn.py --epochs 10 --batch-size 64 --lr 0.001
python make_diagrams.py
```

可调参数：`--epochs`、`--batch-size`、`--lr`、`--data-dir`、`--out-dir`、`--seed`。

## 网络结构

```
Input(1x28x28)
  -> Conv(1->32,3x3)+ReLU -> MaxPool2x2   (32x14x14)
  -> Conv(32->64,3x3)+ReLU -> MaxPool2x2  (64x7x7)
  -> Flatten(3136) -> FC(3136->128)+ReLU+Dropout(0.5)
  -> FC(128->10)
```

## 参数设置

| 参数 | 取值 |
| --- | --- |
| 迭代次数 Epochs | 10 |
| 批大小 Batch size | 64 |
| 学习率 Learning rate | 0.001 |
| 优化器 | Adam |
| 损失函数 | CrossEntropyLoss（交叉熵） |

## 实验结果

10 个 epoch 后，模型在 10000 张测试图片上达到 **99.35%（最佳 99.36%）** 的识别精度。详见 [实验报告](report/MNIST_CNN_实验报告.md)。
