"""LangGraph for adaptive interview pipeline with OpenSearch retrieval."""
import os
from pathlib import Path

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes import (
    MAX_QUESTION_RETRIES,
    adapt_difficulty,
    generate_followup_question,
    generate_question,
    retrieve_related_questions,
    score_answer,
    validate_question,
)
from app.graph.state import InterviewState

# Where to write the graph PNG when the graph is compiled (so you can see node connections)
GRAPH_PNG_PATH = Path(__file__).resolve().parent.parent.parent / "langgraph.png"


def _route_after_score(state: InterviewState) -> str:
    """Route at graph start.

    If the user just answered a previous question, run the scoring branch
    (score_answer -> retrieve -> adapt -> generate/followup). Otherwise this is
    the first technical turn: still run retrieval so the first question is
    grounded against the resume/intro, then generate.
    """
    if state.get("last_user_answer") and state.get("current_question"):
        return "score_answer"
    return "retrieve_related_questions"


def _route_after_validate(state: InterviewState) -> str:
    """If question valid, end. Else retry generate if under limit."""
    if state.get("question_valid"):
        return "__end__"
    if (state.get("retry_count") or 0) < MAX_QUESTION_RETRIES:
        return "generate_question"
    return "__end__"


def _route_after_adapt(state: InterviewState) -> str:
    """
    Ask a follow-up when score indicates the previous answer needs deeper probing;
    otherwise move to a fresh question.
    """
    if not (state.get("last_user_answer") and state.get("current_question")):
        return "generate_question"
    threshold = float(os.environ.get("FOLLOWUP_SCORE_THRESHOLD", "3.5"))
    score = float(state.get("last_score") or 3.0)
    if score < threshold:
        return "generate_followup_question"
    return "generate_question"


def build_interview_graph() -> CompiledStateGraph[InterviewState, dict, dict]:
    """Build and compile the interview pipeline graph."""
    builder = StateGraph(InterviewState)

    builder.add_node("generate_question", generate_question)
    builder.add_node("generate_followup_question", generate_followup_question)
    builder.add_node("validate_question", validate_question)
    builder.add_node("score_answer", score_answer)
    builder.add_node("retrieve_related_questions", retrieve_related_questions)
    builder.add_node("adapt_difficulty", adapt_difficulty)

    # Start: either score (if user answered) or generate first question. path_map is required for correct graph viz.
    builder.add_conditional_edges(
        "__start__",
        _route_after_score,
        path_map={
            "score_answer": "score_answer",
            "retrieve_related_questions": "retrieve_related_questions",
        },
    )

    # User requested retrieval before difficulty adaptation.
    builder.add_edge("score_answer", "retrieve_related_questions")
    # After retrieval: if we just scored an answer, go adapt difficulty;
    # otherwise (first technical turn) go straight to question generation.
    builder.add_conditional_edges(
        "retrieve_related_questions",
        lambda s: "adapt_difficulty"
        if s.get("last_user_answer") and s.get("current_question")
        else "generate_question",
        path_map={
            "adapt_difficulty": "adapt_difficulty",
            "generate_question": "generate_question",
        },
    )
    builder.add_conditional_edges(
        "adapt_difficulty",
        _route_after_adapt,
        path_map={
            "generate_followup_question": "generate_followup_question",
            "generate_question": "generate_question",
        },
    )

    builder.add_edge("generate_question", "validate_question")
    builder.add_edge("generate_followup_question", "validate_question")
    builder.add_conditional_edges(
        "validate_question",
        _route_after_validate,
        path_map={"__end__": END, "generate_question": "generate_question"},
    )

    return builder.compile()


# Compiled graph singleton for reuse
_compiled_graph: CompiledStateGraph[InterviewState, dict, dict] | None = None


def _write_graph_png(compiled: CompiledStateGraph[InterviewState, dict, dict]) -> None:
    """Write LangGraph structure to langgraph.png (and .mmd) so you can see how nodes are connected."""
    try:
        drawable = compiled.get_graph()
        drawable.draw_mermaid_png(output_file_path=str(GRAPH_PNG_PATH))
        # Also write Mermaid source so you can inspect/edit at mermaid.live
        mermaid_path = GRAPH_PNG_PATH.with_suffix(".mmd")
        mermaid_path.write_text(drawable.draw_mermaid(), encoding="utf-8")
    except Exception:
        pass  # e.g. no mermaid CLI or API; skip so app still runs


def get_interview_graph() -> CompiledStateGraph[InterviewState, dict, dict]:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_interview_graph()
        _write_graph_png(_compiled_graph)
    return _compiled_graph
