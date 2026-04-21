import torch
import torch.nn as nn
import torch.nn.functional as F
from abc import ABC, abstractmethod

class BaseEncoder(nn.Module, ABC):
    """
    Abstract base class for Impala CNN block
    """
    def __init__(self, _input_channels, input_shape, features_dim):
        super().__init__()

        self._input_channels = _input_channels
        self._input_shape = input_shape
        self._features_dim = features_dim

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        forward pass for encoder
        :param x: image tensor
        """

    @abstractmethod
    def _build_encoder(self):
        """
        The methods purpose is to build the encoder
        so that subclasses can implement their own architecture
        """

    def _init_weights(self):

        for module in self.modules():
            if isinstance(module, nn.Conv2d):
                nn.init.kaiming_normal_(module.weight, nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)



class ResidualBlock(nn.Module):
    """
    The non-linear and spectral normalization performing element-wise operations for Impala CNN block
    """
    def __init__(self, _channels):
        super().__init__()
        self._channels = _channels
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
    def __init__(self, _input_channels, input_shape, features_dim, _output_channel):
        super().__init__(_input_channels, input_shape, features_dim)

        self._output_channel = _output_channel
        self._build_encoder()
        self._init_weights()


    def _build_encoder(self):
        self._encoder = nn.Sequential(
            ConvSequence(self._input_channels, self._output_channel),
            ConvSequence(self._output_channel, self._output_channel),
            ConvSequence(self._output_channel, self._output_channel),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self._encoder(x)