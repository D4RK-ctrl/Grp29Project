# TripAgent — Agentic Travel Planning System

Assignment #14 | Group 29

## Quick Start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in API keys
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local   # set VITE_API_URL=http://localhost:8000
npm run dev
```

## API Keys Required

| Key | Where to get | Free tier |
|-----|--------------|-----------|
| `GEMINI_API_KEY` | aistudio.google.com/app/apikey | Free tier available |
| `AMADEUS_CLIENT_ID/SECRET` | developers.amadeus.com | 2k calls/month |
| `FOURSQUARE_API_KEY` | location.foursquare.com/developer | 1k calls/day |
| `YELP_API_KEY` | yelp.com/developers | 500 calls/day |
| `TAVILY_API_KEY` | tavily.com | 1k searches/month |
| `OPENWEATHER_API_KEY` | openweathermap.org/api | 1k calls/day |

## Deploy

- **Backend** → Render (use `render.yaml`)
- **Frontend** → Vercel (set `VITE_API_URL` to your Render URL)
