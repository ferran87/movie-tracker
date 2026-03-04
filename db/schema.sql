-- Movie & TV Show Tracker — SQLite Schema

CREATE TABLE IF NOT EXISTS media (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id       INTEGER NOT NULL UNIQUE,
    media_type    TEXT NOT NULL CHECK(media_type IN ('movie', 'tv')),
    title         TEXT NOT NULL,
    overview      TEXT,
    genres        TEXT,           -- JSON array: ["Drama","Comedy"]
    cast_top5     TEXT,           -- JSON array: ["Actor A","Actor B"]
    poster_path   TEXT,           -- TMDB path: "/abc123.jpg"
    release_year  INTEGER,
    imdb_rating   REAL,           -- TMDB vote_average
    imdb_id       TEXT,           -- e.g. "tt1234567"
    language      TEXT,
    runtime_mins  INTEGER,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS watch_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id    INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    watch_date  TEXT NOT NULL,
    platform    TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ratings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_log_id INTEGER NOT NULL REFERENCES watch_log(id) ON DELETE CASCADE,
    person       TEXT NOT NULL CHECK(person IN ('user', 'wife')),
    score        REAL NOT NULL CHECK(score >= 0 AND score <= 10),
    reaction     TEXT,           -- "loved", "liked", "meh", "disliked"
    created_at   TEXT DEFAULT (datetime('now')),
    UNIQUE(watch_log_id, person)
);

CREATE INDEX IF NOT EXISTS idx_watch_log_media ON watch_log(media_id);
CREATE INDEX IF NOT EXISTS idx_watch_log_date  ON watch_log(watch_date);
CREATE INDEX IF NOT EXISTS idx_ratings_log     ON ratings(watch_log_id);
CREATE INDEX IF NOT EXISTS idx_media_type      ON media(media_type);

CREATE TABLE IF NOT EXISTS taste_ratings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id   INTEGER NOT NULL,
    title     TEXT NOT NULL,
    person    TEXT NOT NULL CHECK(person IN ('user', 'wife')),
    score     REAL NOT NULL CHECK(score >= 0 AND score <= 10),
    rated_at  TEXT DEFAULT (datetime('now')),
    UNIQUE(tmdb_id, person)
);
