from pathlib import Path

from langchain_core.messages import AIMessage
from streamlit.testing.v1 import AppTest

import app


def test_quick_prompt_keeps_manual_chat_available(monkeypatch):
    class FakeAgent:
        def __init__(self):
            self.questions = []

        def invoke(self, state, config):
            self.questions.append(state["messages"][0].content)
            return {
                "messages": [AIMessage(content="A concise answer.")],
                "active_guest": None,
            }

    agent = FakeAgent()
    monkeypatch.setattr(app, "alfred", agent)
    dashboard_path = Path(__file__).resolve().parents[1] / "src" / "dashboard.py"
    app_test = AppTest.from_file(dashboard_path).run()

    app_test.button[0].click().run()

    assert len(app_test.chat_input) == 1
    app_test.chat_input[0].set_value("A manually typed question").run()

    assert agent.questions == [
        "Tell me about 'Lady Ada Lovelace'. What's her background and how is she related to me?",
        "A manually typed question",
    ]
