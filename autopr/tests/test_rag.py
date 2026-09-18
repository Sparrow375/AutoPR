"""
Unit tests for AutoPR RAG Pipeline (Indexer, Retriever, Grounding).
"""

from __future__ import annotations

from autopr.rag.grounding import discover_and_load_brd, format_brd_for_prompt
from autopr.rag.indexer import get_indexer
from autopr.rag.retriever import get_retriever


def test_rag_indexer_workspace() -> None:
    indexer = get_indexer()
    count = indexer.index_workspace()
    assert count > 0
    assert indexer.collection.count() > 0


def test_rag_retriever_query() -> None:
    retriever = get_retriever()
    snippets = retriever.retrieve("FastAPI server endpoints", top_k=3)
    assert len(snippets) > 0
    formatted = retriever.format_for_prompt(snippets)
    assert "Relevant Codebase Context" in formatted
    assert snippets[0].relevance_score >= 0.0


def test_brd_grounding_discovery() -> None:
    brd = discover_and_load_brd()
    assert brd is not None
    assert len(brd.requirements) > 0
    formatted = format_brd_for_prompt(brd)
    assert "Active Business Requirement Document" in formatted
