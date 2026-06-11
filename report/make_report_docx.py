"""Generate the experiment report as a Word (.docx) document.

Reads metrics from report/figures/metrics.json and embeds the figures, producing
report/实验报告.docx. Run after src/main.py has produced the figures:

    python report/make_report_docx.py
"""
from __future__ import annotations

import json
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")


def load_metrics() -> dict:
    with open(os.path.join(FIG_DIR, "metrics.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def add_heading(doc: Document, text: str, level: int) -> None:
    doc.add_heading(text, level=level)


def add_kv_table(doc: Document, rows: list[tuple[str, str]]) -> None:
    table = doc.add_table(rows=0, cols=2)
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, v in rows:
        cells = table.add_row().cells
        cells[0].text = k
        cells[1].text = v


def add_image(doc: Document, filename: str, width_in: float = 6.0) -> None:
    path = os.path.join(FIG_DIR, filename)
    doc.add_picture(path, width=Inches(width_in))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def main() -> None:
    m = load_metrics()
    hp = m["hyperparameters"]
    met = m["metrics"]

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Microsoft YaHei"
    style.font.size = Pt(11)

    title = doc.add_heading("实验三 基于卷积神经网络的 MNIST 手写数字图片噪声处理", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_kv_table(
        doc,
        [
            ("实验名称", "基于卷积神经网络的 MNIST 手写数字图片噪声处理"),
            ("专业班级", "（请填写）"),
            ("学号", "（请填写）"),
            ("姓名", "（请填写）"),
            ("实验日期", "（请填写）"),
        ],
    )

    add_heading(doc, "一、实验目的", 1)
    for t in [
        "熟悉 PyTorch 深度学习框架的使用；",
        "熟悉卷积神经网络的训练思路；",
        "掌握卷积神经网络对图像噪声去除的过程。",
    ]:
        doc.add_paragraph(t, style="List Number")

    add_heading(doc, "二、实验内容", 1)
    doc.add_paragraph(
        "现实中的数字图像在数字化和传输过程中常受到成像设备或外部环境噪声干扰，减少图像中噪声"
        "的过程称为图像去噪。本实验以 MNIST 手写数字数据库为训练数据，搭建一个卷积去噪自编码器"
        "（Convolutional Denoising Autoencoder）模型实现图像去噪：在干净图像上叠加高斯噪声得到"
        "“加噪图像”作为网络输入，原始“干净图像”作为目标输出，让网络学习从加噪图像到干净图像"
        "的映射，从而去除噪声。"
    )

    add_heading(doc, "三、构建网络", 1)
    doc.add_paragraph(
        "模型为对称的编码器—解码器结构。编码器用卷积 + 最大池化逐步下采样、提取特征并压缩到低维"
        "表示；解码器用转置卷积逐步上采样、重建去噪后的图像；最后用 Sigmoid 把输出限制到 [0, 1]。"
    )
    doc.add_paragraph("网络结构示意图：")
    p = doc.add_paragraph()
    run = p.add_run(
        "输入 噪声图像 (1×28×28)\n"
        "  └─ 编码器 Encoder\n"
        "       Conv2d(1→32, 3×3, pad=1) + ReLU + MaxPool2d(2×2)  → 32×14×14\n"
        "       Conv2d(32→64, 3×3, pad=1) + ReLU + MaxPool2d(2×2) → 64×7×7  (瓶颈)\n"
        "  └─ 解码器 Decoder\n"
        "       ConvTranspose2d(64→32, 2×2, s=2) + ReLU            → 32×14×14\n"
        "       ConvTranspose2d(32→16, 2×2, s=2) + ReLU            → 16×28×28\n"
        "       Conv2d(16→1, 3×3, pad=1) + Sigmoid                 → 1×28×28\n"
        "输出 去噪图像 (1×28×28)"
    )
    run.font.name = "Consolas"
    run.font.size = Pt(9)

    doc.add_paragraph("网络各层输出尺寸：")
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "层", "类型", "输出尺寸"
    layer_rows = [
        ("输入", "—", "1 × 28 × 28"),
        ("Conv1 + ReLU + MaxPool", "卷积 + 池化", "32 × 14 × 14"),
        ("Conv2 + ReLU + MaxPool", "卷积 + 池化", "64 × 7 × 7"),
        ("DeConv1 + ReLU", "转置卷积", "32 × 14 × 14"),
        ("DeConv2 + ReLU", "转置卷积", "16 × 28 × 28"),
        ("Conv3 + Sigmoid", "卷积", "1 × 28 × 28"),
    ]
    for r in layer_rows:
        cells = table.add_row().cells
        for i, val in enumerate(r):
            cells[i].text = val
    doc.add_paragraph(f"模型可训练参数量：{m['num_parameters']:,}")

    add_heading(doc, "四、神经网络参数设置", 1)
    add_kv_table(
        doc,
        [
            ("迭代次数 (epochs)", str(hp["epochs"])),
            ("批大小 (batch size)", str(hp["batch_size"])),
            ("学习率 (learning rate)", str(hp["learning_rate"])),
            ("优化器 (optimizer)", hp["optimizer"]),
            ("损失函数 (loss)", hp["loss"] + "（均方误差）"),
            ("噪声类型 / 强度", f"高斯噪声 / noise_factor = {hp['noise_factor']}"),
            ("激活函数", "ReLU（隐藏层）、Sigmoid（输出层）"),
            ("设备", hp["device"]),
        ],
    )
    doc.add_paragraph(
        "启动命令： python src/main.py --epochs {epochs} --batch-size {bs} "
        "--lr {lr} --noise-factor {nf}".format(
            epochs=hp["epochs"], bs=hp["batch_size"], lr=hp["learning_rate"], nf=hp["noise_factor"]
        )
    )

    add_heading(doc, "五、实验结果与分析", 1)
    add_heading(doc, "5.1 训练损失曲线", 2)
    doc.add_paragraph(
        "随着迭代轮数增加，训练 MSE 损失从约 {:.4f} 快速下降并逐渐收敛到约 {:.4f}，"
        "说明网络有效地学习到了去噪映射。".format(m["epoch_losses"][0], m["epoch_losses"][-1])
    )
    add_image(doc, "training_loss.png", width_in=5.2)

    add_heading(doc, "5.2 去噪效果对比（干净 / 加噪 / 去噪）", 2)
    doc.add_paragraph(
        "第一行为干净目标图像，第二行为加入高斯噪声后的输入图像（噪声很强、数字几乎被淹没），"
        "第三行为网络去噪后的输出。可见网络成功去除了绝大部分噪声并较好地恢复了数字笔画。"
    )
    add_image(doc, "denoise_samples.png", width_in=6.2)

    add_heading(doc, "5.3 测试精度（量化指标）", 2)
    doc.add_paragraph(
        "对于图像去噪任务，“模型精度”用重建图像与干净图像的接近程度衡量，即 PSNR / SSIM / MSE。"
        "下表为测试集（10000 张）上的结果："
    )
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "指标", "加噪输入（基线）", "去噪输出（本模型）"
    result_rows = [
        ("PSNR", f"{met['noisy_input_psnr']:.2f} dB", f"{met['test_psnr']:.2f} dB"),
        ("SSIM", "—", f"{met['test_ssim']:.4f}"),
        ("MSE", "—", f"{met['test_mse']:.6f}"),
    ]
    for r in result_rows:
        cells = table.add_row().cells
        for i, val in enumerate(r):
            cells[i].text = val

    doc.add_paragraph("测试控制台输出（用于截图存档）：")
    p = doc.add_paragraph()
    run = p.add_run(
        "=== Test results ===\n"
        f"Noisy input PSNR (baseline): {met['noisy_input_psnr']:.2f} dB\n"
        f"Denoised MSE : {met['test_mse']:.6f}\n"
        f"Denoised PSNR: {met['test_psnr']:.2f} dB\n"
        f"Denoised SSIM: {met['test_ssim']:.4f}"
    )
    run.font.name = "Consolas"
    run.font.size = Pt(9)

    add_heading(doc, "5.4 结果分析", 2)
    improve = met["test_psnr"] - met["noisy_input_psnr"]
    for t in [
        "去噪效果显著：PSNR 由加噪输入的 {:.2f} dB 提升到去噪输出的 {:.2f} dB，提升约 {:.1f} dB；"
        "SSIM 达到 {:.2f}，表明去噪图像在结构上与原图高度相似。".format(
            met["noisy_input_psnr"], met["test_psnr"], improve, met["test_ssim"]
        ),
        "收敛行为合理：损失在前 2 个 epoch 急剧下降后平稳收敛，没有出现震荡或发散，说明学习率与优化器设置合适。",
        "编码器—解码器结构的作用：编码器把图像压缩到 64×7×7 的特征表示，迫使网络保留“数字结构”这类主要信息"
        "而丢弃随机噪声；解码器再据此重建干净图像，因此能起到去噪作用。",
        "可改进方向：增加训练轮数或加入跳跃连接（如 U-Net）可进一步提升 PSNR/SSIM；可尝试不同噪声类型"
        "（椒盐、泊松）做鲁棒性对比；使用 GPU 可显著缩短训练时间。",
    ]:
        doc.add_paragraph(t, style="List Bullet")

    add_heading(doc, "六、结论", 1)
    doc.add_paragraph(
        "本实验基于 PyTorch 搭建了卷积去噪自编码器，对叠加高斯噪声的 MNIST 手写数字图像进行去噪。"
        "实验结果表明，该卷积神经网络能够有效去除图像噪声：测试集 PSNR 从 {:.2f} dB 提升至 {:.2f} dB，"
        "SSIM 达 {:.2f}，去噪图像在视觉上清晰地恢复了原始数字。实验验证了卷积神经网络（编码器—解码器结构）"
        "在图像去噪任务中的有效性，也加深了对 PyTorch 框架与 CNN 训练流程的理解。".format(
            met["noisy_input_psnr"], met["test_psnr"], met["test_ssim"]
        )
    )

    out_path = os.path.join(HERE, "实验报告.docx")
    doc.save(out_path)
    print("Saved report docx ->", out_path.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
