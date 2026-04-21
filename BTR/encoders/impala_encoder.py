import torch
import torch.nn as nn
import torch.nn.functional as F
from base_encoder import BaseEncoder

class ResidualBlock(nn.Module):
    """
    The non-linear and spectral normalization performing element-wise operations for Impala CNN block
    """
    def __init__(self, channels):
        super().__init__()
        self._channels = channels
        self._conv1 = nn.utils.spectral_norm(nn.Conv2d(self._channels, self._channels, kernel_size=3, padding=1))
        self._conv2 = nn.utils.spectral_norm(nn.Conv2d(self._channels, self._channels, kernel_size=3, padding=1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip = x
        x = F.relu(x)
        x = self._conv1(x)
        x = F.relu(x)
        x = self._conv2(x)
        return x + skip



class ConvSequence(nn.Module):
    """
    Convolutional sequence and max-pooling of Impala CNN block
    """
    def __init__(self, input_channels, output_channels):
        super().__init__()
        self._conv = nn.Conv2d(input_channels, output_channels, kernel_size= 3, padding=1)
        self._pool = nn.MaxPool2d(3, stride=2, padding=1)
        self._res1 = ResidualBlock(output_channels)
        self._res2 = ResidualBlock(output_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self._pool(self._conv(x))
        x = self._res2(self._res1(x))
        return x



class IMPALAEncoder(BaseEncoder):
    """
    Impala CNN block, building the encoder method
    """
    def __init__(self, input_channels, input_shape, features_dim, channel_list):
        self._channel_list = channel_list
        super().__init__(input_channels, input_shape, features_dim)

    def _build_encoder(self):
        layers = []
        channels = [self._input_channels] + self._channel_list
        for in_ch, out_ch in zip(channels, channels[1:]):
            layers.append(ConvSequence(in_ch, out_ch))
        layers.append(nn.AdaptiveMaxPool2d((6, 6)))
        self._encoder = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self._encoder(x)