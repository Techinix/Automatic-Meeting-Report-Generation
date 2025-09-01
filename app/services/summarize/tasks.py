from typing import Any, Dict, List
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from app.services.cache import CACHE
from app.services.celery_worker import c_worker
from app.core.config import settings
from app.services.summarize.utils import pull_model
from app.services.summarize.prompts import SUMMARIZATION_PROMPT
from app.schemas.langchain import SummarizationState, SummarizationResponseFormatter

pull_model(settings.MODEL_NAME, settings.OLLAMA_URL)

LLM = ChatOllama(model=settings.MODEL_NAME, base_url=settings.OLLAMA_URL)
SUMMARIZATION_MODEL = LLM.with_structured_output(SummarizationResponseFormatter)


def summarization_node(state: SummarizationState) -> Dict[str, Any]:
    """
    Analyze text and extract key information using semantic search.

    Args:
        state (SummarizationState): Current state containing conversation messages.

    Returns:
        Dict[str, Any]: State updated with summary, topics, decisions, and actions.
    """
    summarization_result = SUMMARIZATION_MODEL.invoke(state["messages"])
    return {
        **state,
        "summary": summarization_result.summary,
        "topics": summarization_result.topics,
        "decisions": summarization_result.decisions,
        "actions": summarization_result.actions
    }


def create_graph() -> StateGraph:
    """
    Create the summarization workflow graph.

    Returns:
        StateGraph: Compiled state graph for the summarization workflow.
    """
    workflow = StateGraph(SummarizationState)
    workflow.add_node("summarize", summarization_node)
    workflow.add_edge(START, "summarize")
    workflow.add_edge("summarize", END)
    return workflow.compile()


app = create_graph()

# Save graph visualization
print("Saving graph visualization to rag_graph.png")
try:
    app.get_graph(xray=True).draw_png("rag_graph.png")
    print("Graph visualization saved successfully.")
except Exception as e:
    print(f"Error drawing graph: {e}")
    print("Please ensure you have graphviz installed on your system.")


@c_worker.task
def summarize_text(conversation_key: str) -> str:
    """
    Perform advanced text summarization with semantic search capabilities.

    Args:
        conversation_key (str): Cache key of the conversation data.

    Returns:
        key (str): Cache key containing summarization result.
    """
    conversation = CACHE.load(conversation_key)

    def to_langchain_messages(turns: List[Any]) -> List[Any]:
        messages = [("system", SUMMARIZATION_PROMPT)]
        for t in turns:
            messages.append(("human", f"[{t.start:.1f}-{t.end:.1f}] {t.speaker}: {t.text}"))
        return messages

    messages = to_langchain_messages(conversation.turns)
    final_state = app.invoke({"messages": messages})

    result = {
        "turns": conversation.turns,
        "summary": final_state.get("summary", "Summary generation failed"),
        "topics": final_state.get("topics", []),
        "decisions": final_state.get("decisions", []),
        "actions": final_state.get("actions", []),
        "status": "success"
    }

    key: str = CACHE.save(result)
    return key
