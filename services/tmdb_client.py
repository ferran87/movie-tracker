import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

_BASE = "https://api.themoviedb.org/3"
_IMG_BASE = "https://image.tmdb.org/t/p/w500"


def _get(path: str, params: dict = None) -> dict:
    params = params or {}
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise ValueError("TMDB_API_KEY is not set")
    params["api_key"] = api_key
    response = requests.get(f"{_BASE}{path}", params=params, timeout=10)
    if not response.ok:
        raise RuntimeError(f"TMDB API error {response.status_code} for {path}")
    return response.json()


def search(query: str, media_type: str = "movie") -> list[dict]:
    data = _get(f"/search/{media_type}", {"query": query, "language": "en-US", "page": 1})
    results = []
    for r in data.get("results", [])[:10]:
        title = r.get("title") or r.get("name", "")
        year_raw = r.get("release_date") or r.get("first_air_date") or ""
        results.append({
            "tmdb_id": r["id"],
            "title": title,
            "release_year": int(year_raw[:4]) if year_raw else None,
            "poster_path": r.get("poster_path"),
            "overview": r.get("overview", ""),
            "imdb_rating": r.get("vote_average"),
        })
    return results


def get_details(tmdb_id: int, media_type: str = "movie") -> dict:
    return _get(
        f"/{media_type}/{tmdb_id}",
        {"append_to_response": "credits,external_ids", "language": "en-US"},
    )


def get_poster_url(poster_path: str) -> str | None:
    if not poster_path:
        return None
    return f"{_IMG_BASE}{poster_path}"


_GENRE_NAMES: dict[int, str] = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Sci-Fi", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10763: "News",
    10764: "Reality", 10765: "Sci-Fi & Fantasy", 10766: "Soap",
    10767: "Talk", 10768: "War & Politics",
}


def _normalize_listing(r: dict) -> dict:
    media_type = r.get("media_type", "movie")
    title = r.get("title") or r.get("name", "")
    year_raw = r.get("release_date") or r.get("first_air_date") or ""
    genre_names = [_GENRE_NAMES[gid] for gid in r.get("genre_ids", []) if gid in _GENRE_NAMES]
    return {
        "tmdb_id": r["id"],
        "media_type": media_type,
        "title": title,
        "release_year": int(year_raw[:4]) if year_raw else None,
        "poster_path": r.get("poster_path"),
        "overview": r.get("overview", ""),
        "imdb_rating": r.get("vote_average"),
        "genre_names": genre_names,
    }


def get_by_genre(genre_id: int, media_type: str = "movie", original_language: str = None, page: int = 1) -> list[dict]:
    params = {
        "with_genres": genre_id,
        "sort_by": "popularity.desc",
        "language": "en-US",
        "page": page,
    }
    if original_language:
        params["with_original_language"] = original_language
    data = _get(f"/discover/{media_type}", params)
    results = []
    for r in data.get("results", []):
        item = _normalize_listing(r)
        item["media_type"] = media_type
        results.append(item)
    return results


def get_trending(page: int = 1) -> list[dict]:
    data = _get("/trending/all/week", {"language": "en-US", "page": page})
    return [_normalize_listing(r) for r in data.get("results", []) if r.get("media_type") in ("movie", "tv")]


def get_popular(media_type: str = "movie", page: int = 1) -> list[dict]:
    data = _get(f"/{media_type}/popular", {"language": "en-US", "page": page})
    results = []
    for r in data.get("results", []):
        item = _normalize_listing(r)
        item["media_type"] = media_type
        results.append(item)
    return results


def normalize(raw: dict, media_type: str) -> dict:
    year_raw = raw.get("release_date") or raw.get("first_air_date") or ""
    genres = [g["name"] for g in raw.get("genres", [])]
    cast = [c["name"] for c in raw.get("credits", {}).get("cast", [])[:5]]
    imdb_id = raw.get("external_ids", {}).get("imdb_id")

    if media_type == "movie":
        runtime = raw.get("runtime")
    else:
        runtimes = raw.get("episode_run_time", [])
        runtime = runtimes[0] if runtimes else None

    return {
        "tmdb_id": raw["id"],
        "media_type": media_type,
        "title": raw.get("title") or raw.get("name", ""),
        "overview": raw.get("overview"),
        "genres": genres,
        "cast_top5": cast,
        "poster_path": raw.get("poster_path"),
        "release_year": int(year_raw[:4]) if year_raw else None,
        "imdb_rating": raw.get("vote_average"),
        "imdb_id": imdb_id,
        "language": raw.get("original_language"),
        "runtime_mins": runtime,
    }
