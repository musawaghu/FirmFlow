from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from collector.schema import Message, Source, hash_author
from tests.helpers import SALT, make_message


def test_hash_author_is_stable_and_salted():
    a = hash_author("U123", SALT)
    assert a == hash_author("U123", SALT)
    assert a != hash_author("U124", SALT)
    assert a != hash_author("U123", SALT + "x")
    assert len(a) == 16


def test_hash_author_does_not_contain_the_raw_id():
    assert "U123" not in hash_author("U123", SALT)


def test_hash_author_rejects_short_salt_and_empty_id():
    with pytest.raises(ValueError):
        hash_author("U123", "short")
    with pytest.raises(ValueError):
        hash_author("", SALT)


def test_message_rejects_raw_author_ids():
    base = make_message(1).model_dump()
    for bad in ("sarah@studiomeridian.example", "U0123ABC", "a" * 16 + "0", "G" * 16):
        with pytest.raises(ValidationError):
            Message(**{**base, "author_hash": bad})


def test_message_requires_timezone_and_normalizes_to_utc():
    base = make_message(1).model_dump()
    with pytest.raises(ValidationError):
        Message(**{**base, "timestamp": datetime(2026, 9, 1, 12, 0)})
    est = timezone(timedelta(hours=-5))
    m = Message(**{**base, "timestamp": datetime(2026, 9, 1, 7, 0, tzinfo=est)})
    assert m.timestamp == datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    assert m.timestamp.utcoffset() == timedelta(0)


def test_message_strips_text_and_rejects_empty():
    base = make_message(1).model_dump()
    assert Message(**{**base, "text": "  hello \n"}).text == "hello"
    with pytest.raises(ValidationError):
        Message(**{**base, "text": "   "})


def test_message_rejects_blank_ids_and_unknown_fields():
    base = make_message(1).model_dump()
    with pytest.raises(ValidationError):
        Message(**{**base, "channel": " "})
    with pytest.raises(ValidationError):
        Message(**{**base, "author_name": "Sarah"})


def test_message_is_immutable():
    m = make_message(1)
    with pytest.raises(ValidationError):
        m.text = "changed"


def test_source_values():
    assert {s.value for s in Source} == {"slack", "teams", "gchat", "gmail", "outlook", "fake"}
