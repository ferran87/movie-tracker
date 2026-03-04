import random
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from db.database import (
    get_watched_tmdb_ids, get_taste_rated_tmdb_ids,
    save_taste_rating, add_to_watchlist,
)
from services.tmdb_client import get_trending, get_popular, get_by_genre, get_poster_url

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

st.set_page_config(page_title="Random Rate", page_icon="🎬", layout="wide")
st.title("🎬 What do you think of these?")
st.caption("Rate titles you've seen, add to watchlist, or skip.")

GENRES = {
    "Action":      {"movie": 28,    "tv": 10759},
    "Comedy":      {"movie": 35,    "tv": 35},
    "Drama":       {"movie": 18,    "tv": 18},
    "Thriller":    {"movie": 53,    "tv": 9648},
    "Horror":      {"movie": 27,    "tv": 9648},
    "Sci-Fi":      {"movie": 878,   "tv": 10765},
    "Animation":   {"movie": 16,    "tv": 16},
    "Anime":       {"movie": 16,    "tv": 16, "lang": "ja"},
    "Romance":     {"movie": 10749, "tv": 10749},
    "Crime":       {"movie": 80,    "tv": 80},
    "Documentary": {"movie": 99,    "tv": 99},
}

DEFAULTS = ["Action", "Thriller", "Drama", "Crime"]

# ── Category filter (on page, above cards) ────────────────────────────────────
selected_genres = st.multiselect(
    "Categories",
    options=list(GENRES.keys()),
    default=DEFAULTS,
    key="genre_multiselect",
    label_visibility="collapsed",
)

if not selected_genres:
    st.info("Select at least one category above to load titles.")
    st.stop()


def build_pool(genres: list[str]) -> list[dict]:
    seen: set[int] = set()
    items: list[dict] = []

    for genre in genres:
        cfg = GENRES[genre]
        lang = cfg.get("lang")
        for mtype, gid_key in [("movie", "movie"), ("tv", "tv")]:
            gid = cfg.get(gid_key)
            if gid:
                for item in get_by_genre(gid, mtype, original_language=lang):
                    if item["tmdb_id"] not in seen:
                        items.append(item)
                        seen.add(item["tmdb_id"])

    watched = get_watched_tmdb_ids()
    taste_rated = get_taste_rated_tmdb_ids()
    exclude = watched | taste_rated
    candidates = [
        c for c in items
        if c["tmdb_id"] not in exclude
        and (c.get("imdb_rating") or 0) > 6.5
    ]

    recent = [c for c in candidates if (c.get("release_year") or 0) >= 2016]
    older  = [c for c in candidates if (c.get("release_year") or 0) < 2016]
    random.shuffle(recent)
    random.shuffle(older)
    return recent + older


def pop_next() -> dict | None:
    exclude = st.session_state["excluded"]
    while st.session_state["pool"]:
        candidate = st.session_state["pool"].pop(0)
        if candidate["tmdb_id"] not in exclude:
            return candidate
    return None


def replace_pick(i: int):
    next_pick = pop_next()
    if next_pick:
        st.session_state["picks"][i] = next_pick
    else:
        st.session_state["picks"].pop(i)


# Rebuild pool when genre selection changes or on first load
pool_key = tuple(sorted(selected_genres))
if "pool" not in st.session_state or st.session_state.get("active_genres") != pool_key:
    st.session_state["active_genres"] = pool_key
    st.session_state["excluded"] = get_watched_tmdb_ids() | get_taste_rated_tmdb_ids()
    with st.spinner("Loading titles..."):
        all_candidates = build_pool(selected_genres)
    st.session_state["pool"]  = all_candidates[3:]
    st.session_state["picks"] = all_candidates[:3]

picks: list[dict] = st.session_state["picks"]

if not picks:
    st.success("You've gone through everything in these categories! Try adding more genres or come back later.")
    st.stop()

# ── Cards ─────────────────────────────────────────────────────────────────────
for i, pick in enumerate(picks):
    tmdb_id      = pick["tmdb_id"]
    title        = pick["title"]
    year         = pick.get("release_year") or "?"
    mtype        = "Movie" if pick.get("media_type") == "movie" else "TV Show"
    imdb_rating  = pick.get("imdb_rating")
    raw_overview = pick.get("overview") or "No description available."
    overview     = raw_overview[:300] + ("…" if len(raw_overview) > 300 else "")
    poster       = get_poster_url(pick.get("poster_path"))
    genre_names  = pick.get("genre_names", [])

    st.divider()
    col_img, col_info = st.columns([1, 4])

    with col_img:
        if poster:
            st.image(poster, width=150)
        else:
            st.markdown("🎞️")

    with col_info:
        st.markdown(f"### {title} ({year})")
        # Genres displayed below the title
        if genre_names:
            st.caption("  ·  ".join(genre_names))
        imdb_str = f"⭐ {imdb_rating:.1f} / 10" if imdb_rating else "No rating"
        st.markdown(f"`{mtype}`  ·  {imdb_str}")
        st.write(overview)

        score_key = f"score_{i}_{tmdb_id}"
        st.caption("Your rating:")
        st.segmented_control(
            "Rating", options=list(range(11)), default=5,
            key=score_key, label_visibility="collapsed",
        )

        btn1, btn2, btn3 = st.columns(3)
        with btn1:
            if st.button("✅ Rated it", key=f"rate_{i}_{tmdb_id}", type="primary", use_container_width=True):
                score = st.session_state.get(score_key, 5)
                save_taste_rating(tmdb_id, title, "user", score)
                st.session_state["excluded"].add(tmdb_id)
                replace_pick(i)
                st.toast(f"Rating saved for **{title}**!")
                st.rerun()
        with btn2:
            if st.button("📌 Add to watchlist", key=f"wl_{i}_{tmdb_id}", use_container_width=True):
                add_to_watchlist(
                    tmdb_id, title, pick.get("media_type", "movie"),
                    pick.get("poster_path"), raw_overview,
                )
                replace_pick(i)
                st.toast(f"**{title}** added to your watchlist!")
                st.rerun()
        with btn3:
            if st.button("⏭ Not watched yet", key=f"skip_{i}_{tmdb_id}", use_container_width=True):
                replace_pick(i)
                st.rerun()
