from __future__ import annotations

# Optional module. Requires torch and a TCN implementation.

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover
    torch = None
    nn = None


class TCNDetector(nn.Module if nn is not None else object):
    def __init__(self, input_size: int = 20, hidden_size: int = 128) -> None:
        if nn is None:
            raise RuntimeError("torch is not installed. Install requirements-optional.txt")
        super().__init__()
        self.conv1 = nn.Conv1d(input_size, 64, kernel_size=5, padding=4, dilation=1)
        self.conv2 = nn.Conv1d(64, hidden_size, kernel_size=5, padding=8, dilation=2)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch, features, timesteps)
        out = torch.relu(self.conv1(x))
        out = self.dropout(torch.relu(self.conv2(out)))
        out = out[:, :, -1]
        out = self.fc(out)
        return torch.sigmoid(out)
