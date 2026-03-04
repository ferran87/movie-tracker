import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from db.database import init_db

load_dotenv(Path(__file__).parent / ".env", override=True)

import os
_db_url = os.getenv("DATABASE_URL")
if not _db_url:
    st.error("DATABASE_URL is not set. Add it to your Streamlit secrets or .env file.")
    st.stop()

try:
    init_db()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

pg = st.navigation([
    st.Page("pages/0_Random_Rate.py",      title="Random Rate",     icon="🎬"),
    st.Page("pages/1_Recommendations.py",  title="Recommendations", icon="🤖"),
    st.Page("pages/2_Watchlist.py",        title="Watchlist",       icon="📌"),
    st.Page("pages/3_Search_and_Add.py",   title="Search & Add",    icon="🔍"),
])
pg.run()
