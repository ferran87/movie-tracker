# 🎬 Movie & TV Tracker

A personal Streamlit app for tracking, rating, and getting AI-powered recommendations for movies and TV shows — built for two.

## Features

| Page | Description |
|------|-------------|
| **Random Rate** | Discover new titles by genre. Rate what you've seen, add to watchlist, or skip. Builds your taste profile for better recommendations. |
| **Recommendations** | Claude-powered recommendations based on your ratings. Includes diversity rules for European TV shows, non-English productions, and hidden gems. |
| **Watchlist** | Titles saved to watch next, from both the Random Rate and Recommendations pages. |
| **Search & Add** | Search TMDB to manually log a watched title and record ratings. |

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [SQLite](https://www.sqlite.org/) — local database
- [TMDB API](https://www.themoviedb.org/documentation/api) — movie/TV metadata and posters
- [Anthropic Claude API](https://www.anthropic.com/) — AI recommendations (claude-haiku-4-5)

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ferran87/movie-tracker.git
cd movie-tracker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```
TMDB_API_KEY=your_tmdb_v3_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

- Get a free TMDB API key at [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
- Get an Anthropic API key at [console.anthropic.com](https://console.anthropic.com/)

### 4. Run the app

```bash
streamlit run app.py
```

Or on Windows, double-click **`start.bat`** — it kills any existing instances, clears cache, and starts fresh on port 8501.

## Project Structure

```
movie-tracker/
├── app.py                  # Entry point + navigation
├── pages/
│   ├── 0_Random_Rate.py    # Discovery & rating page
│   ├── 1_Recommendations.py
│   ├── 2_Watchlist.py
│   └── 3_Search_and_Add.py
├── db/
│   └── database.py         # SQLite layer (all DB functions)
├── services/
│   ├── tmdb_client.py      # TMDB API wrapper
│   └── llm_client.py       # Anthropic API wrapper
├── utils/
│   └── prompt_builder.py   # Claude prompt construction
├── start.bat               # Windows launcher script
└── requirements.txt
```

## Notes

- The database (`tracker.db`) and `.env` file are excluded from version control.
- The app is designed for local/personal use — no authentication or multi-user support.
