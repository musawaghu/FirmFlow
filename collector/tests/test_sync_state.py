from collector.sync_state import SyncState


def test_missing_cursor_is_none(tmp_path):
    with SyncState(tmp_path / "s.db") as s:
        assert s.get("slack-main", "C1") is None


def test_cursor_round_trip_and_update(tmp_path):
    with SyncState(tmp_path / "s.db") as s:
        s.set("slack-main", "C1", "100.1")
        assert s.get("slack-main", "C1") == "100.1"
        s.set("slack-main", "C1", "200.2")
        assert s.get("slack-main", "C1") == "200.2"


def test_cursors_are_kept_per_source_and_channel(tmp_path):
    with SyncState(tmp_path / "s.db") as s:
        s.set("slack-main", "C1", "a")
        s.set("slack-main", "C2", "b")
        s.set("other", "C1", "c")
        assert (s.get("slack-main", "C1"), s.get("slack-main", "C2"), s.get("other", "C1")) == ("a", "b", "c")


def test_cursors_survive_reopening_the_file(tmp_path):
    path = tmp_path / "s.db"
    with SyncState(path) as s:
        s.set("slack-main", "C1", "a")
    with SyncState(path) as s:
        assert s.get("slack-main", "C1") == "a"


def test_reset_one_channel_or_a_whole_source(tmp_path):
    with SyncState(tmp_path / "s.db") as s:
        s.set("slack-main", "C1", "a")
        s.set("slack-main", "C2", "b")
        s.set("other", "C1", "c")
        s.reset("slack-main", "C1")
        assert s.get("slack-main", "C1") is None and s.get("slack-main", "C2") == "b"
        s.reset("slack-main")
        assert s.get("slack-main", "C2") is None and s.get("other", "C1") == "c"
