import torch
import torch.nn as nn
import layers.noisy_linear as NoisyLinear

class ValueStream(nn.Module):
    def __init__(self, cnn_output_dim):
        super().__init__()
        self._stream = nn.Sequential(
            NoisyLinear(cnn_output_dim, 512),
            nn.ReLU(),
            NoisyLinear(512, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self._stream(x)


class AdvantageStream(nn.Module):
    def __init__(self, cnn_output_dim, num_actions):
        super().__init__()
        self._stream = nn.Sequential(
            NoisyLinear(cnn_output_dim, 512),
            nn.ReLU(),
            NoisyLinear(512, num_actions)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self._stream(x)