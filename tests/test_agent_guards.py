from app import _guard_missing_fact


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
