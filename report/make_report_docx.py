"""Generate the experiment report as a Word (.docx) document.

The layout follows the course template "人工智能技术及应用实验报告":
a cover page followed by the fixed sections 实验目的 / 实验内容 / 实验步骤 /
实验设备 / 实验过程 / 小结, using 宋体, three-line tables, figure captions
below figures and table captions above tables.

Reads metrics from report/figures/metrics.json and embeds the figures. Run after
src/main.py has produced the figures:

    python report/make_report_docx.py
"""
from __future__ import annotations

import json
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")

# Chinese font sizes (pt)
SI_HAO = Pt(14)        # 四号  -> 一级标题
XIAO_SI = Pt(12)       # 小四号 -> 二级标题 / 正文
WU_HAO = Pt(10.5)      # 五号  -> 图题 / 表题
ER_HAO = Pt(22)        # 二号  -> 封面大标题
SAN_HAO = Pt(16)       # 三号  -> 封面副标题
CN_FONT = "宋体"
EN_FONT = "Times New Roman"


def set_font(run, size, bold=False, cn=CN_FONT, en=EN_FONT):
    run.font.size = size
    run.font.bold = bold
    run.font.name = en
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), cn)
    rfonts.set(qn("w:ascii"), en)
    rfonts.set(qn("w:hAnsi"), en)


