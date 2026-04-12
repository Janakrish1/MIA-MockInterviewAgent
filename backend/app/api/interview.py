"""Adaptive interview pipeline (LangGraph): generate question + validate + score answer + adapt difficulty."""
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.graph.graph import get_interview_graph
from app.graph.state import InterviewState

router = APIRouter()


class TurnRequest(BaseModel):
    resume_summary: str = ""
    focus_area: str = "Software Engineering"
    conversation_history: list[dict[str, str]]  # [{"role":"user"|"assistant","content":"..."}]
    last_user_answer: str | None = None  # set when user just replied (so we score + adapt)
    current_question: str | None = None  # the question we're scoring (when last_user_answer is set)


class TurnResponse(BaseModel):
    question: str  # next question to speak/show
    feedback: str | None = None  # from LangGraph "score_answer" node (LLM evaluates your answer; only when last_user_answer was provided)
    difficulty: str | None = None  # from LangGraph "adapt_difficulty" node (easy/medium/hard) for the next question


def _run_graph(initial: InterviewState) -> dict:
    """Sync graph invocation (run in thread)."""
    graph = get_interview_graph()
    final_state = graph.invoke(initial)
    return final_state


@router.post("/turn", response_model=TurnResponse)
async def interview_turn(body: TurnRequest):
    """
    One step of the adaptive interview: optionally score last answer and adapt difficulty,
    then generate and validate the next question. Uses LangGraph (generate -> validate;
    if user answered, score -> adapt -> generate -> validate).
    """
    if not settings.is_azure_openai_configured:
        raise HTTPException(
            status_code=503,
            detail="Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.",
        )
    initial: InterviewState = {
        "resume_summary": body.resume_summary,
        "focus_area": body.focus_area,
        "conversation_history": body.conversation_history,
        "current_difficulty": "medium",
        "current_question": body.current_question,
        "last_user_answer": body.last_user_answer,
    }
    try:
        final = await asyncio.to_thread(_run_graph, initial)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    question = final.get("final_question") or "Let's continue. What would you like to explore next?"
    feedback = final.get("feedback_for_user")
    difficulty = final.get("current_difficulty")
    return TurnResponse(question=question, feedback=feedback, difficulty=difficulty)
