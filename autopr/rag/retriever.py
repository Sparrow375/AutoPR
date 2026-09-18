"""
AutoPR RAG Pipeline — Codebase Retriever

Performs semantic and hybrid retrieval over indexed repository snippets in ChromaDB,
ranking results by relevance and formatting them with exact file paths and line ranges.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from autopr.config.settings import get_settings
from autopr.rag.indexer import get_indexer

logger = logging.getLogger("autopr.rag.retriever")


class ContextSnippet(BaseModel):
    """Represents a retrieved code or documentation snippet."""

    file_path: str
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: int
    content: str
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


class CodebaseRetriever:
    """Retrieves relevant code context from ChromaDB for agent tasks."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.indexer = get_indexer()

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        file_filter: str | None = None,
    ) -> list[ContextSnippet]:
        """Retrieve most relevant code and documentation snippets for a query.

        Args:
            query: Natural language or code keyword query.
            top_k: Number of snippets to return (defaults to settings.rag_top_k).
            file_filter: Optional substring filter on file_path.

        Returns:
            List of ranked ContextSnippet objects.
        """
        k = top_k or self.settings.rag_top_k
        coll = self.indexer.collection

        if coll.count() == 0:
            logger.info("ChromaDB collection empty. Running automatic indexing first...")
            self.indexer.index_workspace()

        if coll.count() == 0:
            logger.warning("No documents found in index after indexing attempt")
            return []

        actual_k = min(k, coll.count())

        try:
            results = coll.query(
                query_texts=[query],
                n_results=actual_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error("ChromaDB query execution error: %s", e)
            return []

        snippets: list[ContextSnippet] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances, strict=False):
            meta_dict = meta or {}
            file_path = str(meta_dict.get("file_path", "unknown"))

            if file_filter and file_filter not in file_path:
                continue

            # Convert cosine distance to 0..1 similarity score
            similarity = max(0.0, min(1.0, 1.0 - (dist if dist is not None else 0.0)))

            snippets.append(
                ContextSnippet(
                    file_path=file_path,
                    symbol_name=str(meta_dict.get("symbol_name", file_path)),
                    symbol_type=str(meta_dict.get("symbol_type", "snippet")),
                    start_line=int(meta_dict.get("start_line", 1)),
                    end_line=int(meta_dict.get("end_line", 1)),
                    content=doc,
                    relevance_score=round(similarity, 3),
                )
            )

        return snippets

    @staticmethod
    def format_for_prompt(snippets: list[ContextSnippet]) -> str:
        """Format retrieved snippets into a clear markdown prompt section for LLMs.

        Args:
            snippets: List of ContextSnippet objects.

        Returns:
            Structured markdown text with clickable-style header paths.
        """
        if not snippets:
            return "No relevant codebase context snippets found."

        parts: list[str] = ["## Relevant Codebase Context (from RAG):\n"]
        for i, s in enumerate(snippets, start=1):
            parts.append(
                f"### Context [{i}] — `{s.file_path}` (Lines {s.start_line}-{s.end_line}) | Symbol: `{s.symbol_name}` ({s.symbol_type}) [Score: {s.relevance_score}]\n"
                f"```\n{s.content}\n```\n"
            )

        return "\n".join(parts)


_GLOBAL_RETRIEVER: CodebaseRetriever | None = None


def get_retriever() -> CodebaseRetriever:
    """Get or initialize singleton CodebaseRetriever."""
    global _GLOBAL_RETRIEVER
    if _GLOBAL_RETRIEVER is None:
        _GLOBAL_RETRIEVER = CodebaseRetriever()
    return _GLOBAL_RETRIEVER


def retrieve_context(query: str, top_k: int = 5) -> str:
    """Convenience tool function for ADK agents to retrieve formatted context."""
    retriever = get_retriever()
    snippets = retriever.retrieve(query=query, top_k=top_k)
    return retriever.format_for_prompt(snippets)