def para(doc, text="", size=XIAO_SI, bold=False, align=None, before=0, after=0,
         cn=CN_FONT, en=EN_FONT, mono=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if text:
        run = p.add_run(text)
        set_font(run, size, bold=bold, cn=cn, en=(("Consolas" if mono else en)))
    return p


def heading1(doc, text):
    # 宋体 四号 粗体，段前段后 0.5 行(~6pt)
    para(doc, text, size=SI_HAO, bold=True, before=6, after=6)


def heading2(doc, text):
    # 宋体 小四号 粗体
    para(doc, text, size=XIAO_SI, bold=True, before=6, after=6)


def body(doc, text):
    p = para(doc, text, size=XIAO_SI)
    p.paragraph_format.first_line_indent = Pt(24)  # 首行缩进 2 字
    p.paragraph_format.line_spacing = 1.5
    return p


def set_cell_text(cell, text, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(text)
    set_font(run, WU_HAO, bold=bold)


def _set_borders(table, top=True, bottom=True, header_bottom_row=0):
    """Render a three-line (三线表) style: outer top/bottom + line under header."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "left", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        if edge in ("top", "bottom"):
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "12")  # ~1.5pt thicker outer lines
        else:
            el.set(qn("w:val"), "none")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)
    # add a single bottom border to the header row's cells
    for cell in table.rows[header_bottom_row].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcB = OxmlElement("w:tcBorders")
        b = OxmlElement("w:bottom")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "6")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        tcB.append(b)
        tcPr.append(tcB)


def three_line_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], h, bold=True)
    for r in rows:
        cells = table.add_row().cells
        for i, val in enumerate(r):
            set_cell_text(cells[i], str(val), bold=False)
    _set_borders(table)
    return table


def table_caption(doc, text):
    para(doc, text, size=WU_HAO, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=6)


def figure(doc, filename, caption, width_in):
    doc.add_picture(os.path.join(FIG_DIR, filename), width=Inches(width_in))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(doc, caption, size=WU_HAO, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)


def load_metrics() -> dict:
    with open(os.path.join(FIG_DIR, "metrics.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def build_cover(doc):
    for _ in range(2):
        para(doc)
    para(doc, "人工智能技术及应用实验报告", size=ER_HAO, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, "（2026年）", size=SAN_HAO, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER)
    for _ in range(5):
        para(doc)
    fields = [
        "实 验 名 称 ： 基于卷积神经网络的 MNIST 手写数字图片噪声处理",
        "专 业 班 级 ：                                    ",
        "学 生 姓 名 ：                  学 生 学 号 ：                 ",
    ]
    for f in fields:
        p = para(doc, f, size=SI_HAO, bold=False)
        p.paragraph_format.space_after = Pt(12)
    doc.add_page_break()


def main() -> None:
    m = load_metrics()
    hp = m["hyperparameters"]
    met = m["metrics"]
    improve = met["test_psnr"] - met["noisy_input_psnr"]

    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = EN_FONT
    normal.font.size = XIAO_SI
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

    build_cover(doc)

    # 1 实验目的
    heading1(doc, "1  实验目的")
    body(doc, "（1）熟悉 PyTorch 深度学习框架的使用；")
    body(doc, "（2）熟悉卷积神经网络的训练思路；")
    body(doc, "（3）掌握卷积神经网络对图像噪声去除的过程。")

    # 2 实验内容
    heading1(doc, "2  实验内容")
    body(doc,
         "现实中的数字图像在数字化和传输过程中常受到成像设备或外部环境噪声干扰，减少图像中噪声"
         "的过程称为图像去噪。本实验以 MNIST 手写数字数据库为训练数据，搭建一个卷积去噪自编码器"
         "（Convolutional Denoising Autoencoder）模型实现图像去噪：在干净图像上叠加高斯噪声得到"
         "“加噪图像”作为网络输入，原始“干净图像”作为目标输出，让网络学习从加噪图像到干净图像"
         "的映射，从而去除噪声。")

    # 3 实验步骤
    heading1(doc, "3  实验步骤")
    for t in [
        "（1）读取数据（输入数据与目标输出数据）；",
        "（2）创建卷积神经网络模型；",
        "（3）训练网络；",
        "（4）测试网络；",
        "（5）结果输出与分析。",
    ]:
        body(doc, t)

    # 4 实验设备
    heading1(doc, "4  实验设备")
    body(doc, "（1）计算机；")
    body(doc, f"（2）PyTorch 深度学习框架（torch 2.12，torchvision；运行设备：{hp['device']}）。")

    # 5 实验过程
    heading1(doc, "5  实验过程")

    heading2(doc, "5.1  数据读取与噪声添加")
    body(doc,
         "使用 torchvision.datasets.MNIST 自动下载数据集（训练集 60000 张、测试集 10000 张，"
         "均为 28×28 单通道灰度图），并用 ToTensor() 将像素归一化到 [0, 1]。噪声采用零均值高斯噪声，"
         "叠加后裁剪回 [0, 1]：noisy = clamp(image + noise_factor × N(0,1), 0, 1)，其中 "
         f"noise_factor = {hp['noise_factor']}。训练时以干净图像为目标、加噪图像为输入。")

    heading2(doc, "5.2  卷积神经网络模型构建")
    body(doc,
         "模型为对称的编码器—解码器结构。编码器用卷积 + 最大池化逐步下采样、提取特征并压缩到低维"
         "表示；解码器用转置卷积逐步上采样、重建去噪后的图像；最后用 Sigmoid 把输出限制到 [0, 1]。"
         "网络结构及各层输出尺寸如表1所示。")
    table_caption(doc, "表1  卷积去噪自编码器网络结构")
    three_line_table(
        doc,
        ["层", "类型", "输出尺寸"],
        [
            ["输入", "—", "1 × 28 × 28"],
            ["Conv1 + ReLU + MaxPool", "卷积 + 池化", "32 × 14 × 14"],
            ["Conv2 + ReLU + MaxPool", "卷积 + 池化", "64 × 7 × 7"],
            ["DeConv1 + ReLU", "转置卷积", "32 × 14 × 14"],
            ["DeConv2 + ReLU", "转置卷积", "16 × 28 × 28"],
            ["Conv3 + Sigmoid", "卷积", "1 × 28 × 28"],
        ],
    )
    body(doc, f"模型可训练参数量为 {m['num_parameters']:,} 个。")

    heading2(doc, "5.3  网络参数设置")
    body(doc, "训练采用 Adam 优化器与均方误差（MSE）损失函数，主要超参数如表2所示。")
    table_caption(doc, "表2  神经网络参数设置")
    three_line_table(
        doc,
        ["参数", "取值"],
        [
            ["迭代次数 (epochs)", hp["epochs"]],
            ["批大小 (batch size)", hp["batch_size"]],
            ["学习率 (learning rate)", hp["learning_rate"]],
            ["优化器 (optimizer)", hp["optimizer"]],
            ["损失函数 (loss)", hp["loss"] + "（均方误差）"],
            ["噪声类型 / 强度", f"高斯噪声 / {hp['noise_factor']}"],
            ["激活函数", "ReLU（隐藏层）、Sigmoid（输出层）"],
            ["运行设备", hp["device"]],
        ],
    )

    heading2(doc, "5.4  训练过程")
    body(doc,
         "每个批次取干净图像并在线生成加噪图像，前向得到去噪输出，计算其与干净图像之间的 MSE，"
         "再反向传播更新参数。训练损失随迭代轮数的变化如图1所示：损失从约 "
         f"{m['epoch_losses'][0]:.4f} 快速下降并逐渐收敛到约 {m['epoch_losses'][-1]:.4f}，"
         "说明网络有效地学习到了去噪映射。")
    figure(doc, "training_loss.png", "图1  训练损失曲线", width_in=5.0)

    heading2(doc, "5.5  测试结果")
    body(doc,
         "在测试集（10000 张）上对网络进行测试。去噪效果对比如图2所示：第一行为干净目标图像，"
         "第二行为加入高斯噪声后的输入图像（噪声很强、数字几乎被淹没），第三行为网络去噪后的输出，"
         "可见网络成功去除了绝大部分噪声并较好地恢复了数字笔画。")
    figure(doc, "denoise_samples.png", "图2  去噪效果对比（干净 / 加噪 / 去噪）", width_in=6.0)
    body(doc,
         "对于图像去噪任务，“模型精度”用重建图像与干净图像的接近程度衡量，即 PSNR / SSIM / MSE，"
         "测试集量化结果如表3所示。")
    table_caption(doc, "表3  测试集去噪精度")
    three_line_table(
        doc,
        ["指标", "加噪输入（基线）", "去噪输出（本模型）"],
        [
            ["PSNR", f"{met['noisy_input_psnr']:.2f} dB", f"{met['test_psnr']:.2f} dB"],
            ["SSIM", "—", f"{met['test_ssim']:.4f}"],
            ["MSE", "—", f"{met['test_mse']:.6f}"],
        ],
    )
    para(doc, "测试控制台输出（用于截图存档）：", size=XIAO_SI)
    para(doc,
         "=== Test results ===\n"
         f"Noisy input PSNR (baseline): {met['noisy_input_psnr']:.2f} dB\n"
         f"Denoised MSE : {met['test_mse']:.6f}\n"
         f"Denoised PSNR: {met['test_psnr']:.2f} dB\n"
         f"Denoised SSIM: {met['test_ssim']:.4f}",
         size=WU_HAO, mono=True)

    heading2(doc, "5.6  结果分析")
    for t in [
        "（1）去噪效果显著：PSNR 由加噪输入的 {:.2f} dB 提升到去噪输出的 {:.2f} dB，提升约 {:.1f} dB；"
        "SSIM 达到 {:.2f}，表明去噪图像在结构上与原图高度相似。".format(
            met["noisy_input_psnr"], met["test_psnr"], improve, met["test_ssim"]),
        "（2）收敛行为合理：损失在前 2 个 epoch 急剧下降后平稳收敛，没有出现震荡或发散，"
        "说明学习率与优化器设置合适。",
        "（3）编码器—解码器结构的作用：编码器把图像压缩到 64×7×7 的特征表示，迫使网络保留"
        "“数字结构”这类主要信息而丢弃随机噪声；解码器再据此重建干净图像，因此能起到去噪作用。",
        "（4）可改进方向：增加训练轮数或加入跳跃连接（如 U-Net）可进一步提升 PSNR/SSIM；"
        "可尝试不同噪声类型（椒盐、泊松）做鲁棒性对比；使用 GPU 可显著缩短训练时间。",
    ]:
        body(doc, t)

    # 6 小结
    heading1(doc, "6  小结")
    body(doc,
         "本实验基于 PyTorch 搭建了卷积去噪自编码器，对叠加高斯噪声的 MNIST 手写数字图像进行去噪。"
         "实验结果表明，该卷积神经网络能够有效去除图像噪声：测试集 PSNR 从 {:.2f} dB 提升至 {:.2f} dB，"
         "SSIM 达 {:.2f}，去噪图像在视觉上清晰地恢复了原始数字。实验验证了卷积神经网络"
         "（编码器—解码器结构）在图像去噪任务中的有效性，也加深了对 PyTorch 框架与 CNN 训练流程的理解。"
         .format(met["noisy_input_psnr"], met["test_psnr"], met["test_ssim"]))

    out_path = os.path.join(HERE, "实验报告.docx")
    doc.save(out_path)
    print("Saved report docx ->", out_path.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
