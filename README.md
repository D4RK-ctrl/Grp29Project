# TripAgent — Agentic Travel Planning System

> Assignment #14 · Group 29

TripAgent turns a free-text travel brief (e.g. *"5 days in Bangkok in March, mid-range
budget, love street food and temples"*) into a complete, day-by-day itinerary. A tool-calling
LLM agent researches flights, hotels, activities, restaurants and weather in real time,
detects scheduling conflicts, and streams its progress to the UI live. You can then ask for
changes in plain English ("make day 3 more relaxed", "swap the museum for a market") and the
agent revises the plan.

---

## Features

- **Free-text brief → full itinerary** — no rigid forms; describe the trip in a sentence.
- **Tool-calling agent** — researches flights, hotels, activities, restaurants and weather
  through dedicated tools, with a Tavily web-search fallback whenever a provider key is absent.
- **Live progress streaming** — the UI shows each `status` / `tool_call` / `tool_result` event
  over a WebSocket as the agent works, instead of a blank spinner.
- **Conflict detection** — a post-pass flags and auto-resolves overlapping time slots in the
  generated day plan.
- **Conversational revisions** — refine an existing plan in plain English and the agent
  re-plans only what changed.
- **Graceful degradation** — only `LLM_API_KEY` is required to run; every external data source
  is optional.

---

## Architecture

```
┌──────────────────┐        REST (axios)         ┌───────────────────────────┐
│   React + Vite   │ ──────────────────────────▶ │      FastAPI backend      │
│   (frontend)     │                             │                           │
│                  │ ◀───── WebSocket stream ──── │  ┌─────────────────────┐  │
│  Home / Trip     │   (live agent progress)     │  │   Agent orchestrator │  │
│  Dashboard       │                             │  │   (tool-calling loop)│  │
└──────────────────┘                             │  └──────────┬──────────┘  │
                                                 │             │ tools       │
                                                 │  flights · hotels ·       │
                                                 │  activities · restaurants │
                                                 │  · weather · web_search   │
                                                 │             │             │
                                                 │   SQLAlchemy (SQLite/PG)  │
                                                 └───────────────────────────┘
```

**Backend (`/backend`)** — FastAPI + SQLAlchemy.
- `agent/orchestrator.py` — the agent loop. Calls any **OpenAI-compatible chat-completions
  API** (Groq by default) with function/tool calling, executes the requested tools
  concurrently, feeds results back, and repeats until the model returns a final JSON itinerary.
  Includes retry/backoff on rate limits and a post-pass that detects and auto-resolves
  time-overlap conflicts.
- `agent/tools.py` — the six tools the agent can call. Flights and hotels are answered via web
  search (Tavily); activities use Foursquare, restaurants use Yelp, weather uses OpenWeatherMap,
  each with a web-search fallback when no key is configured.
- `routers/trips.py` — REST endpoints; planning/change work runs in a background thread.
- `routers/stream.py` — WebSocket endpoint that streams `status` / `tool_call` / `tool_result`
  / `complete` / `error` events (with heartbeats) to the frontend.
- `db.py` — settings, SQLAlchemy engine and the `trips` / `changes` tables.

**Frontend (`/frontend`)** — React 18 + Vite + Tailwind + React Router.
- `pages/Home.tsx` — brief intake. `pages/TripDashboard.tsx` — itinerary + live agent feed.
- `hooks/useAgentStream.ts` — opens the WebSocket and accumulates progress messages.
- `hooks/useTrip.ts` — REST calls (create trip, poll trip, request change).
- `components/Itinerary/*`, `components/Dashboard/*`, `components/Chat/*` — timeline, day cards,
  flight/hotel/activity segments, conflict banner and agent-thinking UI.

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in at least LLM_API_KEY (see below)
uvicorn main:app --reload   # serves on http://localhost:8000
```
The database tables are created automatically on startup. With no `DATABASE_URL` set it
defaults to a local SQLite file (`trips.db`) — no extra setup needed for local dev.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local  # defaults point at localhost:8000
npm run dev                 # serves on http://localhost:5173
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `LLM_API_KEY` | **Yes** | — | Key for an OpenAI-compatible chat API |
| `LLM_BASE_URL` | No | `https://api.groq.com/openai/v1` | Works with Groq, OpenAI, OpenRouter, etc. |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Any model the chosen provider supports |
| `DATABASE_URL` | No | `sqlite:///./trips.db` | A `postgres://` URL is normalised to `postgresql://` automatically |
| `FOURSQUARE_API_KEY` | No | — | Activities (falls back to web search if unset) |
| `YELP_API_KEY` | No | — | Restaurants (falls back to web search if unset) |
| `TAVILY_API_KEY` | No | — | Powers flight/hotel search and all web-search fallbacks |
| `OPENWEATHER_API_KEY` | No | — | Weather (falls back to web search if unset) |

Only `LLM_API_KEY` is strictly required to boot and plan a trip — every external data tool
degrades gracefully to a Tavily web search when its key is missing. Add `TAVILY_API_KEY` for
markedly better results, then the others as needed.

**Where to get free keys:** Groq — [console.groq.com](https://console.groq.com) ·
Tavily — [tavily.com](https://tavily.com) ·
Foursquare — [location.foursquare.com/developer](https://location.foursquare.com/developer) ·
Yelp — [yelp.com/developers](https://www.yelp.com/developers) ·
OpenWeather — [openweathermap.org/api](https://openweathermap.org/api)

### Frontend (`frontend/.env.local`)

| Variable | Default | Notes |
|----------|---------|-------|
| `VITE_API_URL` | `http://localhost:8000` | Base URL for REST calls |
| `VITE_WS_URL` | `ws://localhost:8000` | Base URL for the WebSocket stream (use `wss://` in prod) |

---

## API Reference

Base path: `/api/trips`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/trips` | Create a trip from a `{ "brief": "..." }`; planning starts in the background |
| `GET` | `/api/trips` | List the 20 most recent trips |
| `GET` | `/api/trips/{trip_id}` | Fetch a trip and its itinerary |
| `POST` | `/api/trips/{trip_id}/change` | Request a change with `{ "change_request": "..." }` |
| `DELETE` | `/api/trips/{trip_id}` | Delete a trip |
| `WS` | `/api/trips/{trip_id}/stream` | Live agent progress events |
| `GET` | `/health` | Health check |

Interactive API docs are available at `http://localhost:8000/docs` when the backend is running.

---

## Deployment

- **Backend → Render** — uses `backend/render.yaml`. Set `LLM_API_KEY` (and any optional data
  keys) as environment variables, and `DATABASE_URL` if using a managed Postgres instance.
- **Frontend → Vercel** — uses `frontend/vercel.json`. Set `VITE_API_URL` and `VITE_WS_URL`
  to your deployed backend (remember `wss://` for the WebSocket).

---

## Project Layout

```
backend/
  main.py              FastAPI app, CORS, router wiring, health check
  db.py                Settings, SQLAlchemy engine, trip/change models
  models.py            Pydantic request/response schemas
  stream_queue.py      Thread-safe queue bridging agent thread ↔ WebSocket
  agent/
    orchestrator.py    Tool-calling agent loop + conflict detection/resolution
    tools.py           Tool implementations and JSON-schema definitions
    prompts.py         Planning and change-request system prompts
  routers/
    trips.py           REST endpoints (create/list/get/change/delete)
    stream.py          WebSocket streaming endpoint
frontend/
  src/
    App.tsx            Routes
    pages/             Home (intake) and TripDashboard
    hooks/             useAgentStream (WebSocket), useTrip (REST)
    components/        Itinerary, Dashboard and Chat UI
    types/             Shared itinerary/stream types
```

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `500` on `POST /api/trips` or planning never completes | `LLM_API_KEY` is missing or invalid — check `backend/.env` and the backend logs. |
| Agent runs but flights/hotels look generic | No `TAVILY_API_KEY` set, so search falls back to the model's own knowledge. Add the key for live results. |
| Frontend can't reach the API | Confirm the backend is on `:8000` and `VITE_API_URL` / `VITE_WS_URL` in `frontend/.env.local` match it. |
| Live agent feed never updates | WebSocket blocked — in production use `wss://` and make sure proxies allow upgrade connections. |
| Rate-limit errors from the LLM provider | The orchestrator retries with backoff; persistent `429`s mean you've hit the provider quota. |

---

## Tech Stack

**Backend:** Python · FastAPI · SQLAlchemy · httpx · Pydantic · WebSockets
**Frontend:** TypeScript · React 18 · Vite · Tailwind CSS · React Router · axios
**External APIs:** OpenAI-compatible LLM (Groq) · Tavily · Foursquare · Yelp · OpenWeatherMap
