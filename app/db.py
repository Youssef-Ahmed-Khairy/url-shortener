import os
import sqlite3
from contextlib import contextmanager


@contextmanager
def get_conn():
    conn = sqlite3.connect(os.environ.get("DB_PATH", "links.db"))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS links (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   code TEXT UNIQUE NOT NULL,
                   url TEXT NOT NULL,
                   clicks INTEGER NOT NULL DEFAULT 0,
                   created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
               )""")


def create_link(code, url):
    with get_conn() as conn:
        conn.execute("INSERT INTO links (code, url) VALUES (?, ?)", (code, url))


def get_link(code):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
    return dict(row) if row else None


def list_links():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT code, url, clicks, created_at FROM links ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def add_click(code):
    with get_conn() as conn:
        conn.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))


def delete_link(code):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM links WHERE code = ?", (code,))
        return cur.rowcount > 0
