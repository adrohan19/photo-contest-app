import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from flask import g

import config


def _get_connection() -> sqlite3.Connection:
    conn = getattr(g, "_database", None)
    if conn is None:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        g._database = conn
    return conn


def close_connection(_: Optional[BaseException] = None) -> None:
    conn = getattr(g, "_database", None)
    if conn is not None:
        conn.close()
        g._database = None


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    with transaction() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uploader_name TEXT NOT NULL,
                email TEXT,
                caption TEXT,
                categories TEXT NOT NULL,
                filename TEXT NOT NULL,
                contest TEXT NOT NULL DEFAULT 'costumes',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                voter_token TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(photo_id) REFERENCES photos(id),
                UNIQUE(voter_token, category)
            )
            """
        )

        # Backfill contest column for databases created before this deployment.
        columns = {
            column_info["name"]
            for column_info in conn.execute("PRAGMA table_info(photos)").fetchall()
        }
        if "contest" not in columns:
            conn.execute("ALTER TABLE photos ADD COLUMN contest TEXT NOT NULL DEFAULT 'costumes'")


def add_photo(
    uploader_name: str,
    email: Optional[str],
    caption: Optional[str],
    categories: List[str],
    filename: str,
    contest: str,
) -> int:
    created_at = datetime.utcnow().isoformat()
    with transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO photos (uploader_name, email, caption, categories, filename, contest, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (uploader_name, email, caption, json.dumps(categories), filename, contest, created_at),
        )
        return cur.lastrowid


def fetch_photos(contest: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = _get_connection()
    query = """
        SELECT
            p.id,
            p.uploader_name,
            p.email,
            p.caption,
            p.categories,
            p.filename,
            p.contest,
            p.created_at
        FROM photos p
    """
    params: List[Any] = []
    if contest:
        query += " WHERE p.contest = ?"
        params.append(contest)
    query += " ORDER BY p.created_at DESC"

    rows = conn.execute(query, params).fetchall()

    photos = []
    for row in rows:
        photo_categories = json.loads(row["categories"])
        photos.append(
            {
                "id": row["id"],
                "uploader_name": row["uploader_name"],
                "email": row["email"],
                "caption": row["caption"],
                "categories": photo_categories,
                "filename": row["filename"],
                "contest": row["contest"],
                "created_at": row["created_at"],
            }
        )
    return photos


def fetch_photo(photo_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_connection()
    row = conn.execute(
        """
        SELECT id, uploader_name, email, caption, categories, filename, contest, created_at
        FROM photos
        WHERE id = ?
        """,
        (photo_id,),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "uploader_name": row["uploader_name"],
        "email": row["email"],
        "caption": row["caption"],
        "categories": json.loads(row["categories"]),
        "filename": row["filename"],
        "contest": row["contest"],
        "created_at": row["created_at"],
    }


def record_vote(photo_id: int, category: str, voter_token: str) -> None:
    now = datetime.utcnow().isoformat()
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO votes (photo_id, category, voter_token, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(voter_token, category)
            DO UPDATE SET photo_id=excluded.photo_id, created_at=excluded.created_at
            """,
            (photo_id, category, voter_token, now),
        )


def aggregate_votes() -> Dict[str, List[Dict[str, Any]]]:
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT
            v.category,
            v.photo_id,
            COUNT(*) AS vote_count
        FROM votes v
        GROUP BY v.category, v.photo_id
        ORDER BY vote_count DESC
        """
    ).fetchall()

    results: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        category = row["category"]
        results.setdefault(category, []).append(
            {"photo_id": row["photo_id"], "votes": row["vote_count"]}
        )
    return results
