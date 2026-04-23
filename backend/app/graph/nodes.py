"""Nodes for the adaptive interview LangGraph pipeline."""
import os

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.llm import get_llm
from app.graph.state import InterviewState
from app.services.opensearch_embeddings import search_similar_questions

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


def _format_retrieved_questions(retrieved: list[dict[str, str | int | float | None]]) -> str:
    if not retrieved:
        return ""
    lines = []
    for idx, item in enumerate(retrieved, start=1):
        question = str(item.get("question") or "").strip()
        if not question:
            continue
        difficulty = str(item.get("difficulty") or "unknown").strip()
        category = str(item.get("category") or "unknown").strip()
        lines.append(f"{idx}. {question} (category: {category}, difficulty: {difficulty})")
    return "\n".join(lines)


def retrieve_related_questions(state: InterviewState) -> dict:
    """
    Retrieve top-k similar questions from OpenSearch to ground the next turn.

    Runs either after scoring (using the candidate's last answer as the query) or
    before generating the very first technical question (using the candidate's
    intro from conversation history and their resume as the query).
    """
    history = state.get("conversation_history") or []
    latest_user_msg = ""
    for m in reversed(history):
        if (m.get("role") or "").lower() == "user":
            latest_user_msg = (m.get("content") or "").strip()
            break
    resume_hint = (state.get("resume_summary") or "").strip()

    query = (
        (state.get("last_user_answer") or "").strip()
        or (state.get("current_question") or "").strip()
        or latest_user_msg
        or resume_hint
        or (state.get("focus_area") or "").strip()
    )
    if not query:
        return {"retrieval_query": None, "retrieved_questions": [], "retrieval_error": None}

    top_k = int(os.environ.get("OPENSEARCH_TOP_K", "3"))
    try:
        retrieved = search_similar_questions(
            query=query,
            top_k=top_k,
        )
        print(f"Retrieved {len(retrieved)} related questions for query: {query}")
        if retrieved:
            for idx, item in enumerate(retrieved, start=1):
                question = (item.get("question") or "").strip()
                category = item.get("category")
                difficulty = item.get("difficulty")
                score = item.get("score")
                print(
                    f"Retrieved Q{idx}: score={score} category={category} "
                    f"difficulty={difficulty} question={question}"
                )
        return {"retrieval_query": query, "retrieved_questions": retrieved, "retrieval_error": None}
    except Exception as exc:
        # Retrieval should not break the interview flow.
        print("OpenSearch retrieval error: ", str(exc))
        return {"retrieval_query": query, "retrieved_questions": [], "retrieval_error": str(exc)}


