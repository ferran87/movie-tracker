import json


def build_recommendation_prompt(
    watch_data: list[dict],
    taste_data: list[dict],
    skipped_titles: list[str],
    media_filter: str = "all",
) -> str:
    if media_filter != "all":
        watch_data = [w for w in watch_data if w.get("media_type") == media_filter]

    has_watch = bool(watch_data)
    has_taste = bool(taste_data)

    if not has_watch and not has_taste:
        return "[]"

    sections = []

    if has_watch:
        lines = []
        for i, item in enumerate(watch_data, 1):
            genres_raw = item.get("genres") or "[]"
            genres = json.loads(genres_raw) if isinstance(genres_raw, str) else genres_raw
            genre_str = ", ".join(genres) if genres else "Unknown"
            user_score = item.get("user_score")
            wife_score = item.get("wife_score")
            user_str = f"{user_score}/10" if user_score is not None else "not rated"
            wife_str = f"{wife_score}/10" if wife_score is not None else "not rated"
            year = item.get("release_year") or "?"
            mtype = item.get("media_type", "?")
            lines.append(
                f"{i}. {item.get('title', 'Unknown')} ({mtype}, {year}) — Genres: {genre_str}\n"
                f"   [My rating: {user_str}] [Wife's rating: {wife_str}]"
            )
        sections.append("Titles they have watched and rated:\n" + "\n".join(lines))

    if has_taste:
        lines = []
        for i, item in enumerate(taste_data, 1):
            user_score = item.get("user_score")
            wife_score = item.get("wife_score")
            user_str = f"{user_score}/10" if user_score is not None else "not rated"
            wife_str = f"{wife_score}/10" if wife_score is not None else "not rated"
            lines.append(
                f"{i}. {item.get('title', 'Unknown')} (not watched yet)\n"
                f"   [My interest rating: {user_str}] [Wife's interest rating: {wife_str}]"
            )
        sections.append("Titles they haven't watched but rated by interest:\n" + "\n".join(lines))

    context_block = "\n\n".join(sections)
    filter_note = f"Only recommend {media_filter}s." if media_filter != "all" else "You can recommend both movies and TV shows."

    skip_note = ""
    if skipped_titles:
        skip_note = f"\nDo NOT recommend any of these titles (already seen or skipped): {', '.join(skipped_titles)}\n"

    return f"""You are a movie and TV show recommendation assistant for a couple.
Here is their taste profile:

{context_block}
{skip_note}
Based on their combined taste — identify the underlying themes, tones, and genres they enjoy most, then surface titles (including lesser-known gems) that match those patterns deeply — recommend exactly 10 titles they haven't seen yet.
{filter_note}

Diversity rules — follow these strictly:
- Include at least 2 non-English-language productions (European, Korean, Latin American, etc.).
- Include at least 1 European TV show (Spain, France, Italy, Scandinavia, UK, Germany, etc.).
- Include at least 2 lesser-known or critically acclaimed titles that are NOT mainstream blockbusters.
- Vary release years — do not cluster all picks in the same decade.
- Do not recommend sequels or franchise entries unless that franchise is clearly present in their taste profile.

Return your response as a JSON array of exactly 10 objects. Each object must have:
- "title": exact title string
- "year": integer release year (or null if unknown)
- "media_type": "movie" or "tv"
- "genres": array of genre name strings
- "reason": 1-2 sentence explanation grounded in their specific ratings and preferences

Only return the JSON array. No markdown, no extra text, no code blocks.
"""
