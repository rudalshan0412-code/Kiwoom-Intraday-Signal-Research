from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch
from torch import nn


HEAD_NAMES = ("A", "B", "C", "D")


class SharedBackboneMultiHead(nn.Module):
    """
    Shared backbone + 4 binary heads.

    Input:
        x: [batch, n_features]

    Output:
        dict[str, Tensor] where each Tensor is logits [batch]
    """

    def __init__(
        self,
        n_features: int,
        hidden1: int = 64,
        hidden2: int = 32,
        dropout: float = 0.10,
    ) -> None:
        super().__init__()

        self.backbone = nn.Sequential(
            nn.Linear(n_features, hidden1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
        )

        self.heads = nn.ModuleDict({
            head: nn.Linear(hidden2, 1)
            for head in HEAD_NAMES
        })

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        h = self.backbone(x)

        return {
            head: layer(h).squeeze(-1)
            for head, layer in self.heads.items()
        }


@dataclass
class NormalizationStats:
    mean: list[float]
    std: list[float]
