# MIA – Mock Interview Agent

Mock Interview Agent (MIA) – practice interviews with AI feedback.

## Project structure

- **`frontend/`** – React + Vite UI (interview flow, chat, TTS playback)
- **`backend/`** – FastAPI + Azure OpenAI (GPT) + Azure Speech (TTS)

## Getting started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Build: `npm run build`  
Preview: `npm run preview`  
Tests: `npm run test`

### Backend

See `backend/README.md`. From `backend/`: create `.env` (from `.env.example`), then:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Test the full interview flow (frontend + backend)

1. **Start the backend** (terminal 1): `cd backend && uvicorn app.main:app --reload --port 8000`
2. **Start the frontend** (terminal 2): `cd frontend && npm run dev`
3. Open **http://localhost:8080** → **Start Interview** → choose a focus area → **Begin Interview**.  
   The first question comes from Azure OpenAI and is spoken via Azure Speech. Type your answer and **Send** to get the next MIA response (with TTS).  
4. Optional: set `VITE_API_URL` in `frontend/.env` if your backend runs on a different host/port.
