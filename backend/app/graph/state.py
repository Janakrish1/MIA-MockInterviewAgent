"""State for the adaptive interview LangGraph pipeline."""
from typing import TypedDict


class InterviewState(TypedDict, total=False):
    """State passed through the interview graph."""

    resume_summary: str
    focus_area: str
    conversation_history: list[dict[str, str]]  # [{role, content}, ...]
    current_difficulty: str  # "easy" | "medium" | "hard"
    current_question: str | None  # question we are scoring (when user just answered)
    last_user_answer: str | None
    last_score: float | None
    last_feedback: str | None
    candidate_question: str | None  # output of generate_question
    question_valid: bool
    retry_count: int
    final_question: str | None  # validated question to return
    feedback_for_user: str | None  # from scoring, to show user
