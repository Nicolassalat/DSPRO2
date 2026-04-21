import torch.nn as nn
from abc import ABC, abstractmethod

class BaseEncoder(nn.Module, ABC):
    """
    Abstract base class for Impala CNN block
    """
    def __init__(self, input_channels, input_shape, features_dim):
        super().__init__()

        self._input_channels = input_channels
        self._input_shape = input_shape
        self._features_dim = features_dim
        self._build_encoder()
        self._init_weights()

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