"""Smoke tests for every dependency in requirements-torch.txt."""

import pytest


def test_torch_tensor_ops():
    torch = pytest.importorskip("torch")
    x = torch.tensor([1.0, 2.0, 3.0])
    y = torch.tensor([1.0, 1.0, 1.0])
    assert torch.equal(x + y, torch.tensor([2.0, 3.0, 4.0]))


def test_torch_nn_linear_forward():
    torch = pytest.importorskip("torch")
    import torch.nn as nn
    layer = nn.Linear(3, 2)
    out = layer(torch.zeros(1, 3))
    assert out.shape == (1, 2)


def test_sklearn_available():
    pytest.importorskip("sklearn")
    from sklearn.cluster import KMeans
    import numpy as np
    X = np.array([[0.0, 0.0], [0.0, 1.0], [10.0, 10.0], [10.0, 11.0]])
    km = KMeans(n_clusters=2, n_init=1, random_state=0).fit(X)
    assert len(set(km.labels_)) == 2
