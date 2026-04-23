"""LangGraph for adaptive interview pipeline with OpenSearch retrieval."""
from pathlib import Path

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes import (
    MAX_QUESTION_RETRIES,
    adapt_difficulty,
    generate_question,
    retrieve_related_questions,
    score_answer,
    validate_question,
)
from app.graph.state import InterviewState

# Where to write the graph PNG when the graph is compiled (so you can see node connections)
GRAPH_PNG_PATH = Path(__file__).resolve().parent.parent.parent / "langgraph.png"


def _route_after_score(state: InterviewState) -> str:
    """If we have a user answer to score, go to score_answer; else go to generate_question."""
    if state.get("last_user_answer") and state.get("current_question"):
        return "score_answer"
    return "generate_question"


def _route_after_validate(state: InterviewState) -> str:
    """If question valid, end. Else retry generate if under limit."""
    if state.get("question_valid"):
        return "__end__"
    if (state.get("retry_count") or 0) < MAX_QUESTION_RETRIES:
        return "generate_question"
    return "__end__"


def build_interview_graph() -> CompiledStateGraph[InterviewState, dict, dict]:
    """Build and compile the interview pipeline graph."""
    builder = StateGraph(InterviewState)

    builder.add_node("generate_question", generate_question)
    builder.add_node("validate_question", validate_question)
    builder.add_node("score_answer", score_answer)
    builder.add_node("retrieve_related_questions", retrieve_related_questions)
    builder.add_node("adapt_difficulty", adapt_difficulty)

    # Start: either score (if user answered) or generate first question. path_map is required for correct graph viz.
    builder.add_conditional_edges(
        "__start__",
        _route_after_score,
        path_map={"score_answer": "score_answer", "generate_question": "generate_question"},
    )

    # User requested retrieval before difficulty adaptation.
    builder.add_edge("score_answer", "retrieve_related_questions")
    builder.add_edge("retrieve_related_questions", "adapt_difficulty")
    builder.add_edge("adapt_difficulty", "generate_question")

    builder.add_edge("generate_question", "validate_question")
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
