import re
import sys
from pathlib import Path
from typing import TypedDict, Annotated, NotRequired

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from agent.prompts import build_prompt
from agent.retriever import guest_info_tool
from agent.tools import get_weather, search_tool, visit_webpage_tool

# Generate the chat interface, including the tools
llm = ChatOllama(model="qwen2.5", temperature=0)
tools = [guest_info_tool, search_tool, visit_webpage_tool, get_weather]
chat_with_tools = llm.bind_tools(tools)


# Generate the AgentState and Agent graph
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    active_guest: NotRequired[str]


def _extract_guest_name(question: str) -> str | None:
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

    if "related to me" in q or "relation" in q or "related" in q:
        if "relation:" not in lower_context and "relationship" not in lower_context:
            return "I don't have that relationship information in the retrieved guest data."

    if "project" in q and "project" not in lower_context:
        return "The retrieved context does not provide information about specific projects."

    return None


def assistant(state: AgentState):
    latest_message = state["messages"][-1]
    question = latest_message.content if hasattr(latest_message, "content") else str(latest_message)

    if _is_weather_question(question):
        location = _extract_location(question)
        when = "tonight" if "tonight" in question.lower() else "today"
        return {"messages": [AIMessage(content=get_weather.invoke({"location": location, "when": when}))]}

    previous_guest = state.get("active_guest")
    guest_ref = _resolve_guest_reference(question, previous_guest)
    guest_name = guest_ref or previous_guest

    if guest_name:
        context = guest_info_tool.invoke(guest_name)
    else:
        context = guest_info_tool.invoke(question)

    guard = _guard_missing_fact(question, context)
    if guard:
        response = AIMessage(content=guard)
        if guest_name:
            state["active_guest"] = guest_name
        return {"messages": [response], "active_guest": guest_name or previous_guest}

    prompt = build_prompt(question, context)
    response = chat_with_tools.invoke([HumanMessage(content=prompt)])

    if guest_name:
        state["active_guest"] = guest_name
    elif "lady ada lovelace" in question.lower() or "ada lovelace" in question.lower():
        state["active_guest"] = "Ada Lovelace"

    return {"messages": [response], "active_guest": state.get("active_guest", previous_guest)}


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
alfred = builder.compile()


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