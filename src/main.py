# Gym Tracker || Felix Harenberg

import os
from pathlib import Path

import flet as ft

from core.storage import EntryStore


def db_path() -> Path:
    # On the phone, Flet points this at a writable, persistent app directory.
    storage_dir = os.getenv("FLET_APP_STORAGE_DATA")
    if storage_dir:
        return Path(storage_dir) / "workout-tracker.db"
    return Path(__file__).resolve().parent.parent / "data" / "workout-tracker.db"


def main(page: ft.Page) -> None:
    page.title = "Workout Tracker"
    store = EntryStore(db_path())

    text_field = ft.TextField(label="Entry", expand=True)
    entries = ft.ListView(expand=True, spacing=4)

    def refresh() -> None:
        entries.controls = [ft.Text(f"{e.created_at}  {e.text}") for e in store.list_all()]
        page.update()

    def save(_: ft.Event) -> None:
        text = (text_field.value or "").strip()
        if not text:
            return
        store.add(text)
        text_field.value = ""
        refresh()

    page.add(
        ft.Row([text_field, ft.Button(content="Save", on_click=save)]),
        ft.Text(f"DB: {store.db_path}", size=10),
        entries,
    )
    refresh()


if __name__ == "__main__":
    ft.run(main)
