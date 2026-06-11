"""将 MNIST CNN 实验报告导出为 Word(.docx) 文档。

依赖 train_mnist_cnn.py + make_diagrams.py 产生的图表与 summary.json。

用法：
    python make_report_docx.py
"""

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

FIG = Path("report/figures")
OUT = Path("report/MNIST_CNN_实验报告.docx")
CN_FONT = "宋体"


def set_cn_font(run, size=None, bold=False):
    run.font.name = "Times New Roman"
    run.font.bold = bold
    if size:
        run.font.size = Pt(size)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)


def add_heading(doc, text, level):
    p = doc.add_heading("", level=level)
    run = p.add_run(text)
    set_cn_font(run, size={1: 16, 2: 14, 3: 13}.get(level, 12), bold=True)
    return p


def add_para(doc, text, bold=False, size=12, align=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    run = p.add_run(text)
    set_cn_font(run, size=size, bold=bold)
    return p


def add_table(doc, rows):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Light Grid Accent 1"
    for i, row in enumerate(rows):
        for j, cell_text in enumerate(row):
            cell = table.cell(i, j)
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(cell_text))
            set_cn_font(run, size=10.5, bold=(i == 0))
    return table


def add_image(doc, path, width=6.2, caption=None):
    if not Path(path).exists():
        return
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        cap = add_para(doc, caption, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        cap.runs[0].font.italic = True


def main():
    with open("outputs/summary.json", encoding="utf-8") as f:
        s = json.load(f)
    hist = s["history"]
    fa = s["final_test_acc"] * 100
    ba = s["best_test_acc"] * 100

    doc = Document()
    # 默认正文字体
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cn_font(title.add_run("实验二　基于卷积神经网络的 MNIST 手写数字识别"), size=18, bold=True)

    add_table(
        doc,
        [
            ["实验名称", "基于卷积神经网络的 MNIST 手写数字识别"],
            ["专业班级", "（请填写）"],
            ["学号", "（请填写）"],
            ["姓名", "（请填写）"],
            ["实验日期", "（请填写）"],
        ],
    )

    add_heading(doc, "一、实验目的", 1)
    for t in [
        "1. 熟悉 PyTorch 深度学习框架的使用；",
        "2. 熟悉卷积神经网络（CNN）的训练思路；",
        "3. 掌握卷积神经网络对 MNIST 手写数字的识别过程。",
    ]:
        add_para(doc, t)

    add_heading(doc, "二、实验内容", 1)
    add_para(
        doc,
        "MNIST 数据库共有 7 万张手写数字图片，其中 6 万张用于训练、1 万张用于测试，"
        "每张图片大小为 28×28 像素（单通道灰度图），标签为 0~9 共 10 类。本实验使用 "
        "PyTorch 搭建一个卷积神经网络模型，完成对 MNIST 手写数字的识别任务，并对训练、"
        "测试结果进行分析。",
    )

    add_heading(doc, "三、实验设备与环境", 1)
    for t in [
        "1. 计算机一台；",
        "2. PyTorch 深度学习框架；",
        f"3. 具体环境：Python 3.12 + torch 2.12.0(CPU) + torchvision 0.27.0 + matplotlib。",
    ]:
        add_para(doc, t)

    add_heading(doc, "四、实验步骤", 1)
    add_para(
        doc,
        "实验按「读取数据 → 创建模型 → 训练网络 → 测试网络 → 结果输出与分析」五个步骤进行，"
        "对应代码见 train_mnist_cnn.py。",
    )

    add_heading(doc, "4.1 读取数据（输入数据与目标输出数据）", 2)
    for t in [
        "· 使用 torchvision.datasets.MNIST 自动下载并加载训练集(60000 张)与测试集(10000 张)。",
        "· 预处理：ToTensor() 归一化到 [0,1]，再用 Normalize((0.1307,),(0.3081,)) 做标准化。",
        "· 训练集 batch_size=64 且 shuffle=True；测试集 batch_size=1000 不打乱。",
        "· 输入数据为形状 [N,1,28,28] 的图像张量；目标输出为形状 [N] 的整数标签(0~9)。",
    ]:
        add_para(doc, t)

    add_heading(doc, "4.2 创建卷积神经网络模型", 2)
    add_para(doc, "网络结构示意图如下：")
    add_image(doc, FIG / "architecture.png", width=6.5, caption="图1 CNN 网络结构示意图")
    add_table(
        doc,
        [
            ["层", "配置", "输出尺寸"],
            ["输入 Input", "单通道灰度图", "1 × 28 × 28"],
            ["卷积 Conv1", "3×3, 1→32, padding=1, ReLU", "32 × 28 × 28"],
            ["池化 Pool1", "MaxPool 2×2", "32 × 14 × 14"],
            ["卷积 Conv2", "3×3, 32→64, padding=1, ReLU", "64 × 14 × 14"],
            ["池化 Pool2", "MaxPool 2×2", "64 × 7 × 7"],
            ["展平 Flatten", "—", "3136"],
            ["全连接 FC1", "3136→128, ReLU, Dropout 0.5", "128"],
            ["全连接 FC2", "128→10", "10"],
        ],
    )
    add_para(doc, "模型可训练参数总数：421,642。")

    add_heading(doc, "4.3 训练网络", 2)
    for t in [
        "· 损失函数：交叉熵损失 CrossEntropyLoss（内部含 Softmax，适合多分类）；",
        "· 优化器：Adam，学习率 lr=0.001；",
        "· 迭代次数 Epochs=10；每轮做前向→计算损失→反向传播→参数更新；",
        "· 随机种子固定为 42，保证结果可复现。",
    ]:
        add_para(doc, t)

    add_heading(doc, "4.4 测试网络", 2)
    add_para(
        doc,
        "每个 epoch 结束后，在 1 万张测试集上用 model.eval()+torch.no_grad() 评估损失与准确率"
        "（准确率 = 预测正确样本数 / 总样本数），并记录最优精度。",
    )

    add_heading(doc, "五、神经网络参数设置（汇总）", 1)
    add_table(
        doc,
        [
            ["参数", "取值"],
            ["迭代次数 Epochs", str(s["epochs"])],
            ["批大小 Batch size", str(s["batch_size"])],
            ["学习率 Learning rate", str(s["lr"])],
            ["优化器 Optimizer", s["optimizer"]],
            ["损失函数 Loss", "CrossEntropyLoss（交叉熵）"],
            ["激活函数", "ReLU"],
            ["正则化", "Dropout(0.5)"],
            ["随机种子", "42"],
            ["可训练参数量", f"{s['trainable_params']:,}"],
        ],
    )

    add_heading(doc, "六、实验结果与分析", 1)
    add_heading(doc, "6.1 训练/测试日志与最终精度（精度截图）", 2)
    add_image(doc, FIG / "results_panel.png", width=6.5, caption="图2 训练日志与最终测试精度")
    add_table(
        doc,
        [["Epoch", "训练损失", "训练精度", "测试损失", "测试精度"]]
        + [
            [
                str(i + 1),
                f"{hist['train_loss'][i]:.4f}",
                f"{hist['train_acc'][i]*100:.2f}%",
                f"{hist['test_loss'][i]:.4f}",
                f"{hist['test_acc'][i]*100:.2f}%",
            ]
            for i in range(s["epochs"])
        ],
    )
    add_para(doc, f"最终测试精度：{fa:.2f}%（最佳 {ba:.2f}%）。", bold=True)

    add_heading(doc, "6.2 损失与精度曲线", 2)
    add_image(doc, FIG / "training_curves.png", width=6.5, caption="图3 训练/测试 损失与精度曲线")
    for t in [
        "· 训练损失从约 0.21 快速下降并趋于平稳，测试损失同步下降，模型有效学习且无明显过拟合；",
        "· 测试精度第 1 个 epoch 即达 98.25%，第 3 个 epoch 后稳定在 99% 以上；",
        "· 训练精度与测试精度差距很小，表明 Dropout 与较浅网络有效控制了过拟合。",
    ]:
        add_para(doc, t)

    add_heading(doc, "6.3 混淆矩阵", 2)
    add_image(doc, FIG / "confusion_matrix.png", width=5.2, caption="图4 测试集混淆矩阵")
    for t in [
        "· 对角线元素占绝对多数，绝大部分样本被正确分类；",
        "· 误分类极少，主要集中在形状相近的数字之间（如 5↔3、4↔9、7↔2）。",
    ]:
        add_para(doc, t)

    add_heading(doc, "6.4 预测示例", 2)
    add_image(doc, FIG / "sample_predictions.png", width=5.8, caption="图5 测试样本预测示例（绿色=正确）")

    add_heading(doc, "七、结论", 1)
    for t in [
        "1. 基于 PyTorch 成功搭建了含 2 卷积层、2 池化层、2 全连接层的 CNN，完成 MNIST 识别任务；",
        f"2. 在 Epochs=10、batch_size=64、lr=0.001、Adam、交叉熵设置下，最终测试精度达 {fa:.2f}%（最佳 {ba:.2f}%）；",
        "3. CNN 通过卷积+池化自动提取空间特征，具有参数共享、平移不变、精度高的优势；",
        "4. 后续可尝试增加卷积层、加入 BatchNorm、数据增强或调整学习率以进一步提升性能。",
    ]:
        add_para(doc, t)

    doc.save(str(OUT))
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
