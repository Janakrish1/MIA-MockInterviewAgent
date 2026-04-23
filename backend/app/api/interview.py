"""Adaptive interview pipeline (LangGraph): generate question + validate + score answer + adapt difficulty."""
import asyncio
from statistics import mean

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.graph.graph import get_interview_graph
from app.graph.state import InterviewState
from app.services.interview_feedback_store import append_feedback, read_feedback

router = APIRouter()


class TurnRequest(BaseModel):
    resume_summary: str = ""
    focus_area: str = "Software Engineering"
    interview_id: str | None = None
    conversation_history: list[dict[str, str]]  # [{"role":"user"|"assistant","content":"..."}]
    last_user_answer: str | None = None  # set when user just replied (so we score + adapt)
    current_question: str | None = None  # the question we're scoring (when last_user_answer is set)


class TurnResponse(BaseModel):
    question: str  # next question to speak/show
    feedback: str | None = None  # from LangGraph "score_answer" node (LLM evaluates your answer; only when last_user_answer was provided)
    difficulty: str | None = None  # from LangGraph "adapt_difficulty" node (easy/medium/hard) for the next question


class InterviewReportResponse(BaseModel):
    interview_id: str
    total_answers_scored: int
    average_score: float | None
    feedback_entries: list[dict]


def _run_graph(initial: InterviewState) -> dict:
    """Sync graph invocation (run in thread)."""
    graph = get_interview_graph()
    final_state = graph.invoke(initial)
    return final_state


def _build_interviewer_prompt(question: str, score: float | None) -> str:
    """Create natural interviewer transition before the next question."""
    if score is None:
        return question
    if score >= 4.0:
        prefix = "Great answer. Let's build on that."
    elif score <= 2.0:
        prefix = "Thanks for sharing. Let's break it down one step further."
    else:
        prefix = "Good effort. Let's go a bit deeper."
    return f"{prefix} {question}"


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
        # Force a single interview domain regardless of client input.
        "focus_area": "Software Engineering",
        "conversation_history": body.conversation_history,
        "current_difficulty": "medium",
        "current_question": body.current_question,
        "last_user_answer": body.last_user_answer,
    }
    try:
        final = await asyncio.to_thread(_run_graph, initial)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    next_question = final.get("final_question") or "Let's continue. What would you like to explore next?"
    feedback = final.get("feedback_for_user")
    score = final.get("last_score")
    difficulty = final.get("current_difficulty")

    if body.interview_id and body.last_user_answer and body.current_question and feedback is not None:
        append_feedback(
            interview_id=body.interview_id,
            entry={
                "question": body.current_question,
                "answer": body.last_user_answer,
                "score": score,
                "feedback": feedback,
                "next_difficulty": difficulty,
                "next_question": next_question,
            },
        )

    # Keep feedback in backend for reporting, but present interviewer-style response in UI.
    conversational_question = _build_interviewer_prompt(next_question, score if body.last_user_answer else None)
    return TurnResponse(question=conversational_question, feedback=None, difficulty=difficulty)


@router.get("/report/{interview_id}", response_model=InterviewReportResponse)
async def interview_report(interview_id: str):
    entries = read_feedback(interview_id)
    numeric_scores = [float(e["score"]) for e in entries if isinstance(e.get("score"), (int, float))]
    avg = round(mean(numeric_scores), 2) if numeric_scores else None
    return InterviewReportResponse(
        interview_id=interview_id,
        total_answers_scored=len(entries),
        average_score=avg,
        feedback_entries=entries,
    )
