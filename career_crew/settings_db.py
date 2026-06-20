import sqlite3
import os

DB_PATH = os.getenv("SETTINGS_DB_PATH", "/app/data/settings.db")


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS settings "
        "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    con.commit()
    return con


def get_all() -> dict:
    with _conn() as con:
        rows = con.execute("SELECT key, value FROM settings").fetchall()
    return {k: v for k, v in rows}


def upsert(data: dict) -> None:
    with _conn() as con:
        for k, v in data.items():
            if v is None or v == "":
                con.execute("DELETE FROM settings WHERE key = ?", (k,))
            else:
                con.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (k, str(v)),
                )
        con.commit()
