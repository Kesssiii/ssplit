from pathlib import Path

from .database import get_db


MIGRATIONS_DIRECTORY = Path(__file__).parent.parent / "migrations"


def run_migrations():
    database = get_db()
    database.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    applied_versions = {
        row[0]
        for row in database.execute("SELECT version FROM schema_migrations")
    }

    migration_files = sorted(MIGRATIONS_DIRECTORY.glob("*.sql"))
    for migration_file in migration_files:
        version = int(migration_file.stem.split("_", 1)[0])
        if version in applied_versions:
            continue

        database.executescript(migration_file.read_text(encoding="utf-8"))
        database.execute(
            "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
            (version, migration_file.name),
        )

    database.commit()
