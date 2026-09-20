import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        database_path = Path(current_app.instance_path) / "ssplit.sqlite3"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def init_db():
    from .migrations import run_migrations

    run_migrations()


def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()