def generate_question(state: InterviewState) -> dict:
    """Generate next interview question using resume + history + current difficulty."""
    llm = get_llm()
    resume = state.get("resume_summary") or "(No resume provided.)"
    difficulty = state.get("current_difficulty") or "medium"
    history = state.get("conversation_history") or []
    last_feedback = state.get("last_feedback")
    retrieved_questions = state.get("retrieved_questions") or []

    history_str = _format_history(history)
    retrieved_str = _format_retrieved_questions(retrieved_questions)

    prompt = f"""You are MIA, a warm and professional software engineering interviewer.
You are already in the middle of a live mock interview with the candidate.

How to speak (very important):
- Speak naturally, like a real human interviewer.
- If the candidate has just said something (intro or answer), acknowledge it briefly and specifically (1 short sentence) before asking the next question.
- Tailor the next question to the candidate's resume, stated experience, tools, and role. Do not ask generic textbook questions if their resume shows specific expertise.
- Never restart or re-introduce yourself. You have already introduced yourself earlier.
- Do not add meta labels like "MIA:" or "Interviewer:". Do not number the turn.
- Keep the whole turn under 4 sentences.

Candidate resume / background summary:
{resume}

Current difficulty level for the next question: {difficulty}

Conversation so far:
{history_str}
"""
    if last_feedback:
        prompt += (
            "\nInternal scoring note about the candidate's last answer "
            "(use this to shape tone and depth, but DO NOT read it aloud): "
            f"{last_feedback}\n"
        )
    if retrieved_str:
        prompt += (
            "\nReference technical questions retrieved from the interview question bank "
            "(inspiration only - DO NOT copy them verbatim; adapt the underlying concept "
            "to the candidate's actual experience on their resume):\n"
            f"{retrieved_str}\n"
        )

    prompt += (
        "\nRespond as MIA now. Produce ONE natural interviewer turn containing, in order:\n"
        "1. A short, human acknowledgement of the candidate's last message (skip only if the candidate has not spoken yet).\n"
        "2. A smooth transition.\n"
        "3. ONE clear technical interview question tailored to the candidate's resume and the retrieved topics.\n"
        "End the turn with the question itself."
    )

    messages = [
        SystemMessage(
            content=(
                "You speak as a warm, professional human interviewer named MIA. "
                "You acknowledge what the candidate said and ask the next question naturally. "
                "Never re-introduce yourself. Output plain conversation only, no labels."
            )
        ),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    question = (response.content or "").strip()
    print("Generate question: ", question)
    return {"candidate_question": question, "retry_count": state.get("retry_count", 0)}


def generate_followup_question(state: InterviewState) -> dict:
    """Generate a targeted follow-up for the most recent question and answer."""
    llm = get_llm()
    resume = state.get("resume_summary") or "(No resume provided.)"
    difficulty = state.get("current_difficulty") or "medium"
    history = state.get("conversation_history") or []
    current_question = (state.get("current_question") or "").strip()
    last_user_answer = (state.get("last_user_answer") or "").strip()
    last_feedback = (state.get("last_feedback") or "").strip()
    retrieved_questions = state.get("retrieved_questions") or []

    history_str = _format_history(history)
    retrieved_str = _format_retrieved_questions(retrieved_questions)
    prompt = f"""You are MIA, a warm and professional software engineering interviewer.
The candidate's previous answer was weak or partial, and you want to help them go deeper on the SAME topic.

How to speak (very important):
- Speak naturally, like a real human interviewer.
- Briefly and supportively acknowledge the candidate's last answer (1 short sentence), without restating it word-for-word.
- Stay on the SAME topic as the previous question. Do not switch topics.
- Tailor the probe to the candidate's resume and experience.
- Never re-introduce yourself. No meta labels like "MIA:" or "Interviewer:". No numbering.
- Keep the whole turn under 4 sentences.

Current difficulty level: {difficulty}
Candidate resume / background summary:
{resume}

Previous interviewer question: {current_question}
Candidate answer: {last_user_answer}
Internal scoring note (do NOT read aloud): {last_feedback}

Conversation so far:
{history_str}
"""
    if retrieved_str:
        prompt += (
            "\nReference technical questions retrieved from the question bank "
            "(use only to understand the topic; DO NOT copy them verbatim):\n"
            f"{retrieved_str}\n"
        )

    prompt += (
        "\nRespond as MIA now. Produce ONE natural interviewer turn containing, in order:\n"
        "1. A short, human acknowledgement of the candidate's last answer.\n"
        "2. A smooth transition that stays on the same topic.\n"
        "3. ONE focused follow-up question that probes the missing depth on the SAME topic, tailored to the candidate's resume.\n"
        "End the turn with the follow-up question itself."
    )

    messages = [
        SystemMessage(
            content=(
                "You speak as a warm, professional human interviewer named MIA. "
                "You acknowledge what the candidate said and ask a focused follow-up on the same topic. "
                "Never re-introduce yourself. Output plain conversation only, no labels."
            )
        ),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    question = (response.content or "").strip()
    print("Generate follow-up question: ", question)
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
            content=(
                "You are validating an interviewer turn from MIA. The turn may include a brief "
                "acknowledgement of the candidate's last message followed by exactly one interview question. "
                "Reply YES if the turn contains a clear, relevant, non-duplicate technical question at the end "
                "and stays on software engineering. Reply NO otherwise.\n\n"
                f"Conversation so far:\n{history_str}\n\n"
                f"Turn to validate: {candidate}\n\nAnswer YES or NO."
            )
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
