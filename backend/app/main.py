"""MIA Backend — Mock Interview Agent API."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api import chat, interview, resume, speech
from app.graph.graph import GRAPH_PNG_PATH, get_interview_graph

app = FastAPI(
    title="MIA Backend",
    description="Mock Interview Agent — Azure OpenAI + Azure Speech",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173", "http://127.0.0.1:8080", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(speech.router, prefix="/api/speech", tags=["speech"])


@app.on_event("startup")
def _compile_graph_on_startup():
    """Compile the LangGraph pipeline at startup so langgraph.png is generated and /api/langgraph/image works."""
    try:
        get_interview_graph()
    except Exception:
        pass


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/langgraph/image")
def langgraph_image():
    """Serve the LangGraph pipeline PNG (generated when the graph is first compiled). Open in browser: GET /api/langgraph/image"""
    if not GRAPH_PNG_PATH.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Graph image not generated yet. Trigger an interview turn once to compile the graph.")
    return FileResponse(GRAPH_PNG_PATH, media_type="image/png")
