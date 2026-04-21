import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class NoisyLinear(nn.Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self._in_features = in_features
        self._out_features = out_features

        # Learnable Parameters
        self._weight_mu = nn.Parameter(torch.empty(out_features, in_features))
        self._weight_sigma = nn.Parameter(torch.empty(out_features, in_features))
        self._bias_mu = nn.Parameter(torch.empty(out_features))
        self._bias_sigma = nn.Parameter(torch.empty(out_features))

        # Buffers
        self.register_buffer('_weight_epsilon',torch.zeros(out_features, in_features))
        self.register_buffer('_bias_epsilon',torch.zeros(out_features))

        self.reset_parameters()
        self.reset_noise()

    def reset_parameters(self):
        bound = 1 / math.sqrt(self._in_features)

        nn.init.uniform_(self._weight_mu, a = -bound, b = bound)
        nn.init.uniform_(self._bias_mu, a = -bound, b = bound)

        nn.init.constant_(self._weight_sigma, 0.5*bound)
        nn.init.constant_(self._bias_sigma, 0.5*bound)

    def reset_noise(self):
        epsilon_in  = torch.randn(self._in_features)
        epsilon_out = torch.randn(self._out_features)

        def factorised_transform(x):
            return torch.sign(x) * torch.sqrt(torch.abs(x))

        epsilon_in = factorised_transform(epsilon_in)
        epsilon_out = factorised_transform(epsilon_out)

        self._weight_epsilon.copy_(torch.outer(epsilon_out, epsilon_in))
        self._bias_epsilon.copy_(epsilon_out)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.training:
            weight = self._weight_mu + self._weight_sigma * self._weight_epsilon
            bias = self._bias_mu + self._bias_sigma * self._bias_epsilon
        else:
            weight = self._weight_mu
            bias = self._bias_mu

        return F.linear(x, weight, bias)