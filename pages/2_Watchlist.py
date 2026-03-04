import streamlit as st
from db.database import get_watchlist, remove_from_watchlist
from services.tmdb_client import get_poster_url

st.set_page_config(page_title="Watchlist", page_icon="📌", layout="wide")
st.title("📌 Watchlist")
st.caption("Movies and TV shows you want to watch next.")

items = get_watchlist()

if not items:
    st.info("Your watchlist is empty. Add titles from the **Recommendations** or **Random Rate** pages.")
    st.stop()

st.markdown(f"**{len(items)} title(s)** saved")
st.divider()

for item in items:
    tmdb_id    = item["tmdb_id"]
    title      = item["title"]
    mtype      = "Movie" if item["media_type"] == "movie" else "TV Show"
    overview   = item["overview"] or ""
    poster     = get_poster_url(item["poster_path"])
    added_at   = item["added_at"][:10] if item["added_at"] else ""

    col_img, col_info = st.columns([1, 4])

    with col_img:
        if poster:
            st.image(poster, width=150)
        else:
            st.markdown("🎞️")

    with col_info:
        st.markdown(f"### {title}")
        st.markdown(f"`{mtype}`  ·  Added {added_at}")
        if overview:
            st.write(overview[:300] + ("…" if len(overview) > 300 else ""))

        if st.button("🗑 Remove", key=f"remove_{tmdb_id}", use_container_width=False):
            remove_from_watchlist(tmdb_id)
            st.toast(f"**{title}** removed from watchlist.")
            st.rerun()

    st.divider()
