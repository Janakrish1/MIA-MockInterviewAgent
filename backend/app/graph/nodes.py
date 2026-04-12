"""Nodes for the adaptive interview LangGraph pipeline."""
from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.llm import get_llm
from app.graph.state import InterviewState

MAX_QUESTION_RETRIES = 2


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "(No prior messages yet.)"
    lines = []
    for m in history:
        role = m.get("role", "unknown")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"{role.upper()}: {content}")
    print("Format history: ", lines)
    return "\n".join(lines) if lines else "(No prior messages yet.)"


def generate_question(state: InterviewState) -> dict:
    """Generate next interview question using resume + history + current difficulty."""
    llm = get_llm()
    resume = state.get("resume_summary") or "(No resume provided.)"
    focus = state.get("focus_area") or "Software Engineering"
    difficulty = state.get("current_difficulty") or "medium"
    history = state.get("conversation_history") or []
    last_feedback = state.get("last_feedback")

    history_str = _format_history(history)
    prompt = f"""You are MIA, a Mock Interview Agent. Conduct a technical software engineering interview.
Focus area: {focus}
Current difficulty level: {difficulty}
Candidate resume summary: {resume}

Conversation so far:
{history_str}
"""
    if last_feedback:
        prompt += f"\nScoring feedback from last answer (use to adapt): {last_feedback}\n"

    prompt += "\nOutput exactly ONE clear interview question. No preamble, no numbering. Just the question."

    messages = [
        SystemMessage(content="You output only a single interview question, nothing else. No greeting or explanation."),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    question = (response.content or "").strip()
    print("Generate question: ", question)
    return {"candidate_question": question, "retry_count": state.get("retry_count", 0)}


def validate_question(state: InterviewState) -> dict:
    """Validate that the generated question is acceptable (clear, relevant, not duplicate)."""
    llm = get_llm()
    candidate = state.get("candidate_question") or ""
    history_str = _format_history(state.get("conversation_history") or [])
    retry_count = state.get("retry_count", 0)

    messages = [
        SystemMessage(content="You are a validator. Reply with exactly YES or NO and nothing else."),
        HumanMessage(
            content=f"Is this a clear, relevant, non-duplicate technical interview question? "
            f"Conversation so far:\n{history_str}\n\nQuestion to validate: {candidate}\n\nAnswer YES or NO."
        ),
    ]
    response = llm.invoke(messages)
    answer = (response.content or "").strip().upper()
    valid = "YES" in answer and "NO" not in answer[:4]
    print("Validate question: ", answer, valid)
    if valid:
        return {"question_valid": True, "final_question": candidate}
    # Invalid: increment retry; accept candidate anyway if we've exhausted retries
    new_retry = retry_count + 1
    return {
        "question_valid": False,
        "retry_count": new_retry,
        "final_question": candidate if new_retry >= MAX_QUESTION_RETRIES else None,
    }


def score_answer(state: InterviewState) -> dict:
    """Score the candidate's answer and produce brief feedback (rubric-style)."""
    llm = get_llm()
    question = state.get("current_question") or ""
    answer = state.get("last_user_answer") or ""

    messages = [
        SystemMessage(
            content="You are an interview scoring agent. Score the answer from 1 (poor) to 5 (excellent). "
            "Then give one short sentence of feedback. Format your reply exactly as: SCORE: <1-5> FEEDBACK: <sentence>"
        ),
        HumanMessage(
            content=f"Question: {question}\n\nCandidate answer: {answer}\n\nOutput SCORE: <number> FEEDBACK: <sentence>"
        ),
    ]
    response = llm.invoke(messages)
    text = (response.content or "").strip()
    score = 3.0
    feedback = text
    print("Score answer: ", text)
    if "SCORE:" in text.upper():
        parts = text.upper().split("FEEDBACK:", 1)
        try:
            score_str = parts[0].replace("SCORE:", "").strip()
            score = float(score_str.strip(". ")[:1])
            if score < 1 or score > 5:
                score = 3.0
        except Exception:
            pass
        feedback = parts[1].strip() if len(parts) > 1 else text
    return {"last_score": score, "last_feedback": feedback, "feedback_for_user": feedback}


def adapt_difficulty(state: InterviewState) -> dict:
    """Adjust difficulty for next question based on last score."""
    score = state.get("last_score") or 3.0
    current = (state.get("current_difficulty") or "medium").lower()
    next_difficulty = current
    print("Adapt difficulty: ", score, current, next_difficulty)
    if score >= 4.0 and current == "easy":
        next_difficulty = "medium"
    elif score >= 4.0 and current == "medium":
        next_difficulty = "hard"
    elif score <= 2.0 and current == "hard":
        next_difficulty = "medium"
    elif score <= 2.0 and current == "medium":
        next_difficulty = "easy"
    return {"current_difficulty": next_difficulty}
