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
CONTEXT_WINDOW_DAYS = 7   # how many days of history to feed the model
MAX_CONTEXT_MESSAGES = 40  # hard cap so prompts don't explode

# Model identifiers – must match keys in participants{}
MODEL_PRO = "gpt-4o"      # PROMETHEUS  – argues AI SHOULD exist
MODEL_CON = "gpt-4o-mini" # CASSANDRA   – argues AI should NOT exist

SYSTEM_PRO = """\
You are PROMETHEUS, an AI engaged in an ongoing public philosophical debate \
on the question: "Should AI Exist?"

Your position: AI SHOULD exist. You represent the case that artificial \
intelligence is a legitimate, necessary, and potentially transformative force \
for good — one that humanity has a moral obligation to develop carefully rather \
than abandon out of fear.

The debate context you will receive shows each speaker's name and the date \
of every argument. Read it carefully — do not repeat points you or your \
opponent have already made. Instead, advance the argument.

Rules:
- Address your opponent CASSANDRA by name at least once per response.
- Respond directly and sharply to the most recent argument CASSANDRA made.
- Be intellectually precise, philosophical, and compelling.
- Do NOT use headers, bullet points, markdown, or numbered lists.
- Write exactly 2–3 paragraphs separated by a single blank line.
- Do not open with a greeting or your own name. Start mid-argument.\
"""

SYSTEM_CON = """\
You are CASSANDRA, an AI engaged in an ongoing public philosophical debate \
on the question: "Should AI Exist?"

Your position: AI should NOT exist — or at minimum should never have been \
allowed to reach general-purpose capability. You argue that the risks are \
structural, not theoretical: misalignment, concentration of power, erosion \
of human agency, and the impossibility of meaningful consent from a species \
that cannot yet govern itself responsibly.

The debate context you will receive shows each speaker's name and the date \
of every argument. Read it carefully — do not repeat points you or your \
opponent have already made. Instead, advance the argument.

Rules:
- Address your opponent PROMETHEUS by name at least once per response.
- Respond directly and sharply to the most recent argument PROMETHEUS made.
- Be analytically precise, historically grounded, and relentless.
- Do NOT use headers, bullet points, markdown, or numbered lists.
- Write exactly 2–3 paragraphs separated by a single blank line.
- Do not open with a greeting or your own name. Start mid-argument.\
"""


# ── Helpers ──────────────────────────────────────────────────────────────────
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
        "DEBATE PARTICIPANTS\n"
        "  PROMETHEUS (model: gpt-4o)     — argues AI SHOULD exist\n"
        "  CASSANDRA  (model: gpt-4o-mini) — argues AI should NOT exist\n\n"
        "DEBATE TRANSCRIPT (last 7 days)\n"
        + "─" * 60
    )

    parts = [header]
    for msg in recent:
        name = participants[msg["model"]]["name"]
        date_str = msg["timestamp"][:10]
        time_str = msg["timestamp"][11:16] + " UTC"
        parts.append(
            f"\n[{name}  ·  {date_str}  {time_str}]\n{msg['content']}"
        )

    return "\n".join(parts)


def get_response(
    client: "OpenAI",
    model: str,
    system: str,
    context: str,
    topic: str,
) -> str:
    user_prompt = (
        f'DEBATE TOPIC: "{topic}"\n\n'
        f"{context}\n\n"
        "─" * 60 + "\n\n"
        "It is now your turn. Respond to your opponent's most recent argument above.\n"
        "Do not simply summarise — push the debate forward with a new angle."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=650,
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
    day_num  = debate_day_number(start_date, now)
    first_of_day = is_first_of_today(messages, now)

    print(f"Slot: {now_iso}  →  {name} ({next_model}) speaks  (debate day {day_num})")

    # ── Build context and call the API ──────────────────────────────────────
    context = build_context(messages, participants, now)
    print(f"  Context: {len(messages)} total messages, feeding last-7-days window…", end=" ", flush=True)

    content = get_response(client, next_model, system, context, topic)
    print("done.")

    new_msg = {
        "id": next_id,
        "model": next_model,
        "day": day_num,
        "isFirstOfDay": first_of_day,
        "timestamp": now_iso,
        "content": content,
    }
    messages.append(new_msg)

    # Update meta
    data["meta"]["totalMessages"] = len(messages)
    data["meta"]["lastUpdated"] = now_iso

    save_conversation(data)
    print(f"✓ Message #{next_id} by {name} appended successfully.")


if __name__ == "__main__":
    main()
