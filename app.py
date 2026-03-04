import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from db.database import init_db

load_dotenv(Path(__file__).parent / ".env", override=True)
init_db()

pg = st.navigation([
    st.Page("pages/0_Random_Rate.py",      title="Random Rate",     icon="🎬"),
    st.Page("pages/1_Recommendations.py",  title="Recommendations", icon="🤖"),
    st.Page("pages/2_Watchlist.py",        title="Watchlist",       icon="📌"),
    st.Page("pages/3_Search_and_Add.py",   title="Search & Add",    icon="🔍"),
])
pg.run()
