"""
AutoPR RAG Pipeline — Codebase Indexer

Scans workspace files, performs AST-aware chunking on Python modules and semantic
chunking on documentation/config files, computes embeddings via Google GenAI,
and persists them in an in-memory or on-disk ChromaDB collection.
"""

from __future__ import annotations

import ast
import logging
import os
from pathlib import Path
from typing import Any

import chromadb
from google import genai

from autopr.config.settings import get_settings

logger = logging.getLogger("autopr.rag.indexer")

COLLECTION_NAME = "autopr_knowledge"

# File extensions to index
SUPPORTED_EXTENSIONS = {".py", ".md", ".json", ".toml", ".ts", ".tsx", ".yaml", ".yml"}

# Directories to exclude from indexing
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".chroma",
    "build",
    "dist",
    ".pytest_cache",
    ".ruff_cache",
}


def _get_workspace_root() -> Path:
    return Path(os.getcwd()).resolve()


def _extract_python_chunks(file_path: Path, relative_path: str) -> list[dict[str, Any]]:
    """Extract AST-aware function, class, and module chunks from Python files."""
    chunks: list[dict[str, Any]] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        tree = ast.parse(content, filename=str(file_path))
    except Exception as e:
        logger.debug("AST parsing failed for %s: %s, falling back to line chunking", relative_path, e)
        return _extract_generic_chunks(file_path, relative_path)

    # 1. Module-level docstring/header
    module_doc = ast.get_docstring(tree) or ""
    if module_doc:
        chunks.append({
            "id": f"{relative_path}:module_doc",
            "text": f"Module {relative_path} overview:\n{module_doc}",
            "file_path": relative_path,
            "symbol_name": relative_path,
            "symbol_type": "module_doc",
            "start_line": 1,
            "end_line": min(len(lines), 30),
        })

    # 2. Iterate AST top-level definitions
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            start = node.lineno
            end = node.end_lineno or start
            chunk_code = "\n".join(lines[start - 1 : end])
            class_doc = ast.get_docstring(node) or ""
            chunks.append({
                "id": f"{relative_path}:{node.name}:class",
                "text": f"File {relative_path} Class {node.name}\nDocstring: {class_doc}\nCode:\n{chunk_code[:2500]}",
                "file_path": relative_path,
                "symbol_name": node.name,
                "symbol_type": "class",
                "start_line": start,
                "end_line": end,
            })
            # Also extract individual methods if class is large
            if end - start > 40:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_start = item.lineno
                        m_end = item.end_lineno or m_start
                        m_code = "\n".join(lines[m_start - 1 : m_end])
                        chunks.append({
                            "id": f"{relative_path}:{node.name}.{item.name}:method",
                            "text": f"File {relative_path} Method {node.name}.{item.name}\nCode:\n{m_code[:2000]}",
                            "file_path": relative_path,
                            "symbol_name": f"{node.name}.{item.name}",
                            "symbol_type": "method",
                            "start_line": m_start,
                            "end_line": m_end,
                        })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno or start
            chunk_code = "\n".join(lines[start - 1 : end])
            fn_doc = ast.get_docstring(node) or ""
            chunks.append({
                "id": f"{relative_path}:{node.name}:function",
                "text": f"File {relative_path} Function {node.name}\nDocstring: {fn_doc}\nCode:\n{chunk_code[:2500]}",
                "file_path": relative_path,
                "symbol_name": node.name,
                "symbol_type": "function",
                "start_line": start,
                "end_line": end,
            })

    if not chunks:
        return _extract_generic_chunks(file_path, relative_path)

    return chunks


