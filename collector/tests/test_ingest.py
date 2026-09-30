import pytest

from collector.connectors.base import FetchResult
from collector.ingest import ingest_channel, ingest_source
from collector.sync_state import SyncState
from tests.helpers import ScriptedConnector, make_message


def three_pages():
    return [
        FetchResult([make_message(1), make_message(2)], "c1", has_more=True),
        FetchResult([make_message(3)], "c2", has_more=True),
        FetchResult([make_message(4)], "c3", has_more=False),
    ]


def test_reads_every_page_and_saves_the_final_cursor(tmp_path):
    seen = []
    with SyncState(tmp_path / "s.db") as state:
        conn = ScriptedConnector({"C1": three_pages()})
        stats = ingest_channel(conn, state, "C1", seen.extend)
        assert [m.message_id for m in seen] == ["m1", "m2", "m3", "m4"]
        assert (stats.pages, stats.messages, stats.error) == (3, 4, None)
        assert state.get("fake-1", "C1") == "c3"


def test_second_run_only_fetches_what_is_new(tmp_path):
    with SyncState(tmp_path / "s.db") as state:
        conn = ScriptedConnector({"C1": three_pages()})
        ingest_channel(conn, state, "C1", lambda msgs: None)
        seen = []
        stats = ingest_channel(conn, state, "C1", seen.extend)
        assert seen == [] and stats.messages == 0
        assert conn.calls[-1] == ("C1", "c3")  # resumed from the saved cursor, not from the start


def test_a_failing_handler_does_not_advance_the_cursor(tmp_path):
    def boom(msgs):
        raise RuntimeError("downstream failed")

    with SyncState(tmp_path / "s.db") as state:
        conn = ScriptedConnector({"C1": three_pages()})
        with pytest.raises(RuntimeError):
            ingest_channel(conn, state, "C1", boom)
        assert state.get("fake-1", "C1") is None  # the page will be delivered again next run


def test_progress_is_kept_when_a_later_page_fails(tmp_path):
    delivered = []

    def handler(msgs):
        if len(delivered) >= 2:
            raise RuntimeError("fail on the second page")
        delivered.extend(msgs)

    with SyncState(tmp_path / "s.db") as state:
        conn = ScriptedConnector({"C1": three_pages()})
        with pytest.raises(RuntimeError):
            ingest_channel(conn, state, "C1", handler)
        assert state.get("fake-1", "C1") == "c1"  # page 1 done, page 2 will be retried


def test_stuck_cursor_with_more_pages_raises_instead_of_looping(tmp_path):
    stuck = [FetchResult([make_message(1)], "same", has_more=True), FetchResult([make_message(2)], "same", has_more=True)]
    with SyncState(tmp_path / "s.db") as state:
        conn = ScriptedConnector({"C1": stuck})
        state.set("fake-1", "C1", "same")
        with pytest.raises(RuntimeError, match="did not advance"):
            ingest_channel(conn, state, "C1", lambda m: None)


def test_max_pages_bounds_a_single_run(tmp_path):
    with SyncState(tmp_path / "s.db") as state:
        conn = ScriptedConnector({"C1": three_pages()})
        stats = ingest_channel(conn, state, "C1", lambda m: None, max_pages=2)
        assert stats.pages == 2
        assert state.get("fake-1", "C1") == "c2"  # the third page is left for the next run


def test_one_broken_channel_does_not_block_the_others(tmp_path):
    with SyncState(tmp_path / "s.db") as state:
        conn = ScriptedConnector(
            {
                "C1": [FetchResult([make_message(1, channel="C-other")], "a")],  # adapter misbehaves
                "C2": [FetchResult([make_message(2, channel="C2")], "b")],
            }
        )
        seen = []
        results = ingest_source(conn, state, seen.extend)
        assert results["C1"].error == "ConnectorError"
        assert results["C2"].error is None and results["C2"].messages == 1
        assert [m.channel for m in seen] == ["C2"]
        assert state.get("fake-1", "C1") is None
