from pathlib import Path

from core.storage import EntryStore


def test_new_store_is_empty(tmp_path: Path) -> None:
    store = EntryStore(tmp_path / "test.db")
    assert store.list_all() == []


def test_add_returns_entry_with_id_and_text(tmp_path: Path) -> None:
    store = EntryStore(tmp_path / "test.db")
    entry = store.add("Bench press 80kg")
    assert entry.id == 1
    assert entry.text == "Bench press 80kg"


def test_list_all_returns_newest_first(tmp_path: Path) -> None:
    store = EntryStore(tmp_path / "test.db")
    store.add("first")
    store.add("second")
    assert [e.text for e in store.list_all()] == ["second", "first"]


def test_entries_survive_reopening(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    EntryStore(db_path).add("persisted")
    assert [e.text for e in EntryStore(db_path).list_all()] == ["persisted"]


def test_creates_missing_parent_directory(tmp_path: Path) -> None:
    store = EntryStore(tmp_path / "nested" / "dir" / "test.db")
    store.add("x")
    assert len(store.list_all()) == 1
