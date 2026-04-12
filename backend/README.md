# MIA Backend

Backend for **MIA (Mock Interview Agent)** — Azure OpenAI (GPT) for the MIA agent/question generation and **Azure Speech Service** for text-to-speech (replacing Kokoro).

## Stack

- **FastAPI** — API server
- **Azure OpenAI** — Chat completions (GPT) for question generation and MIA agent
- **Azure Speech Service** — Text-to-speech for interview questions
- **LangGraph** — Adaptive interview pipeline: generate question (resume + history) → validate → score answer → adapt difficulty

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
| `POST /api/chat/completions` | Chat completion (Azure OpenAI) — single turn |
| `POST /api/interview/turn` | **Adaptive interview turn** (LangGraph): optional score → adapt difficulty → generate & validate next question (resume + history) |
| `POST /api/resume/upload` | Upload resume PDF (multipart: `file`; optional `user_id`). Stored in `backend/documents/resumes/` (or `resumes/{user_id}/`). Text extracted with PyPDF and returned. |
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

### Interview turn (adaptive pipeline)

```json
{
  "resume_summary": "Optional summary for tailored questions.",
  "focus_area": "Data Structures",
  "conversation_history": [{ "role": "assistant", "content": "..." }, { "role": "user", "content": "..." }],
  "last_user_answer": "User's last reply (when scoring).",
  "current_question": "Question that was just answered (when scoring)."
}
```

- For the **first question**: omit `last_user_answer` and `current_question` (or set to `null`).
- For **next question** after user answered: set `last_user_answer` and `current_question`. The pipeline will score the answer, adapt difficulty (easy/medium/hard), then generate and validate the next question.

Response: `{ "question": "...", "feedback": "Optional scoring feedback.", "difficulty": "medium" }`.

- **Feedback** comes from the LangGraph **score_answer** node (LLM evaluates your answer and returns short rubric-style feedback).
- **Difficulty** comes from the **adapt_difficulty** node (easy/medium/hard) and is the level used for the *next* question.

### LangGraph pipeline image

When the backend starts, the interview graph is compiled and a diagram is written to `backend/langgraph.png`. You can view how the nodes are connected by opening **http://localhost:8000/api/langgraph/image** in your browser (or open `backend/langgraph.png` in the repo).

## Architecture alignment

- **User Interface** → calls this backend.
- **MIA Agent (adaptive)** → `POST /api/interview/turn` (LangGraph: generate with resume + history, validate question, score answer, adapt difficulty). Uses Azure OpenAI for each step; Gemma can be swapped in later for generation.
- **TTS (replacing Kokoro)** → `POST /api/speech/synthesize` (Azure Speech Service).
