import streamlit as st
from db.database import (
    get_rated_titles_for_llm, get_taste_ratings_for_llm,
    get_skipped_rec_tmdb_ids, add_recommendation_skip, save_taste_rating,
    add_to_watchlist, get_all_excluded_tmdb_ids,
)
from services.llm_client import get_recommendations
from services.tmdb_client import search, get_poster_url

st.set_page_config(page_title="Recommendations", page_icon="🤖", layout="wide")
st.title("🤖 AI Recommendations")
st.caption("Powered by Claude — personalized based on what you've both rated.")

with st.sidebar:
    st.header("Options")
    media_filter = st.radio(
        "Recommend",
        ["all", "movie", "tv"],
        format_func=lambda x: {"all": "Movies & TV", "movie": "Movies only", "tv": "TV Shows only"}[x],
    )

if "watch_data" not in st.session_state:
    st.session_state["watch_data"] = get_rated_titles_for_llm()
    st.session_state["taste_data"] = get_taste_ratings_for_llm()

watch_data = st.session_state["watch_data"]
taste_data = st.session_state["taste_data"]

if not watch_data and not taste_data:
    st.warning("Rate some titles on the **Discover & Rate** page or log watched titles first.")
    st.stop()

total_signals = len(watch_data) + len(taste_data)
with st.expander(f"Based on {total_signals} rated title(s) — click to preview"):
    if watch_data:
        st.markdown("**Watched & rated:**")
        for item in watch_data:
            score = item.get("user_score")
            score_str = f"{score}/10" if score is not None else "—"
            st.markdown(f"- **{item['title']}** ({item.get('release_year','?')}) — Rating: {score_str}")
    if taste_data:
        st.markdown("**Rated by interest (not watched):**")
        for item in taste_data:
            score = item.get("user_score")
            score_str = f"{score}/10" if score is not None else "—"
            st.markdown(f"- **{item['title']}** — Rating: {score_str}")

if st.button("✨ Get Recommendations", type="primary"):
    exclude_ids = get_all_excluded_tmdb_ids()

    # Tell Claude to avoid titles already rated on the landing page
    skipped_titles = [item["title"] for item in taste_data] + [item["title"] for item in watch_data]

    with st.spinner("Claude is thinking..."):
        recs = get_recommendations(watch_data, taste_data, skipped_titles, media_filter)

    # Enrich each rec with TMDB data (poster, rating, tmdb_id)
    enriched = []
    for rec in recs:
        title     = rec.get("title", "")
        mtype     = rec.get("media_type", "movie")
        results   = search(title, mtype)
        tmdb_data = results[0] if results else {}
        enriched.append({
            **rec,
            "tmdb_id":    tmdb_data.get("tmdb_id"),
            "poster_path": tmdb_data.get("poster_path"),
            "imdb_rating": tmdb_data.get("imdb_rating"),
            "overview":    tmdb_data.get("overview", rec.get("reason", "")),
        })

    # Filter out already watched, rated, or skipped titles
    enriched = [r for r in enriched if r.get("tmdb_id") not in exclude_ids]

    st.session_state["recs"]        = enriched
    st.session_state["rating_mode"] = set()

# ── Render recommendation cards ───────────────────────────────────────────────
recs: list[dict] = st.session_state.get("recs", [])
rating_mode: set = st.session_state.get("rating_mode", set())

if not recs:
    st.stop()

st.divider()
for i, rec in enumerate(recs):
    tmdb_id     = rec.get("tmdb_id")
    title       = rec.get("title", "Unknown")
    year        = rec.get("year") or "?"
    mtype       = "Movie" if rec.get("media_type") == "movie" else "TV Show"
    genres      = rec.get("genres", [])
    reason      = rec.get("reason", "")
    imdb_rating = rec.get("imdb_rating")
    poster      = get_poster_url(rec.get("poster_path"))

    col_img, col_info = st.columns([1, 4])

    with col_img:
        if poster:
            st.image(poster, width=150)
        else:
            st.markdown("🎞️")

    with col_info:
        st.markdown(f"### {title} ({year})")
        if genres:
            st.caption("  ·  ".join(genres))
        imdb_str = f"⭐ {imdb_rating:.1f} / 10" if imdb_rating else "No rating"
        st.markdown(f"`{mtype}`  ·  {imdb_str}")
        overview = rec.get("overview", "")
        if overview:
            st.write(overview[:300] + ("…" if len(overview) > 300 else ""))

        if tmdb_id in rating_mode:
            # Rating mode: show score selector + submit
            score_key = f"rec_score_{i}_{tmdb_id}"
            st.caption("Your rating:")
            st.segmented_control(
                "Rating", options=list(range(11)), default=5,
                key=score_key, label_visibility="collapsed",
            )
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.button("✅ Submit rating", key=f"submit_{i}_{tmdb_id}", type="primary", use_container_width=True):
                    score = st.session_state.get(score_key, 5)
                    if tmdb_id:
                        save_taste_rating(tmdb_id, title, "user", score)
                        add_recommendation_skip(tmdb_id, title)
                    st.session_state["recs"].pop(i)
                    st.session_state["rating_mode"].discard(tmdb_id)
                    st.toast(f"Rating saved for **{title}**!")
                    st.rerun()
            with col_cancel:
                if st.button("✕ Cancel", key=f"cancel_{i}_{tmdb_id}", use_container_width=True):
                    st.session_state["rating_mode"].discard(tmdb_id)
                    st.rerun()
        else:
            # Default mode: action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("👁 Already Watched", key=f"watched_{i}_{tmdb_id}", use_container_width=True):
                    st.session_state["rating_mode"].add(tmdb_id)
                    st.rerun()
            with col2:
                if st.button("📌 Add to Watchlist", key=f"wl_{i}_{tmdb_id}", use_container_width=True):
                    if tmdb_id:
                        add_to_watchlist(
                            tmdb_id, title, rec.get("media_type", "movie"),
                            rec.get("poster_path"), rec.get("overview", ""),
                        )
                    st.session_state["recs"].pop(i)
                    st.toast(f"**{title}** added to your watchlist!")
                    st.rerun()
            with col3:
                if st.button("⏭ Skip", key=f"skip_{i}_{tmdb_id}", use_container_width=True):
                    if tmdb_id:
                        add_recommendation_skip(tmdb_id, title)
                    st.session_state["recs"].pop(i)
                    st.rerun()

    st.divider()
