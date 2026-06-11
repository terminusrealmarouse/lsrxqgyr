"""Convolutional denoising autoencoder for MNIST.

Architecture (input/output are single-channel 28x28 images in [0, 1]):

    Encoder
        Conv2d(1  -> 32, k3, s1, p1) + ReLU + MaxPool2d(2)   -> 32 x 14 x 14
        Conv2d(32 -> 64, k3, s1, p1) + ReLU + MaxPool2d(2)   -> 64 x  7 x  7
    Decoder
        ConvTranspose2d(64 -> 32, k2, s2)            + ReLU   -> 32 x 14 x 14
        ConvTranspose2d(32 -> 16, k2, s2)            + ReLU   -> 16 x 28 x 28
        Conv2d(16 -> 1, k3, s1, p1)                  + Sigmoid-> 1  x 28 x 28
"""
from __future__ import annotations

import torch
from torch import nn


class DenoisingCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 32 x 14 x 14
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 64 x 7 x 7
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2),  # 32 x 14 x 14
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 16, kernel_size=2, stride=2),  # 16 x 28 x 28
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 1, kernel_size=3, stride=1, padding=1),  # 1 x 28 x 28
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))
