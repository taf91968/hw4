# Campus Customs — Homework 4

A customer website for **Campus Customs**, a Yale apparel shop. It has a **React + Vite + TypeScript** front end and a **Python FastAPI** back end whose brain is a **PydanticAI** shopping agent.

Shoppers can:
- browse and filter 102 products by category, size and price
- open single-item pages with live stock by size
- create an account and log in
- chat with an assistant that checks real prices and stock, shows matching products as cards on the page, remembers logged-in shoppers, and suggests in-stock alternatives when a size is sold out

## What's in this repository

```
hw4/
├── backend/                 FastAPI app — run Uvicorn from this folder
│   ├── main.py              API app (the file Uvicorn runs): products, accounts, chat
│   ├── prompts/prompt.md    ┐
│   ├── agent.py             │ the agent: system prompt, agent wiring,
│   ├── tools.py             │ tools it can call, and Pydantic/PydanticAI types
│   ├── models.py            ┘
│   ├── db.py                database access (shared by the website and the tools)
│   ├── auth.py              password hashing, login, session cookie
│   ├── audit.py             append-only audit trail of agent activity
│   └── requirements.txt
├── frontend/                React + Vite + TypeScript site
├── output/                  harness.md, usability.md, design.md, app_check.html (+ images), audit_trail.json
├── scripts/                 app_check_shots.py (re-takes the app_check screenshots)
├── AI_prompt.md             log of every prompt used to build this
├── .env.example             settings template (placeholders only)
└── data/                    ← NOT in the repo: put the data pack here (see step 1)
```

**The agent is four files in `backend/`:**

| File | Role |
|---|---|
| `prompts/prompt.md` | System prompt: Campus Customs voice and how to answer |
| `agent.py` | Agent wiring |
| `tools.py` | The 7 tools the agent can call |
| `models.py` | Pydantic / PydanticAI types |

`main.py` exposes the agent at `POST /api/chat`.

**Left out on purpose** (see `.gitignore`):
- the real `.env`
- the database `campus_customs.db`
- the product images
- `node_modules`

## Requirements

- Python 3.11+ (developed on 3.13)
- Node.js 20+ (developed on Node 24)
- A Portkey API key

## 1. Place the data pack

Download the course data pack, [data.zip](https://zlisto.github.io/mgt_409_fa26/data/hw4/data.zip), and unzip it so that `data/` sits **inside `hw4/`**:

```
hw4/
└── data/
    ├── campus_customs.db        SQLite: catalogue, inventory, users, chat_messages
    └── products/                102 product photos (*.jpg)
```

PowerShell, from the `hw4` folder:

```powershell
Invoke-WebRequest https://zlisto.github.io/mgt_409_fa26/data/hw4/data.zip -OutFile data.zip
Expand-Archive data.zip -DestinationPath . ; Remove-Item data.zip
```

Optional: keep an untouched copy to reset accounts and chats later.

```powershell
Copy-Item data\campus_customs.db data\campus_customs.seed.db
```

## 2. Settings (.env)

Copy `.env.example` to `.env` (in `hw4/` or `hw4/backend/`) and fill in your key:

```
PORTKEY_API_KEY=your_portkey_api_key_here
OPENAI_MODEL=gpt-5.6-luna
SESSION_SECRET=any_long_random_string
```

If `PORTKEY_API_KEY` is already set as an environment variable, you can skip `.env`. **Never commit `.env`.**

## 3. Run the back end (FastAPI + agent)

From `hw4/backend`:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API runs at http://localhost:8000; try http://localhost:8000/api/health. On OneDrive or Dropbox, pause syncing while creating the virtual environment and installing packages.

## 4. Run the front end (React + Vite)

In a second terminal, from `hw4/frontend`:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server forwards `/api` and `/media` to the back end on port 8000, so run both.

**Test account** (from the data pack): `Test@campuscustoms.yale.edu` / `password`.

**Things to try:**
- In the chat, ask "What hoodies do you have?" The matching cards appear on the page; click one to open its product page.
- On a product page, click **Ask about this item** and tap "Is this in stock in M?".
- On **Products**, choose **Hoodies** and size **M**.
- On the Fencing Left Chest Hoodie, click **Find similar in L**.
- Log in, chat, log out and log back in; your chat comes back.

## Troubleshooting

| Problem | Fix |
|---|---|
| Products don't load / "Is the backend running?" | Start the back end (step 3) and check that `data/campus_customs.db` exists. |
| Chat says the assistant "isn't set up yet" | Set `PORTKEY_API_KEY` (step 2) and restart Uvicorn. |
| An edit doesn't take effect with `--reload` (Windows) | Stop Uvicorn (Ctrl+C), check port 8000 is free (`netstat -ano \| findstr :8000`), and start it again. |
| Photos missing | Check that `data/products/*.jpg` exists (step 1). |

## Documentation

- **`output/harness.md`:** how the system works. Start with "Start here"; Part 10 is the reference (models and why, tools, safety rules, limits).
- **`output/usability.md`, `output/design.md`:** the usability and design changes and why.
- **`output/app_check.html`:** live-site test with screenshots (double-click to open).
- **`output/audit_trail.json`:** append-only log of agent runs (JSON Lines).
- **`AI_prompt.md`:** every prompt used to build the project.
