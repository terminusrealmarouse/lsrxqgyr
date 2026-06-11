"""Quantitative image-quality metrics for the denoising task.

For an image restoration problem the natural measure of "accuracy" is how close
the restored image is to the clean target.  We report:

* MSE  - mean squared error (also the training loss)
* PSNR - peak signal-to-noise ratio in dB (higher is better)
* SSIM - structural similarity index in [0, 1] (higher is better)
"""
from __future__ import annotations

import numpy as np
import torch
from skimage.metrics import structural_similarity as ssim


@torch.no_grad()
def batch_mse(output: torch.Tensor, target: torch.Tensor) -> float:
    return torch.mean((output - target) ** 2).item()


@torch.no_grad()
def batch_psnr(output: torch.Tensor, target: torch.Tensor) -> float:
    """Average PSNR (dB) over a batch, assuming pixel values in [0, 1]."""
    mse = torch.mean((output - target) ** 2, dim=[1, 2, 3])
    mse = torch.clamp(mse, min=1e-10)
    psnr = 10.0 * torch.log10(1.0 / mse)
    return psnr.mean().item()


@torch.no_grad()
def batch_ssim(output: torch.Tensor, target: torch.Tensor) -> float:
    """Average SSIM over a batch using scikit-image (data_range=1.0)."""
    out = output.detach().cpu().numpy()
    tgt = target.detach().cpu().numpy()
    scores = []
    for i in range(out.shape[0]):
        scores.append(
            ssim(tgt[i, 0], out[i, 0], data_range=1.0)
        )
    return float(np.mean(scores))
