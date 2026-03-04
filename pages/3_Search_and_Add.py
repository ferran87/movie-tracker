import streamlit as st
from datetime import date
from services.tmdb_client import search, get_details, get_poster_url, normalize
from db.database import insert_media, log_watch, save_rating

st.set_page_config(page_title="Search & Add", page_icon="🔍", layout="wide")
st.title("🔍 Search & Add")

PLATFORMS = ["Netflix", "Amazon Prime", "Disney+", "Apple TV+", "HBO Max", "YouTube", "Other"]
REACTIONS = ["loved", "liked", "meh", "disliked"]

media_type = st.radio("Type", ["movie", "tv"], format_func=lambda x: "Movie" if x == "movie" else "TV Show", horizontal=True)
query = st.text_input("Search title", placeholder="e.g. The Bear, Interstellar...")

results = []
if query:
    with st.spinner("Searching TMDB..."):
        results = search(query, media_type)

if results:
    options = {
        f"{r['title']} ({r['release_year'] or '?'})": r for r in results
    }
    chosen_label = st.selectbox("Select a result", list(options.keys()))
    chosen = options[chosen_label]

    col_img, col_info = st.columns([1, 3])
    with col_img:
        poster = get_poster_url(chosen["poster_path"])
        if poster:
            st.image(poster, width=180)
    with col_info:
        st.markdown(f"### {chosen['title']} ({chosen['release_year'] or '?'})")
        st.caption(chosen.get("overview", ""))
        st.caption(f"TMDB rating: {chosen['imdb_rating']}")

    st.divider()
    st.subheader("Log this viewing")

    with st.form("log_form"):
        watch_date = st.date_input("Date watched", value=date.today())
        platform = st.selectbox("Platform", [""] + PLATFORMS)
        notes = st.text_area("Notes (optional)", placeholder="What did you think?")

        st.markdown("**Your rating**")
        user_score = st.slider("Your score", 0.0, 10.0, 7.0, 0.5)
        user_reaction = st.selectbox("Your reaction", REACTIONS, key="user_rx")

        st.markdown("**Wife's rating**")
        wife_score = st.slider("Wife's score", 0.0, 10.0, 7.0, 0.5)
        wife_reaction = st.selectbox("Wife's reaction", REACTIONS, key="wife_rx")

        submitted = st.form_submit_button("Save", type="primary")

    if submitted:
        with st.spinner("Fetching full details and saving..."):
            raw = get_details(chosen["tmdb_id"], media_type)
            normalized = normalize(raw, media_type)
            media_id = insert_media(normalized)
            log_id = log_watch(
                media_id,
                watch_date.isoformat(),
                platform or None,
                notes or None,
            )
            save_rating(log_id, "user", user_score, user_reaction)
            save_rating(log_id, "wife", wife_score, wife_reaction)
        st.success(f"✅ '{chosen['title']}' logged successfully!")
