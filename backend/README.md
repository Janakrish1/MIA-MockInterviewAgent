# MIA Backend

Backend for **MIA (Mock Interview Agent)** — Azure OpenAI (GPT) for the MIA agent/question generation and **Azure Speech Service** for text-to-speech (replacing Kokoro).

## Stack

- **FastAPI** — API server
- **Azure OpenAI** — Chat completions (GPT) for question generation and MIA agent
- **Azure Speech Service** — Text-to-speech for interview questions

## Setup

1. **Python 3.10+** (recommended: 3.11 or 3.12).

2. **Create a virtual environment and install dependencies:**

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Azure (use your free credits):**

   - Copy `.env.example` to `.env` and fill in your values.
   - **Azure OpenAI:** Create an [Azure OpenAI resource](https://portal.azure.com), deploy a model (e.g. `gpt-4o-mini` or `gpt-4o`), and set:
     - `AZURE_OPENAI_ENDPOINT`
     - `AZURE_OPENAI_API_KEY`
     - `AZURE_OPENAI_CHAT_DEPLOYMENT` (your deployment name)
   - **Azure Speech:** Create a [Speech resource](https://portal.azure.com) and set:
     - `AZURE_SPEECH_KEY`
     - `AZURE_SPEECH_REGION`

## Run

From the `backend` directory (with venv activated):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `POST /api/chat/completions` | Chat completion (Azure OpenAI) — for MIA agent / question generation |
| `POST /api/speech/synthesize` | Text-to-speech (Azure Speech) — returns WAV audio |

### Chat request body

```json
{
  "messages": [
    { "role": "system", "content": "You are a technical interviewer." },
    { "role": "user", "content": "Generate one software engineering interview question." }
  ],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

### Speech request body

```json
{
  "text": "Hello, this is your next interview question.",
  "voice_name": "en-US-JennyNeural"
}
```

`voice_name` is optional; default is `en-US-JennyNeural`. Response is `audio/wav`.

## Architecture alignment

- **User Interface** → calls this backend.
- **MIA Agent / question generation** → `POST /api/chat/completions` (Azure OpenAI).
- **TTS (replacing Kokoro)** → `POST /api/speech/synthesize` (Azure Speech Service).

Scoring agent and finetuned Gemma can be added later; this backend starts with Azure OpenAI + Azure Speech.
