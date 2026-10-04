from pathlib import Path

from langchain_core.documents import Document
from langchain_core.tools import Tool
from langchain_community.retrievers import BM25Retriever
import pandas as pd


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "gala-invitees.parquet"

# Load the dataset
guest_dataset = pd.read_parquet(DATA_PATH)

# Convert dataset entries into Document objects
docs = [
    Document(
        page_content="\n".join([
            f"Name: {guest['name']}",
            f"Relation: {guest['relation']}",
            f"Description: {guest['description']}",
            f"Email: {guest['email']}"
        ]),
        metadata={"name": guest["name"]}
    )
    for guest in guest_dataset.to_dict(orient="records")
]

bm25_retriever = BM25Retriever.from_documents(docs)


def _normalize(text: str) -> str:
    return text.lower().strip().replace("'", "").replace('"', "")


def extract_text(query: str) -> str:
    """Return the single most relevant guest record for the user query."""
    if not query or not query.strip():
        return "No matching guest information found."

    normalized_query = _normalize(query)

    # Prefer exact matches on names or text in the record.
    exact_matches = []
    for doc in docs:
        doc_text = _normalize(doc.page_content)
        doc_name = _normalize(str(doc.metadata.get("name", "")))
        if normalized_query in doc_text or normalized_query in doc_name:
            exact_matches.append(doc)

    if exact_matches:
        return exact_matches[0].page_content

    # Fallback to retriever ranking, but still keep the answer narrow.
    results = bm25_retriever.invoke(query)
    if results:
        for doc in results[:3]:
            if normalized_query in _normalize(doc.page_content):
                return doc.page_content
        return results[0].page_content

    return "No matching guest information found."


guest_info_tool = Tool(
    name="guest_info_retriever",
    func=extract_text,
    description="Retrieves the most relevant gala guest information for a specific person or relationship query."
)