def _extract_generic_chunks(file_path: Path, relative_path: str, chunk_lines: int = 50) -> list[dict[str, Any]]:
    """Extract sliding window line chunks for non-python or unparseable files."""
    chunks: list[dict[str, Any]] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    lines = content.splitlines()
    if not lines:
        return []

    total_lines = len(lines)
    step = max(20, chunk_lines - 10)

    for i in range(0, total_lines, step):
        start = i + 1
        end = min(total_lines, i + chunk_lines)
        chunk_text = "\n".join(lines[i:end])
        chunks.append({
            "id": f"{relative_path}:lines_{start}_{end}",
            "text": f"File {relative_path} (Lines {start}-{end}):\n{chunk_text}",
            "file_path": relative_path,
            "symbol_name": f"{relative_path} ({start}-{end})",
            "symbol_type": "document_chunk",
            "start_line": start,
            "end_line": end,
        })
        if end >= total_lines:
            break

    return chunks


class GeminiEmbeddingFunction(chromadb.EmbeddingFunction[chromadb.Documents]):
    """Chroma-compatible embedding function wrapping Google GenAI."""

    def __init__(self, api_key: str, model: str) -> None:
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model = model

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        if not self.client:
            raise ValueError("Gemini API key not configured for embeddings")
        embeddings: list[list[float]] = []
        batch_size = 20
        doc_list = list(input)
        for i in range(0, len(doc_list), batch_size):
            batch = doc_list[i : i + batch_size]
            res = self.client.models.embed_content(
                model=self.model,
                contents=batch,
            )
            for emb in res.embeddings:
                embeddings.append(emb.values)
        return embeddings


class CodebaseIndexer:
    """Indexes workspace code and documentation into ChromaDB."""

    def __init__(self, use_gemini_embeddings: bool = False) -> None:
        self.settings = get_settings()
        self.chroma_client = chromadb.Client()  # In-memory fast vector store

        # Use Gemini embeddings only if explicitly requested; default to local ONNX
        # to preserve Gemini API rate limits for agent reasoning loops.
        if use_gemini_embeddings and self.settings.gemini_api_key:
            self.embedding_fn = GeminiEmbeddingFunction(
                api_key=self.settings.gemini_api_key,
                model=self.settings.embedding_model,
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            self.embedding_fn = None
            self.collection = self.chroma_client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

    def index_workspace(self, root_dir: Path | None = None) -> int:
        """Scan workspace and index all supported code and docs into ChromaDB.

        Args:
            root_dir: Workspace root directory (defaults to current directory).

        Returns:
            Total count of indexed chunks.
        """
        root = (root_dir or _get_workspace_root()).resolve()
        logger.info("Starting codebase indexing in %s", root)

        all_chunks: list[dict[str, Any]] = []

        for path in root.rglob("*"):
            if any(exc in path.parts for exc in EXCLUDE_DIRS):
                continue
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            rel_path = str(path.relative_to(root)).replace("\\", "/")
            if path.suffix == ".py":
                chunks = _extract_python_chunks(path, rel_path)
            else:
                chunks = _extract_generic_chunks(path, rel_path)

            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning("No indexable chunks discovered in %s", root)
            return 0

        # Prepare for ChromaDB insertion
        ids = [c["id"] for c in all_chunks]
        documents = [c["text"] for c in all_chunks]
        metadatas = [
            {
                "file_path": c["file_path"],
                "symbol_name": c["symbol_name"],
                "symbol_type": c["symbol_type"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
            }
            for c in all_chunks
        ]

        logger.info("Upserting %d codebase chunks into ChromaDB...", len(all_chunks))
        # Batch upsert in chunks of 50
        batch_size = 50
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=ids[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

        logger.info("Successfully indexed %d chunks into collection '%s'", len(all_chunks), COLLECTION_NAME)
        return len(all_chunks)


_GLOBAL_INDEXER: CodebaseIndexer | None = None


def get_indexer() -> CodebaseIndexer:
    """Get or initialize singleton CodebaseIndexer."""
    global _GLOBAL_INDEXER
    if _GLOBAL_INDEXER is None:
        _GLOBAL_INDEXER = CodebaseIndexer()
    return _GLOBAL_INDEXER
