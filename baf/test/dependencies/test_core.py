"""Smoke tests for every dependency in requirements-core.txt."""

import pytest


def test_aiohttp():
    import aiohttp
    assert aiohttp.ClientSession


def test_gidgethub():
    import gidgethub
    from gidgethub import sansio  # noqa: F401


def test_gidgetlab():
    import gidgetlab
    from gidgetlab import sansio  # noqa: F401


def test_dateparser():
    import dateparser
    parsed = dateparser.parse("2024-01-15")
    assert parsed is not None
    assert parsed.year == 2024


def test_langdetect():
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    assert detect("hello world, this is an english sentence") == "en"


def test_markdownify():
    from markdownify import markdownify
    assert markdownify("<b>hi</b>").strip() == "**hi**"


def test_nltk():
    import nltk
    assert hasattr(nltk, "tokenize")


def test_numpy():
    import numpy as np
    arr = np.array([1, 2, 3])
    assert arr.sum() == 6
    assert np.ascontiguousarray(arr).dtype == arr.dtype


def test_pandas():
    import pandas as pd
    df = pd.DataFrame({"a": [1, 2, 3]})
    assert df["a"].sum() == 6


def test_python_telegram_bot():
    import telegram
    assert telegram.__version__


def test_psycopg2():
    import psycopg2  # noqa: F401


def test_pydantic():
    from pydantic import BaseModel, ValidationError

    class M(BaseModel):
        x: int

    assert M(x=3).x == 3
    with pytest.raises(ValidationError):
        M(x="not-an-int")  # type: ignore[arg-type]


def test_pyvis():
    from pyvis.network import Network
    net = Network()
    net.add_node(1)
    assert len(net.nodes) == 1


def test_pyyaml():
    import yaml
    loaded = yaml.safe_load(yaml.safe_dump({"a": 1}))
    assert loaded == {"a": 1}


def test_requests():
    import requests
    assert requests.Session


def test_snowballstemmer():
    import snowballstemmer
    stemmer = snowballstemmer.stemmer("english")
    assert stemmer.stemWord("running") == "run"


def test_sqlalchemy():
    from sqlalchemy import create_engine, text
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


def test_streamlit():
    import streamlit as st
    assert hasattr(st, "session_state")


def test_streamlit_antd_components():
    import streamlit_antd_components  # noqa: F401


def test_text2num():
    from text_to_num import text2num, alpha2digit
    assert text2num("twenty-three", lang="en") == 23
    assert alpha2digit("twenty-three", lang="en") == "23"


def test_websocket_client():
    import websocket
    assert hasattr(websocket, "WebSocket")


def test_websockets():
    import websockets  # noqa: F401


def test_bcrypt():
    import bcrypt
    pw = b"secret"
    hashed = bcrypt.hashpw(pw, bcrypt.gensalt())
    assert bcrypt.checkpw(pw, hashed)
