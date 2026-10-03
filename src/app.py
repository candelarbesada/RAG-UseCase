from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from prompts import build_prompt
from retriever import guest_info_tool

load_dotenv()

# Generate the chat interface, including the tools
llm = ChatOllama(model="qwen2.5", temperature=0)
tools = [guest_info_tool]
chat_with_tools = llm.bind_tools(tools)


# Generate the AgentState and Agent graph
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def assistant(state: AgentState):
    latest_message = state["messages"][-1]
    question = latest_message.content if hasattr(latest_message, "content") else str(latest_message)
    context = guest_info_tool.invoke(question)
    prompt = build_prompt(question, context)
    response = chat_with_tools.invoke(prompt)
    return {"messages": [response]}


# The graph
builder = StateGraph(AgentState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")
alfred = builder.compile()

messages = [HumanMessage(content="Tell me about our guest named 'Lady Ada Lovelace'.")]
response = alfred.invoke({"messages": messages})

print("Alfred's Response:")
print(response["messages"][-1].content)