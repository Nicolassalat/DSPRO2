import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class IQN(nn.Module):
    def __init__(self, n_taus, embedding_dim, cnn_output_dim):
        super().__init__()
        self.n_taus = n_taus
        self.embedding_dim = embedding_dim
        self.cnn_output_dim = cnn_output_dim

        self._cos_embedding = nn.Linear(self.embedding_dim, self.cnn_output_dim)

        self.register_buffer(
            '_arange',
            torch.arange(1, embedding_dim + 1).float()
        )

    def _cosine_embedding(self, taus):
        x = torch.cos(taus.unsqueeze(-1) * math.pi * self._arange)
        x = F.relu(self._cos_embedding(x))
        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]

        taus = torch.rand(B, self.n_taus, device=x.device)

        tau_embedding = self._cosine_embedding(taus)

        x = x.unsqueeze(1) * tau_embedding

        return x, taus