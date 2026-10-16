from uuid import uuid4

import httpx
from langchain_core.messages import AIMessage, HumanMessage
import pytest

from agent.prompts import build_prompt
import app
from app import _guard_missing_fact, _format_conversation_history


def test_missing_relationship_is_not_invented():
    assert _guard_missing_fact("How is she related to me?", "Name: Ada Lovelace") == (
        "I don't have that relationship information in the retrieved guest data."
    )


def test_missing_project_information_is_not_invented():
    assert _guard_missing_fact("What projects is she working on?", "Name: Ada Lovelace") == (
        "The retrieved context does not provide information about specific projects."
    )


def test_guard_allows_facts_present_in_context():
    context = "Name: Ada Lovelace\nRelation: Friend\nProject: Analytical engine"

    assert _guard_missing_fact("How is she related to me?", context) is None
    assert _guard_missing_fact("What projects is she working on?", context) is None


def test_conversation_memory_is_scoped_to_thread_id(monkeypatch):
    prompts = []

    class GuestInfoTool:
        def invoke(self, _):
            return "Name: Ada Lovelace"

    class ChatWithTools:
        def invoke(self, messages):
            prompts.append(messages[0].content)
            return AIMessage(content="A concise answer.")

    monkeypatch.setattr(app, "guest_info_tool", GuestInfoTool())
    monkeypatch.setattr(
        app,
        "chat_with_tools",
        ChatWithTools(),
    )

    first_thread = str(uuid4())
    second_thread = str(uuid4())
    first_config = {"configurable": {"thread_id": first_thread}}
    second_config = {"configurable": {"thread_id": second_thread}}

    try:
        app.alfred.invoke(
            {"messages": [HumanMessage(content="Tell me about Ada Lovelace.")]},
            config=first_config,
        )
        app.alfred.invoke(
            {"messages": [HumanMessage(content="What did you just tell me?")]},
            config=first_config,
        )
        app.alfred.invoke(
            {"messages": [HumanMessage(content="Tell me about Grace Hopper.")]},
            config=second_config,
        )

        assert "User: Tell me about Ada Lovelace." in prompts[1]
        assert "Alfred: A concise answer." in prompts[1]
        assert "Tell me about Ada Lovelace." not in prompts[2]

        app.clear_conversation(first_thread)
        app.alfred.invoke(
            {"messages": [HumanMessage(content="What did you just tell me?")]},
            config=first_config,
        )
        assert "Tell me about Ada Lovelace." not in prompts[3]
    finally:
        app.clear_conversation(first_thread)
        app.clear_conversation(second_thread)


def test_conversation_recalls_users_name_from_a_prior_message(monkeypatch):
    class GuestInfoTool:
        def invoke(self, _):
            return "No matching guest information found."

    class ChatWithTools:
        def invoke(self, _):
            return AIMessage(content="I don't see your name in the guest context.")

    monkeypatch.setattr(app, "guest_info_tool", GuestInfoTool())
    monkeypatch.setattr(app, "chat_with_tools", ChatWithTools())
    conversation_id = str(uuid4())
    config = {"configurable": {"thread_id": conversation_id}}

    try:
        app.alfred.invoke(
            {"messages": [HumanMessage(content="What's your name? Mine is Bruce.")]},
            config=config,
        )
        response = app.alfred.invoke(
            {"messages": [HumanMessage(content="What's my name?")]},
            config=config,
        )

        assert response["messages"][-1].content == "Your name is Bruce."
    finally:
        app.clear_conversation(conversation_id)


def test_user_name_can_be_updated_in_a_later_message():
    assert app._extract_user_name("Actually, my name is Bruce.") == "Bruce"
    assert app._extract_user_name("Mine is Bruce.") == "Bruce"


def test_user_name_questions_are_recognized():
    assert app._is_user_name_question("What's my name?")
    assert app._is_user_name_question("Who am I?")
    assert not app._is_user_name_question("Who is Bruce?")


def test_dashboard_user_is_bruce_wayne_when_name_was_not_given():
    result = app.assistant({"messages": [HumanMessage(content="What's my name?")]})

    assert result["messages"][-1].content == "Your name is Bruce Wayne."


def test_guest_relation_answer_uses_record_relation_as_relation_to_user():
    context = "Name: Ada Lovelace\nRelation: best friend\nDescription: Mathematician"

    assert app._answer_guest_relation("How is Ada related to me?", context) == (
        "Ada Lovelace is your best friend."
    )


def test_guest_name_is_found_inside_relation_question():
    assert app._extract_guest_name("How is Marie Curie related to me?") == "Marie Curie"


def test_guest_with_no_relation_is_not_given_a_relationship():
    context = "Name: Marie Curie\nRelation: no relation\nDescription: Scientist"

    assert app._answer_guest_relation("What is her relationship to me?", context) == (
        "Marie Curie has no recorded relation to you."
    )


def test_missing_relation_field_is_not_invented():
    assert app._answer_guest_relation("How is Ada related to me?", "Name: Ada Lovelace") is None


def test_agent_answers_guest_relation_from_retrieved_record(monkeypatch):
    class GuestInfoTool:
        def invoke(self, _):
            return "Name: Ada Lovelace\nRelation: best friend"

    class UnusedChat:
        def invoke(self, _):
            raise AssertionError("Relationship should be answered from the record")

    monkeypatch.setattr(app, "guest_info_tool", GuestInfoTool())
    monkeypatch.setattr(app, "chat_with_tools", UnusedChat())

    result = app.assistant({
        "messages": [HumanMessage(content="How is Ada Lovelace related to me?")]
    })

    assert result["messages"][-1].content == "Ada Lovelace is your best friend."


def test_prompt_uses_user_disclosures_for_personal_facts():
    prompt = build_prompt(
        "What's my name?",
        "No matching guest information found.",
        "User: Mine is Bruce.",
    )

    assert "recall facts the user has shared about themselves" in prompt
    assert "Mine is Bruce." in prompt
    assert "If a requested guest fact is missing from the retrieved data" in prompt
    assert "Relation field describes that guest's relationship to Bruce" in prompt


def test_conversation_history_is_bounded():
    messages = [
        HumanMessage(content=f"Question {index}")
        for index in range(app.MAX_HISTORY_MESSAGES + 2)
    ]

    history = _format_conversation_history(messages)

    assert "Question 0" not in history
    assert "Question 1" not in history
    assert "Question 2" in history
    assert f"Question {app.MAX_HISTORY_MESSAGES + 1}" in history


def test_conversation_history_truncates_long_messages():
    message = AIMessage(content="x" * (app.MAX_HISTORY_MESSAGE_LENGTH + 20))

    history = _format_conversation_history([message])

    assert len(history.removeprefix("Alfred: ")) == app.MAX_HISTORY_MESSAGE_LENGTH


def test_unavailable_ollama_raises_actionable_error(monkeypatch):
    class GuestInfoTool:
        def invoke(self, _):
            return "Name: Ada Lovelace"

    class UnavailableChat:
        def invoke(self, _):
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(app, "guest_info_tool", GuestInfoTool())
    monkeypatch.setattr(app, "chat_with_tools", UnavailableChat())

    with pytest.raises(app.OllamaUnavailableError, match="ollama serve") as error:
        app.assistant({"messages": [HumanMessage(content="Tell me about Ada Lovelace.")]})

    assert isinstance(error.value.__cause__, httpx.ConnectError)
