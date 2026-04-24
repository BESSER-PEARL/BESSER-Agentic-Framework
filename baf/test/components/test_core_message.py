"""Tests for baf.core.message.Message / MessageType and baf.core.file.File."""

from datetime import datetime

import pytest

from baf.core.file import File
from baf.core.message import Message, MessageType, get_message_type
from baf.platforms.payload import PayloadAction


def test_message_construction_attributes():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    msg = Message(t=MessageType.STR, content="hello", is_user=True, timestamp=ts)
    assert msg.type is MessageType.STR
    assert msg.content == "hello"
    assert msg.is_user is True
    assert msg.timestamp == ts


def test_message_type_enum_values():
    assert MessageType.STR.value == "str"
    assert MessageType.JSON.value == "json"
    assert MessageType.RAG_ANSWER.value == "rag_answer"
    assert MessageType.IMAGE.value == "image"


def test_get_message_type_lookup():
    assert get_message_type("str") is MessageType.STR
    assert get_message_type("markdown") is MessageType.MARKDOWN
    assert get_message_type("does-not-exist") is None


def test_message_get_action_maps_user_vs_agent():
    user_msg = Message(MessageType.STR, "hi", is_user=True, timestamp=datetime.now())
    agent_msg = Message(MessageType.STR, "hi", is_user=False, timestamp=datetime.now())
    assert user_msg.get_action() is PayloadAction.USER_MESSAGE
    assert agent_msg.get_action() is PayloadAction.AGENT_REPLY_STR


def test_message_get_action_file_user_vs_audio_agent():
    user_file = Message(MessageType.FILE, b"data", is_user=True, timestamp=datetime.now())
    agent_audio = Message(MessageType.AUDIO, b"data", is_user=False, timestamp=datetime.now())
    assert user_file.get_action() is PayloadAction.USER_FILE
    assert agent_audio.get_action() is PayloadAction.AGENT_REPLY_AUDIO


def test_file_from_bytes_and_roundtrip():
    raw = b"\x00\x01\x02 hello"
    f = File(file_name="hello.bin", file_type="bin", file_data=raw)
    assert f.name == "hello.bin"
    assert f.type == "bin"
    assert f.base64  # non-empty base64 string

    data = f.to_dict()
    assert data == {"name": "hello.bin", "type": "bin", "base64": f.base64}

    restored = File.from_dict(data)
    assert restored.name == "hello.bin"
    assert restored.type == "bin"
    assert restored.base64 == f.base64


def test_file_get_json_string_and_decode():
    raw = b"payload"
    f = File(file_name="p.txt", file_type="txt", file_data=raw)
    restored = File.decode(f.get_json_string())
    assert restored is not None
    assert restored.name == "p.txt"
    assert restored.type == "txt"
    assert restored.base64 == f.base64


def test_file_requires_some_source():
    with pytest.raises(ValueError):
        File(file_name="empty.txt", file_type="txt")


def test_file_defaults_name_and_type_when_missing():
    f = File(file_data=b"x")
    assert f.name == "default_filename"
    assert f.type == "file"
