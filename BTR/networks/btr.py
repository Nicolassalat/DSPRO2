import torch
import torch.nn as nn
import layers.noisy_linear as NoisyLinear
import encoders.impala_encoder as IMPALAEncoder
from value_stream import *
from iqn import *


class BTRNetwork(nn.Module):
    def __init__(self, input_channels, input_shape, features_dim, channel_list, num_actions, n_taus=8,
                 embedding_dim=64):
        super().__init__()

        self._n_taus = n_taus
        self._num_actions = num_actions

        self._encoder = IMPALAEncoder(input_channels, input_shape, features_dim, channel_list)

        cnn_output_dim = 6 * 6 * channel_list[-1]

        self._iqn = IQN(n_taus, embedding_dim, cnn_output_dim)
        self._value_stream = ValueStream(cnn_output_dim)
        self._advantage_stream = AdvantageStream(cnn_output_dim, num_actions)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]

        # normalise
        x = x.float() / 255.0

        # encode
        x = self._encoder(x)

        # flatten after adaptive maxpool
        x = x.view(B, -1)

        # IQN — returns (B, n_taus, cnn_output_dim) and taus
        x, taus = self._iqn(x)

        # value and advantage streams
        value = self._value_stream(x)  # (B, n_taus, 1)
        advantage = self._advantage_stream(x)  # (B, n_taus, num_actions)

        # dueling combination
        q_values = value + (advantage - advantage.mean(dim=-1, keepdim=True))

        return q_values, taus

    def reset_noise(self):
        for module in self.modules():
            if isinstance(module, NoisyLinear):
                module.reset_noise()