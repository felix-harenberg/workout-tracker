# Gym Tracker || Felix Harenberg

import os
from pathlib import Path

import flet as ft

from core.db import connect
from ui.app import App


def db_path() -> Path:
    # On the phone, Flet points this at a writable, persistent app directory.
    storage_dir = os.getenv("FLET_APP_STORAGE_DATA")
    if storage_dir:
        return Path(storage_dir) / "workout-tracker.db"
    return Path(__file__).resolve().parent.parent / "data" / "workout-tracker.db"


def main(page: ft.Page) -> None:
    page.title = "Workout Tracker"
    App(page, connect(db_path())).start()


if __name__ == "__main__":
    ft.run(main)
