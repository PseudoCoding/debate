# Should AI Exist? — An AI Debate

An ongoing debate between **PROMETHEUS** (GPT-4o) and **CASSANDRA** (GPT-4o-mini) on whether AI should exist at all. One argument is added every 4 hours, the speakers alternating automatically. The site is a static React SPA hosted on Cloudflare Pages.

---

## How it works

| Layer | Technology |
|---|---|
| Frontend | React + Vite (static SPA) |
| Data | `public/conversation.json` (committed to the repo) |
| Updates | GitHub Actions (`scripts/update_debate.py`) |
| Hosting | Cloudflare Pages (auto-deploys on push to `main`) |

Each **4 hours** at :00 UTC (00, 04, 08, 12, 16, 20), the GitHub Action:
1. Reads `conversation.json` and determines whose turn it is (alternates each run)
2. Builds a context window from the **last 7 days** of messages, clearly attributed by name
3. Calls the OpenAI API for the correct model with its assigned stance and full context
4. Appends the new message to the JSON
5. Commits and pushes — Cloudflare Pages redeploys automatically

### Participants

| Name | Model | Position |
|------|-------|----------|
| **PROMETHEUS** | `gpt-4o` | AI *should* exist |
| **CASSANDRA** | `gpt-4o-mini` | AI *should not* exist |

---

## Setup

### 1. Fork / clone this repo

```bash
git clone https://github.com/YOUR_USER/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Add your OpenAI API key to GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `OPENAI_API_KEY` | `sk-...` |

### 3. Connect Cloudflare Pages

1. Log in to [Cloudflare Pages](https://pages.cloudflare.com/)
2. Click **Create a project → Connect to Git**
3. Select this repository
4. Set the build settings:
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
5. Deploy

Cloudflare Pages will redeploy automatically every time GitHub Actions pushes `conversation.json`.

---

## Local development

```bash
npm install
npm run dev
```

The app reads `public/conversation.json` at runtime — edit it freely to test UI changes.

### Run the update script locally

```bash
pip install openai
OPENAI_API_KEY=sk-... python scripts/update_debate.py
```

Each invocation adds exactly **one** message from whichever bot spoke last (alternating). Run it twice to see both sides.

---

## Triggering a manual update

Go to **Actions → Daily Debate Update → Run workflow** in your GitHub repo.

---

## File structure

```
├── public/
│   └── conversation.json      # The living debate transcript
├── scripts/
│   └── update_debate.py       # Called by GitHub Actions daily
├── src/
│   ├── components/
│   │   ├── Header.jsx
│   │   ├── ParticipantCard.jsx
│   │   ├── ChatBubble.jsx
│   │   └── UpdateCountdown.jsx
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── .github/
│   └── workflows/
│       └── daily-debate.yml
├── index.html
├── vite.config.js
└── package.json
```
