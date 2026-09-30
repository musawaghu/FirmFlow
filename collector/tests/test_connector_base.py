import pytest

from collector.connectors.base import ChannelNotAllowed, Connector, ConnectorError, FetchResult
from collector.schema import Source
from tests.helpers import ScriptedConnector, make_message


def test_allowlist_must_not_be_empty():
    with pytest.raises(ValueError):
        ScriptedConnector({})
    with pytest.raises(ValueError):

        class Dummy(Connector):
            source = Source.FAKE

            def _fetch_new(self, channel, cursor, *, since, limit):
                return FetchResult()

        Dummy("x", ["", "  "])


def test_reading_a_channel_outside_the_allowlist_is_refused_before_the_adapter_runs():
    c = ScriptedConnector({"C1": [FetchResult([make_message(1)], "a")]})
    with pytest.raises(ChannelNotAllowed):
        c.fetch_new("C2", None)
    assert c.calls == []  # the adapter was never called


def test_allowlisted_channel_returns_messages():
    c = ScriptedConnector({"C1": [FetchResult([make_message(1)], "a")]})
    result = c.fetch_new("C1", None)
    assert [m.message_id for m in result.messages] == ["m1"]
    assert result.cursor == "a"


def test_adapter_returning_another_channels_messages_is_rejected():
    leaked = make_message(1, channel="C-private")
    c = ScriptedConnector({"C1": [FetchResult([leaked], "a")]})
    with pytest.raises(ConnectorError):
        c.fetch_new("C1", None)


def test_adapter_returning_another_sources_messages_is_rejected():
    c = ScriptedConnector({"C1": [FetchResult([make_message(1, source_id="other")], "a")]})
    with pytest.raises(ConnectorError):
        c.fetch_new("C1", None)


def test_duplicate_channels_are_collapsed():
    c = ScriptedConnector({"C1": []})
    assert c.channels == ("C1",)
