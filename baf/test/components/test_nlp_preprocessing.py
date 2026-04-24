"""Tests for baf.nlp.preprocessing utilities."""

import pytest

from baf.core.agent import Agent
from baf.nlp.preprocessing.pipelines import lang_map, lang_map_tokenizers
from baf.nlp.preprocessing.text_preprocessing import (
    process_text,
    stem_text,
    tokenize,
)


def test_tokenize_basic_english():
    tokens = tokenize("Hello, World!", language="en")
    assert "hello" in tokens
    assert "world" in tokens
    # Punctuation should have been stripped
    assert "," not in tokens
    assert "!" not in tokens


def test_tokenize_lowercases_tokens():
    tokens = tokenize("The QUICK Fox", language="en")
    assert all(t == t.lower() for t in tokens)


def test_tokenize_accepts_iso_language_codes():
    # lang_map contains ISO → name mapping; tokenize should accept either form.
    assert "english" in lang_map.values() or "en" in lang_map
    tokens_iso = tokenize("hello world", language="en")
    tokens_name = tokenize("hello world", language="english")
    assert tokens_iso == tokens_name


def test_stem_text_english_reduces_words_to_root():
    result = stem_text("running runner runs", language="english")
    # Snowball English stemmer reduces these to 'run'
    assert "run" in result.split()


def test_stem_text_returns_string():
    # The exact stem may depend on the Snowball version, but the output
    # must be a non-empty space-separated string covering the input words.
    result = stem_text("hello worlds", language="english")
    assert isinstance(result, str)
    assert result.strip()
    assert len(result.split()) == 2


def test_process_text_returns_string():
    agent = Agent("a")
    out = process_text("Hello world", agent.nlp_engine)
    assert isinstance(out, str)
    assert out  # not empty


def test_process_text_when_preprocessing_disabled():
    from baf import nlp
    agent = Agent("a")
    agent.set_property(nlp.NLP_PRE_PROCESSING, False)
    assert process_text("Hello World", agent.nlp_engine) == "Hello World"


def test_lang_map_is_populated():
    assert isinstance(lang_map, dict)
    assert len(lang_map) > 0
    assert isinstance(lang_map_tokenizers, dict) or isinstance(lang_map_tokenizers, set) or hasattr(lang_map_tokenizers, "__iter__")
