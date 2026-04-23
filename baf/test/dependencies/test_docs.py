"""Smoke tests for every dependency in requirements-docs.txt."""

import pytest


def test_sphinx():
    sphinx = pytest.importorskip("sphinx")
    assert sphinx.__version__


def test_sphinx_copybutton():
    pytest.importorskip("sphinx_copybutton")


def test_sphinx_paramlinks():
    pytest.importorskip("sphinx_paramlinks")


def test_furo():
    furo = pytest.importorskip("furo")
    assert furo


def test_m2r2():
    m2r2 = pytest.importorskip("m2r2")
    assert m2r2
