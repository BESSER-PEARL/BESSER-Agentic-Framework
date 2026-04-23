"""Smoke tests for every dependency in requirements-tensorflow.txt."""

import pytest


def test_tensorflow():
    tf = pytest.importorskip("tensorflow")
    a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
    b = tf.constant([[1.0, 0.0], [0.0, 1.0]])
    product = tf.matmul(a, b)
    assert product.shape == (2, 2)
    assert tf.reduce_sum(product).numpy() == 10.0


def test_keras():
    keras = pytest.importorskip("keras")
    from keras import Sequential
    from keras.layers import Dense
    model = Sequential([Dense(4, input_shape=(3,)), Dense(1)])
    assert len(model.layers) == 2
    assert keras.__version__
