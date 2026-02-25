from __future__ import annotations

# Optional module. Requires torch_geometric.

try:
    import torch
    import torch.nn.functional as F
    import torch_geometric as pyg
except Exception:  # pragma: no cover
    torch = None
    F = None
    pyg = None


class WashTradeGNN(torch.nn.Module if torch is not None else object):
    def __init__(self, in_channels: int = 16) -> None:
        if torch is None or pyg is None:
            raise RuntimeError("torch_geometric is not installed.")
        super().__init__()
        self.conv1 = pyg.nn.GCNConv(in_channels, 32)
        self.conv2 = pyg.nn.GCNConv(32, 64)
        self.fc = torch.nn.Linear(64, 1)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        x = self.fc(x)
        return torch.sigmoid(x)
