from langchain_core.documents import Document

from agent import retriever


def make_document(name: str, description: str = "") -> Document:
    return Document(
        page_content=f"Name: {name}\nDescription: {description}",
        metadata={"name": name},
    )


def test_extract_text_prefers_exact_guest_match(monkeypatch):
    ada = make_document("Ada Lovelace", "Mathematician")
    monkeypatch.setattr(retriever, "docs", [make_document("Grace Hopper"), ada])

    class UnusedRetriever:
        def invoke(self, query):
            raise AssertionError("BM25 should not run for an exact match")

    monkeypatch.setattr(retriever, "bm25_retriever", UnusedRetriever())

    assert retriever.extract_text("Ada Lovelace") == ada.page_content


def test_extract_text_uses_bm25_fallback(monkeypatch):
    result = make_document("Ada Lovelace", "Mathematician")
    monkeypatch.setattr(retriever, "docs", [make_document("Grace Hopper")])

    class MatchingRetriever:
        def invoke(self, query):
            return [result]

    monkeypatch.setattr(retriever, "bm25_retriever", MatchingRetriever())

    assert retriever.extract_text("Mathematician") == result.page_content


def test_extract_text_rejects_empty_query():
    assert retriever.extract_text("  ") == "No matching guest information found."
