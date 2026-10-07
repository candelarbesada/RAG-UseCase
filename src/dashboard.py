import sys
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import alfred

st.set_page_config(
    page_title="Wayne Manor — Alfred",
    page_icon="🕰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #0f1115;
        --panel: #171b22;
        --panel-soft: #1d222a;
        --panel-strong: #11151b;
        --gold: #d9b36c;
        --gold-soft: #f3d79d;
        --text: #f3f3f1;
        --muted: #b4b7bc;
        --line: rgba(217, 179, 108, 0.25);
        --success: #90d9a7;
    }

    .stApp {
        background: radial-gradient(circle at top left, rgba(217, 179, 108, 0.08), transparent 30%),
                    linear-gradient(180deg, #0d0f13 0%, #11151b 100%);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(17, 21, 27, 0.98), rgba(11, 13, 18, 0.98));
        border-right: 1px solid var(--line);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: var(--gold-soft);
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }

    .subtitle {
        color: var(--muted);
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.72rem;
        margin-bottom: 1.2rem;
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(28, 33, 39, 0.95), rgba(17, 21, 27, 0.95));
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .metric-value {
        color: var(--gold-soft);
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 0.4rem;
    }

    .stChatMessage {
        border: 1px solid rgba(217, 179, 108, 0.12);
        border-radius: 18px;
        background: rgba(17, 21, 27, 0.8);
        padding: 0.25rem 0.35rem;
    }

    .stChatMessage[data-testid="chat-message-user"] {
        background: rgba(38, 44, 53, 0.9);
    }

    .stChatMessage[data-testid="chat-message-assistant"] {
        background: rgba(23, 27, 33, 0.95);
        border-color: rgba(217, 179, 108, 0.22);
    }

    .sidebar-button {
        background: rgba(217, 179, 108, 0.1);
        border: 1px solid rgba(217, 179, 108, 0.28);
        border-radius: 12px;
        color: var(--text);
        padding: 0.7rem 0.8rem;
        margin-bottom: 0.4rem;
    }

    .stButton > button {
        width: 100%;
        background: rgba(217, 179, 108, 0.12);
        color: var(--text);
        border: 1px solid rgba(217, 179, 108, 0.32);
        border-radius: 12px;
        padding: 0.65rem 0.8rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: rgba(217, 179, 108, 0.7);
        background: rgba(217, 179, 108, 0.18);
    }

    .stTextInput > div > div > input {
        background: rgba(17, 21, 27, 0.9);
        color: var(--text);
        border: 1px solid rgba(217, 179, 108, 0.28);
        border-radius: 12px;
    }

    .stExpander {
        background: rgba(17, 21, 27, 0.7);
        border: 1px solid rgba(217, 179, 108, 0.15);
        border-radius: 12px;
    }

    code {
        color: var(--gold-soft);
        background: rgba(0, 0, 0, 0.25);
        border-radius: 8px;
        padding: 0.15rem 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "trace" not in st.session_state:
    st.session_state.trace = []
if "last_context" not in st.session_state:
    st.session_state.last_context = "Awaiting instructions."
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

st.markdown('<div class="main-title">Wayne Manor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Intelligence desk • Alfred, your butler</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Quick brief")
    quick_prompts = [
        "Tell me about 'Lady Ada Lovelace'. What's her background and how is she related to me?",
        "Who is she related to?",
        "What is the weather in Paris today?",
        "Tell me about 'Nikola Tesla'.",
        "Who is 'Ada Lovelace' and what is her relationship to me?",
    ]

    for prompt in quick_prompts:
        if st.button(prompt, key=f"prompt_{prompt[:18]}"):
            st.session_state.pending_prompt = prompt

    st.markdown("---")

    if st.button("Clear the desk"):
        st.session_state.messages = []
        st.session_state.trace = []
        st.session_state.last_context = "Awaiting instructions."
        st.session_state.pending_prompt = None

    st.markdown("---")
    st.caption("Service status")
    st.success("Agent is ready")

metric_cols = st.columns(4)
with metric_cols[0]:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Current guest</div>
            <div class="metric-value">""" + (st.session_state.last_context if st.session_state.last_context else "No active guest") + """</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with metric_cols[1]:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Status</div>
            <div class="metric-value">Ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with metric_cols[2]:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Toolset</div>
            <div class="metric-value">4 active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with metric_cols[3]:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Service</div>
            <div class="metric-value">Confidential</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

chat_container = st.container()

if st.session_state.pending_prompt:
    user_input = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
else:
    user_input = st.chat_input("Ask Alfred for the latest update...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("The butler is preparing the answer..."):
        response = alfred.invoke({"messages": [HumanMessage(content=user_input)]})
        answer = response["messages"][-1].content
        st.session_state.messages.append({"role": "assistant", "content": answer})

    try:
        guest_name = response.get("active_guest")
        st.session_state.last_context = guest_name or "No active guest"
    except Exception:
        st.session_state.last_context = "No active guest"

    st.session_state.trace.append({
        "prompt": user_input,
        "response": answer,
        "context": st.session_state.last_context,
    })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.markdown("---")

with st.expander("Operational trace", expanded=False):
    if st.session_state.trace:
        for item in reversed(st.session_state.trace):
            st.markdown(f"**Question:** {item['prompt']}")
            st.markdown(f"**Context:** {item['context']}")
            st.markdown(f"**Answer:** {item['response']}")
            st.markdown("---")
    else:
        st.write("No log entries yet.")
