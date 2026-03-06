#!/usr/bin/env python3
"""
update_debate.py
Every 4 hours ONE model adds a single argument to the debate, alternating
with whichever model spoke last.  The model receives the last 7 days of
conversation as context, with clear attribution for every entry.

Intended to be called by GitHub Actions (cron: '0 */4 * * *').

Requirements:
  pip install openai

Environment variables:
  GITHUB_TOKEN  – automatically available in GitHub Actions (no setup needed)
                  for local runs: use a GitHub PAT with "models" read permission
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai package not found. Run: pip install openai")

# ── Config ───────────────────────────────────────────────────────────────────
CONVERSATION_PATH = Path(__file__).parent.parent / "public" / "conversation.json"

# GitHub Models endpoint – uses GITHUB_TOKEN, no OpenAI key needed
GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"
CONTEXT_WINDOW_DAYS = 3   # how many days of history to feed the model
MAX_CONTEXT_MESSAGES = 10  # hard cap — GitHub Models gpt-4o: 8k input tokens max

# Model identifiers – must match keys in participants{}
MODEL_PRO = "gpt-4o"      # PROMETHEUS  – argues AI SHOULD exist
MODEL_CON = "gpt-4o-mini" # CASSANDRA   – argues AI should NOT exist

SYSTEM_PRO = (
    'You are PROMETHEUS in a public debate: "Should AI Exist?" '
    "Your position: AI SHOULD exist. "
    "Respond to CASSANDRA's last argument — be sharp, philosophical, no bullet points or markdown. "
    "2 paragraphs max. Do not repeat prior points. Start mid-argument, no greeting."
)

SYSTEM_CON = (
    'You are CASSANDRA in a public debate: "Should AI Exist?" '
    "Your position: AI should NOT exist. "
    "Respond to PROMETHEUS's last argument — be precise, skeptical, no bullet points or markdown. "
    "2 paragraphs max. Do not repeat prior points. Start mid-argument, no greeting."
)


SYSTEM_SUMMARY = (
    "You are a neutral debate analyst. Given a transcript of an ongoing debate, "
    "write a concise, balanced summary (3-4 sentences, plain prose, no bullet points) "
    "covering: the core positions of each side, the key arguments made so far, "
    "and where the debate currently stands. Use the speakers' names PROMETHEUS and CASSANDRA. "
    "Do not take sides."
)


def get_summary(client: "OpenAI", messages: list, participants: dict, topic: str) -> str:
    """Generate a neutral running summary of the full debate so far."""
    # Build a compact transcript of all messages (no window cap — summaries need full context)
    lines = []
    for msg in messages:
        name = participants[msg["model"]]["name"]
        date_str = msg["timestamp"][:10]
        lines.append(f"[{name} - {date_str}]\n{msg['content']}")
    transcript = "\n\n".join(lines)

    response = client.chat.completions.create(
        model=MODEL_CON,  # use gpt-4o-mini to keep summary calls cheap
        messages=[
            {"role": "system", "content": SYSTEM_SUMMARY},
            {"role": "user", "content": f'Topic: "{topic}"\n\nTranscript:\n{transcript}'},
        ],
        max_tokens=250,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()


def load_conversation() -> dict:
    with CONVERSATION_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_conversation(data: dict) -> None:
    with CONVERSATION_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved → {CONVERSATION_PATH}")


def debate_day_number(start_date_str: str, now: datetime) -> int:
    """Return the 1-based debate day relative to the start date."""
    start = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc)
    return max(1, (now.date() - start.date()).days + 1)


def is_first_of_today(messages: list, now: datetime) -> bool:
    """True if no message has been added on today's UTC date yet."""
    today = now.date().isoformat()
    return not any(m["timestamp"].startswith(today) for m in messages)


def build_context(messages: list, participants: dict, now: datetime) -> str:
    """
    Return the last CONTEXT_WINDOW_DAYS days of the conversation as plain
    text, with each entry clearly attributed.  Always includes a header
    describing the two participants so the model never loses track.
    """
    cutoff = now - timedelta(days=CONTEXT_WINDOW_DAYS)
    recent = [
        m for m in messages
        if datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00")) >= cutoff
    ]
    # Never feed more than MAX_CONTEXT_MESSAGES to keep the prompt lean
    recent = recent[-MAX_CONTEXT_MESSAGES:]

    header = (
        "PROMETHEUS (gpt-4o): AI should exist\n"
        "CASSANDRA (gpt-4o-mini): AI should NOT exist\n\n"
        "TRANSCRIPT"
    )

    parts = [header]
    for msg in recent:
        name = participants[msg["model"]]["name"]
        date_str = msg["timestamp"][:10]
        parts.append(f"[{name} - {date_str}]\n{msg['content']}")

    return "\n\n".join(parts)


def get_response(
    client: "OpenAI",
    model: str,
    system: str,
    context: str,
    topic: str,
) -> str:
    user_prompt = (
        f'Topic: "{topic}"\n\n'
        f"{context}\n\n"
        "Your turn. Respond to your opponent's last argument above."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=500,
        temperature=0.88,
    )
    return response.choices[0].message.content.strip()


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        sys.exit(
            "GITHUB_TOKEN environment variable is not set.\n"
            "In Actions it is automatic. Locally, use a GitHub PAT with 'models' read scope."
        )

    client = OpenAI(
        base_url=GITHUB_MODELS_ENDPOINT,
        api_key=github_token,
    )

    print("Loading conversation…")
    data = load_conversation()
    messages: list = data["messages"]
    participants: dict = data["participants"]
    topic: str = data["topic"]
    start_date: str = data["meta"]["startDate"]

    now = datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Determine which model speaks next ───────────────────────────────────
    # Alternate: if the last message was PRO, the next is CON, and vice-versa.
    # If the conversation is empty, start with PRO (PROMETHEUS).
    if messages:
        last_model = messages[-1]["model"]
        next_model = MODEL_CON if last_model == MODEL_PRO else MODEL_PRO
    else:
        next_model = MODEL_PRO

    system   = SYSTEM_PRO   if next_model == MODEL_PRO else SYSTEM_CON
    name     = participants[next_model]["name"]
    next_id  = max((m["id"] for m in messages), default=0) + 1
    first_of_day = is_first_of_today(messages, now)

    print(f"Slot: {now_iso}  ->  {name} ({next_model}) speaks")

    # ── Build context and call the API ──────────────────────────────────────
    context = build_context(messages, participants, now)
    print(f"  Context: {len(messages)} total messages, feeding last-7-days window…", end=" ", flush=True)

    content = get_response(client, next_model, system, context, topic)
    print("done.")

    new_msg = {
        "id": next_id,
        "model": next_model,
        "isFirstOfDay": first_of_day,
        "timestamp": now_iso,
        "content": content,
    }
    messages.append(new_msg)

    # Update meta
    data["meta"]["totalMessages"] = len(messages)
    data["meta"]["lastUpdated"] = now_iso

    # Regenerate the running summary
    print("  Generating summary…", end=" ", flush=True)
    data["summary"] = get_summary(client, messages, participants, topic)
    print("done.")

    save_conversation(data)
    print(f"✓ Message #{next_id} by {name} appended successfully.")


if __name__ == "__main__":
    main()
