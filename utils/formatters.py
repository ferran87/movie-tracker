import json
from datetime import datetime


def format_score(score) -> str:
    if score is None:
        return "—"
    return f"{score:.1f} / 10"


def format_date(iso_str: str) -> str:
    if not iso_str:
        return "—"
    try:
        return datetime.strptime(iso_str, "%Y-%m-%d").strftime("%b %d, %Y")
    except ValueError:
        return iso_str


def parse_genres(genres_json) -> list[str]:
    if not genres_json:
        return []
    if isinstance(genres_json, list):
        return genres_json
    try:
        return json.loads(genres_json)
    except (json.JSONDecodeError, TypeError):
        return []


def genre_badges(genres_json) -> str:
    genres = parse_genres(genres_json)
    return ", ".join(genres) if genres else "—"


def avg_couple_score(user_score, wife_score) -> str:
    scores = [s for s in [user_score, wife_score] if s is not None]
    if not scores:
        return "—"
    return f"{sum(scores) / len(scores):.1f} / 10"
