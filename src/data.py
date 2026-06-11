"""MNIST data loading and noise injection utilities.

The denoising task uses the *clean* MNIST image as the target output and a
*noisy* version of the same image as the network input.
"""
from __future__ import annotations

import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms


def get_mnist_loaders(data_dir: str, batch_size: int = 128, num_workers: int = 0):
    """Return (train_loader, test_loader) for MNIST with pixels scaled to [0, 1]."""
    transform = transforms.ToTensor()  # yields float tensors in [0, 1], shape (1, 28, 28)

    train_set = datasets.MNIST(root=data_dir, train=True, download=True, transform=transform)
    test_set = datasets.MNIST(root=data_dir, train=False, download=True, transform=transform)

    train_loader = DataLoader(
        train_set, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    test_loader = DataLoader(
        test_set, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )
    return train_loader, test_loader


def add_gaussian_noise(images: torch.Tensor, noise_factor: float = 0.5) -> torch.Tensor:
    """Add zero-mean Gaussian noise and clamp back to the valid [0, 1] range."""
    noisy = images + noise_factor * torch.randn_like(images)
    return torch.clamp(noisy, 0.0, 1.0)
