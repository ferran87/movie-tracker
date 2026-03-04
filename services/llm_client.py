import os
import json
import time
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from utils.prompt_builder import build_recommendation_prompt

load_dotenv(Path(__file__).parent.parent / ".env", override=True)

_MODEL = "claude-haiku-4-5-20251001"


def get_recommendations(
    watch_data: list[dict],
    taste_data: list[dict],
    skipped_titles: list[str],
    media_filter: str = "all",
) -> list[dict]:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = build_recommendation_prompt(watch_data, taste_data, skipped_titles, media_filter)

    for attempt in range(3):
        try:
            message = client.messages.create(
                model=_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                time.sleep(5 * (attempt + 1))  # 5s, then 10s
            else:
                raise
    text = message.content[0].text.strip()
    # Strip markdown code fences if Claude adds them
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)
