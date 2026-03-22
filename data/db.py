import sqlite3
import os

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scores.db')


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT    NOT NULL CHECK(length(player_name) <= 10),
                score       INTEGER NOT NULL,
                level       INTEGER NOT NULL,
                lines       INTEGER NOT NULL,
                played_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')


def insert_score(name: str, score: int, level: int, lines: int) -> None:
    name = (name.strip() or 'PLAYER')[:10]
    with _get_conn() as conn:
        conn.execute(
            'INSERT INTO scores (player_name, score, level, lines) VALUES (?, ?, ?, ?)',
            (name, score, level, lines),
        )


def get_top_scores(limit: int = 10) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            'SELECT player_name, score, level, lines, played_at '
            'FROM scores ORDER BY score DESC LIMIT ?',
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def clear_scores() -> None:
    with _get_conn() as conn:
        conn.execute('DELETE FROM scores')
