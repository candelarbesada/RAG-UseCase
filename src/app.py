import re
import sys
from pathlib import Path
from typing import TypedDict, Annotated, NotRequired
from uuid import uuid4

import httpx

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

from agent.prompts import build_prompt
from agent.retriever import find_guest_name, guest_info_tool
from agent.tools import get_weather, search_tool, visit_webpage_tool

# Generate the chat interface, including the tools
llm = ChatOllama(model="qwen2.5", temperature=0)
tools = [guest_info_tool, search_tool, visit_webpage_tool, get_weather]
chat_with_tools = llm.bind_tools(tools)
memory = MemorySaver()
MAX_HISTORY_MESSAGES = 6
MAX_HISTORY_MESSAGE_LENGTH = 1000
DEFAULT_USER_NAME = "Bruce Wayne"


class OllamaUnavailableError(RuntimeError):
    """Raised when the local Ollama service refuses a model connection."""


# Generate the AgentState and Agent graph
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    active_guest: NotRequired[str]
    user_name: NotRequired[str]


def _extract_guest_name(question: str) -> str | None:
    dataset_name = find_guest_name(question)
    if dataset_name:
        return dataset_name

    q = question.strip()
    patterns = [
        r"(?:tell me about|who is|about|this is)\s+['\"]?([A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+){0,3})['\"]?",
        r"\b([A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+){0,3})\b"
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            name = match.group(1).strip()
            if name.lower() not in {"what", "who", "how", "why", "when", "where", "tell", "me", "about", "this", "that"}:
                return name
    return None


def _is_weather_question(question: str) -> bool:
    q = question.lower()
    return "weather" in q or "forecast" in q or "rain" in q or "temperature" in q


def _extract_location(question: str) -> str:
    q = question.strip()
    lower_q = q.lower()

    patterns = [
        r"\bin\s+([A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+){0,2})",
        r"\bweather\s+(?:is|like|in)\s+([A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+){0,2})",
        r"\bforecast\s+(?:is|like|in)\s+([A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+){0,2})",
        r"\btemperature\s+(?:is|like|in)\s+([A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+){0,2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            location = match.group(1).strip()
            if location.lower() not in {"our", "the", "this", "that", "for", "will", "it", "be", "suitable"}:
                return location

    for city in ["Paris", "London", "Madrid", "Berlin", "New York", "Rome", "Barcelona", "Tokyo"]:
        if city.lower() in lower_q:
            return city

    return "Paris"


def _resolve_guest_reference(question: str, previous_guest: str | None) -> str | None:
    q = question.lower()
    pronouns = {"she", "he", "her", "him", "they", "them", "their"}
    if previous_guest and any(word in q for word in pronouns):
        return previous_guest
    return _extract_guest_name(question)


def _guard_missing_fact(question: str, context: str) -> str | None:
    q = question.lower()
    lower_context = context.lower()

    if _is_guest_relation_question(question) and not re.search(
        r"^Relation:\s*\S",
        context,
        re.MULTILINE | re.IGNORECASE,
    ):
        return "I don't have that relationship information in the retrieved guest data."

    if "project" in q and "project" not in lower_context:
        return "The retrieved context does not provide information about specific projects."

    return None


def _extract_user_name(message: str) -> str | None:
    patterns = (
        r"\bmy name is\s+([A-ZÀ-Ý][A-Za-zÀ-ÿ'’-]*)",
        r"\bmine is\s+([A-ZÀ-Ý][A-Za-zÀ-ÿ'’-]*)",
    )
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _is_user_name_question(question: str) -> bool:
    normalized = question.lower().replace("’", "'")
    return bool(
        re.search(r"\bwhat(?:'s| is)\s+my name\b", normalized)
        or re.search(r"\bwho am i\b", normalized)
        or re.search(r"\bwhat did i tell you my name was\b", normalized)
    )


def _is_guest_relation_question(question: str) -> bool:
    return bool(re.search(r"\b(relation|relationship|related|connection)\b", question, re.IGNORECASE))


def _answer_guest_relation(question: str, context: str) -> str | None:
    if not _is_guest_relation_question(question):
        return None

    guest_match = re.search(r"^Name:\s*(.+)$", context, re.MULTILINE | re.IGNORECASE)
    relation_match = re.search(r"^Relation:\s*(.+)$", context, re.MULTILINE | re.IGNORECASE)
    if not guest_match or not relation_match:
        return None

    guest_name = guest_match.group(1).strip()
    relation = relation_match.group(1).strip()
    if relation.lower() in {"no relation", "none", "no known relation"}:
        return f"{guest_name} has no recorded relation to you."

    return f"{guest_name} is your {relation}."


def _format_conversation_history(messages: list[AnyMessage]) -> str:
    """Format a bounded number of prior user/assistant messages for the model."""
    history = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "User"
        elif isinstance(message, AIMessage):
            role = "Alfred"
        else:
            continue

        if isinstance(message.content, str) and message.content.strip():
            content = message.content.strip()[:MAX_HISTORY_MESSAGE_LENGTH]
            history.append(f"{role}: {content}")

    return "\n".join(history[-MAX_HISTORY_MESSAGES:])


def assistant(state: AgentState):
    latest_message = state["messages"][-1]
    question = latest_message.content if hasattr(latest_message, "content") else str(latest_message)
    user_name = _extract_user_name(question) or state.get("user_name") or DEFAULT_USER_NAME
    conversation_updates = {"user_name": user_name} if user_name else {}

    if user_name and _is_user_name_question(question):
        return {
            "messages": [AIMessage(content=f"Your name is {user_name}.")],
            **conversation_updates,
        }

    if _is_weather_question(question):
        location = _extract_location(question)
        when = "tonight" if "tonight" in question.lower() else "today"
        return {
            "messages": [AIMessage(content=get_weather.invoke({"location": location, "when": when}))],
            **conversation_updates,
        }

    previous_guest = state.get("active_guest")
    guest_ref = _resolve_guest_reference(question, previous_guest)
    guest_name = guest_ref or previous_guest

    if guest_name:
        context = guest_info_tool.invoke(guest_name)
    else:
        context = guest_info_tool.invoke(question)

    relation_answer = _answer_guest_relation(question, context)
    if relation_answer:
        if guest_name:
            state["active_guest"] = guest_name
        return {
            "messages": [AIMessage(content=relation_answer)],
            "active_guest": guest_name or previous_guest,
            **conversation_updates,
        }

    guard = _guard_missing_fact(question, context)
    if guard:
        response = AIMessage(content=guard)
        if guest_name:
            state["active_guest"] = guest_name
        return {
            "messages": [response],
            "active_guest": guest_name or previous_guest,
            **conversation_updates,
        }

    conversation_history = _format_conversation_history(state["messages"][:-1])
    prompt = build_prompt(question, context, conversation_history)
    try:
        response = chat_with_tools.invoke([HumanMessage(content=prompt)])
    except httpx.ConnectError as error:
        raise OllamaUnavailableError(
            "Alfred could not connect to Ollama at its local address. Start Ollama "
            "(for example, run `ollama serve` in a separate PowerShell window), "
            "then retry. If the model is not installed, run `ollama pull qwen2.5`."
        ) from error

    if guest_name:
        state["active_guest"] = guest_name
    elif "lady ada lovelace" in question.lower() or "ada lovelace" in question.lower():
        state["active_guest"] = "Ada Lovelace"

    return {
        "messages": [response],
        "active_guest": state.get("active_guest", previous_guest),
        **conversation_updates,
    }


# The graph
builder = StateGraph(AgentState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latests message requires a tool, route to tools
    # Otherwise, provide a direct response
    tools_condition,
)
builder.add_edge("tools", "assistant")
alfred = builder.compile(checkpointer=memory)


def new_conversation_id() -> str:
    """Return an isolated identifier for a new conversation."""
    return str(uuid4())


def clear_conversation(conversation_id: str) -> None:
    """Remove a conversation's in-memory checkpoint state."""
    memory.delete_thread(conversation_id)


if __name__ == "__main__":
    messages = [HumanMessage(content="Tell me about 'Lady Ada Lovelace'. What's her background and how is she related to me?")]
    response = alfred.invoke({"messages": messages})

    print("Alfred's Response:")
    print(response["messages"][-1].content)
    print()

    # Second interaction (referencing the first)
    response = alfred.invoke({"messages": response["messages"] + [HumanMessage(content="What projects is she currently working on?")]})

    print("Alfred's Response:")
    print(response["messages"][-1].content)