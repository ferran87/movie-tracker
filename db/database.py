import json
import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn:  # auto-commit on success, rollback on exception
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                yield cur
    finally:
        conn.close()


def init_db():
    with get_db() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id            SERIAL PRIMARY KEY,
                tmdb_id       INTEGER NOT NULL UNIQUE,
                media_type    TEXT NOT NULL CHECK(media_type IN ('movie', 'tv')),
                title         TEXT NOT NULL,
                overview      TEXT,
                genres        TEXT,
                cast_top5     TEXT,
                poster_path   TEXT,
                release_year  INTEGER,
                imdb_rating   REAL,
                imdb_id       TEXT,
                language      TEXT,
                runtime_mins  INTEGER,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS watch_log (
                id          SERIAL PRIMARY KEY,
                media_id    INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                watch_date  TEXT NOT NULL,
                platform    TEXT,
                notes       TEXT,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id           SERIAL PRIMARY KEY,
                watch_log_id INTEGER NOT NULL REFERENCES watch_log(id) ON DELETE CASCADE,
                person       TEXT NOT NULL CHECK(person IN ('user', 'wife')),
                score        REAL NOT NULL CHECK(score >= 0 AND score <= 10),
                reaction     TEXT,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(watch_log_id, person)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_watch_log_media ON watch_log(media_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_watch_log_date  ON watch_log(watch_date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ratings_log     ON ratings(watch_log_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_media_type      ON media(media_type)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS taste_ratings (
                id        SERIAL PRIMARY KEY,
                tmdb_id   INTEGER NOT NULL,
                title     TEXT NOT NULL,
                person    TEXT NOT NULL CHECK(person IN ('user', 'wife')),
                score     REAL NOT NULL CHECK(score >= 0 AND score <= 10),
                rated_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tmdb_id, person)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id          SERIAL PRIMARY KEY,
                tmdb_id     INTEGER NOT NULL UNIQUE,
                title       TEXT NOT NULL,
                media_type  TEXT NOT NULL,
                poster_path TEXT,
                overview    TEXT,
                added_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recommendation_skips (
                id         SERIAL PRIMARY KEY,
                tmdb_id    INTEGER NOT NULL UNIQUE,
                title      TEXT NOT NULL,
                skipped_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def insert_media(data: dict) -> int:
    sql = """
        INSERT INTO media (
            tmdb_id, media_type, title, overview, genres, cast_top5,
            poster_path, release_year, imdb_rating, imdb_id, language, runtime_mins
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(tmdb_id) DO UPDATE SET
            title        = excluded.title,
            overview     = excluded.overview,
            genres       = excluded.genres,
            cast_top5    = excluded.cast_top5,
            poster_path  = excluded.poster_path,
            release_year = excluded.release_year,
            imdb_rating  = excluded.imdb_rating,
            imdb_id      = excluded.imdb_id,
            language     = excluded.language,
            runtime_mins = excluded.runtime_mins
        RETURNING id
    """
    with get_db() as cur:
        cur.execute(sql, (
            data["tmdb_id"], data["media_type"], data["title"], data.get("overview"),
            json.dumps(data.get("genres", [])), json.dumps(data.get("cast_top5", [])),
            data.get("poster_path"), data.get("release_year"), data.get("imdb_rating"),
            data.get("imdb_id"), data.get("language"), data.get("runtime_mins"),
        ))
        return cur.fetchone()["id"]


def log_watch(media_id: int, watch_date: str, platform: str = None, notes: str = None) -> int:
    with get_db() as cur:
        cur.execute(
            "INSERT INTO watch_log (media_id, watch_date, platform, notes) VALUES (%s, %s, %s, %s) RETURNING id",
            (media_id, watch_date, platform, notes),
        )
        return cur.fetchone()["id"]


def save_rating(watch_log_id: int, person: str, score: float, reaction: str = None):
    with get_db() as cur:
        cur.execute(
            """INSERT INTO ratings (watch_log_id, person, score, reaction)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT(watch_log_id, person) DO UPDATE SET
                   score    = excluded.score,
                   reaction = excluded.reaction""",
            (watch_log_id, person, score, reaction),
        )


def get_watch_history(media_type: str = None, platform: str = None) -> list:
    sql = """
        SELECT
            wl.id AS log_id, wl.watch_date, wl.platform, wl.notes,
            m.id AS media_id, m.title, m.media_type, m.genres, m.poster_path,
            m.release_year, m.imdb_rating, m.imdb_id, m.overview, m.cast_top5,
            r_u.score AS user_score, r_u.reaction AS user_reaction,
            r_w.score AS wife_score, r_w.reaction AS wife_reaction
        FROM watch_log wl
        JOIN media m ON m.id = wl.media_id
        LEFT JOIN ratings r_u ON r_u.watch_log_id = wl.id AND r_u.person = 'user'
        LEFT JOIN ratings r_w ON r_w.watch_log_id = wl.id AND r_w.person = 'wife'
    """
    filters, params = [], []
    if media_type:
        filters.append("m.media_type = %s")
        params.append(media_type)
    if platform:
        filters.append("wl.platform = %s")
        params.append(platform)
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY wl.watch_date DESC"

    with get_db() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def get_rated_titles_for_llm() -> list[dict]:
    sql = """
        SELECT
            m.title, m.media_type, m.genres, m.release_year,
            r_u.score AS user_score, r_w.score AS wife_score
        FROM watch_log wl
        JOIN media m ON m.id = wl.media_id
        LEFT JOIN ratings r_u ON r_u.watch_log_id = wl.id AND r_u.person = 'user'
        LEFT JOIN ratings r_w ON r_w.watch_log_id = wl.id AND r_w.person = 'wife'
        ORDER BY wl.watch_date DESC
    """
    with get_db() as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]


def delete_watch_log(log_id: int):
    with get_db() as cur:
        cur.execute("DELETE FROM watch_log WHERE id = %s", (log_id,))


def get_platforms() -> list[str]:
    with get_db() as cur:
        cur.execute("SELECT DISTINCT platform FROM watch_log WHERE platform IS NOT NULL ORDER BY platform")
        return [r["platform"] for r in cur.fetchall()]


def save_taste_rating(tmdb_id: int, title: str, person: str, score: float):
    with get_db() as cur:
        cur.execute(
            """INSERT INTO taste_ratings (tmdb_id, title, person, score)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT(tmdb_id, person) DO UPDATE SET
                   score    = excluded.score,
                   rated_at = CURRENT_TIMESTAMP""",
            (tmdb_id, title, person, score),
        )


def get_watched_tmdb_ids() -> set:
    with get_db() as cur:
        cur.execute("SELECT DISTINCT tmdb_id FROM media JOIN watch_log ON watch_log.media_id = media.id")
        return {r["tmdb_id"] for r in cur.fetchall()}


def get_taste_rated_tmdb_ids() -> set:
    with get_db() as cur:
        cur.execute("SELECT DISTINCT tmdb_id FROM taste_ratings")
        return {r["tmdb_id"] for r in cur.fetchall()}


def add_to_watchlist(tmdb_id: int, title: str, media_type: str, poster_path: str = None, overview: str = None):
    with get_db() as cur:
        cur.execute(
            """INSERT INTO watchlist (tmdb_id, title, media_type, poster_path, overview)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT(tmdb_id) DO UPDATE SET added_at = CURRENT_TIMESTAMP""",
            (tmdb_id, title, media_type, poster_path, overview),
        )


def get_watchlist() -> list:
    with get_db() as cur:
        cur.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
        return cur.fetchall()


def get_watchlist_tmdb_ids() -> set:
    with get_db() as cur:
        cur.execute("SELECT tmdb_id FROM watchlist")
        return {r["tmdb_id"] for r in cur.fetchall()}


def remove_from_watchlist(tmdb_id: int):
    with get_db() as cur:
        cur.execute("DELETE FROM watchlist WHERE tmdb_id = %s", (tmdb_id,))


def add_recommendation_skip(tmdb_id: int, title: str):
    with get_db() as cur:
        cur.execute(
            """INSERT INTO recommendation_skips (tmdb_id, title)
               VALUES (%s, %s)
               ON CONFLICT(tmdb_id) DO UPDATE SET skipped_at = CURRENT_TIMESTAMP""",
            (tmdb_id, title),
        )


def get_skipped_rec_tmdb_ids() -> set:
    with get_db() as cur:
        cur.execute("SELECT tmdb_id FROM recommendation_skips")
        return {r["tmdb_id"] for r in cur.fetchall()}


def get_taste_ratings_for_llm() -> list[dict]:
    sql = """
        SELECT tmdb_id, title, person, score
        FROM taste_ratings
        ORDER BY rated_at DESC
    """
    with get_db() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    # Pivot per-title: merge user + wife scores into one dict
    by_title: dict[int, dict] = {}
    for r in rows:
        tid = r["tmdb_id"]
        if tid not in by_title:
            by_title[tid] = {"tmdb_id": tid, "title": r["title"], "user_score": None, "wife_score": None}
        if r["person"] == "user":
            by_title[tid]["user_score"] = r["score"]
        else:
            by_title[tid]["wife_score"] = r["score"]
    return list(by_title.values())
