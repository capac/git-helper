"""
rag_helper.py
-------------
Retrieval layer for the Git Helper app.

Responsibilities:
  - Connect to Qdrant (cloud or local)
  - Embed a user query with the same model used at ingest time
  - Run dense vector search (+ optional keyword pre-filter)
  - Return ranked SearchResult objects ready for the agent to use

Intentionally kept framework-free so it can be used from the
Streamlit app, from evaluation scripts, or from a notebook.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, ScoredPoint
    )


# ── Constants ────────────────────────────────────────────────────────────────

COLLECTION = "progit"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
DEFAULT_TOP_K = 5

# git commands whose effects are hard or impossible to reverse
DESTRUCTIVE_COMMANDS = {
    "reset --hard", "push --force", "push -f",
    "rebase", "filter-branch", "filter-repo",
    "clean -f", "clean -fd", "clean -fx",
    "checkout --", "restore",
    "rm --cached", "commit --amend",
    "reflog expire", "gc --prune",
}


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    doc_id: str
    score: float
    chapter: str
    section: str
    text: str
    doc_type: str  # "prose" | "commands"
    commands: list[str] = field(default_factory=list)
    is_destructive: bool = False

    @classmethod
    def from_scored_point(cls, point: ScoredPoint) -> "SearchResult":
        p = point.payload or {}
        commands = p.get("commands", [])
        return cls(
            doc_id=p.get("doc_id", str(point.id)),
            score=point.score,
            chapter=p.get("chapter_title", ""),
            section=p.get("section_title", ""),
            text=p.get("text", ""),
            doc_type=p.get("type", "prose"),
            commands=commands,
            is_destructive=_any_destructive(commands),
        )

    def as_context_block(self) -> str:
        """Format this result for injection into an LLM prompt."""
        lines = [
            f"[Source: {self.chapter} › {self.section}]",
            self.text,
        ]
        if self.commands:
            lines.append("\nRelevant commands:")
            lines.extend(f"  $ {cmd}" for cmd in self.commands)
        return "\n".join(lines)


def _any_destructive(commands: list[str]) -> bool:
    for cmd in commands:
        normalised = cmd.removeprefix("git ").strip()
        if any(normalised.startswith(d) for d in DESTRUCTIVE_COMMANDS):
            return True
    return False


# ── Core class ───────────────────────────────────────────────────────────────

class GitRAG:
    """
    Thin wrapper around Qdrant + OpenAI embeddings.

    Usage
    -----
    rag = GitRAG.from_env()
    results = rag.search("how do I undo my last commit without losing changes")
    for r in results:
        print(r.as_context_block())
    """

    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: Optional[str],
        openai_client: OpenAI,
        collection: str = COLLECTION,
    ):
        self.qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self.openai = openai_client
        self.collection = collection

    # ── Constructors ────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "GitRAG":
        """Build from environment variables (12-factor style)."""
        return cls(
            qdrant_url=os.environ["QDRANT_URL"],
            qdrant_api_key=os.environ.get("QDRANT_API_KEY"),  # None for local
            openai_client=OpenAI(api_key=os.environ["OPENAI_API_KEY"]),
        )

    # ── Public API ──────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        doc_type: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Dense vector search over the Pro Git corpus.

        Parameters
        ----------
        query    : natural-language question or command fragment
        top_k    : number of results to return
        doc_type : optionally restrict to prose or command chunks
        """
        vector = self._embed(query)
        qdrant_filter = _build_filter(doc_type)

        response = self.qdrant.query_points(
            collection_name = self.collection,
            query = vector,
            limit = top_k,
            query_filter = qdrant_filter,
            with_payload = True,
        )
        return [SearchResult.from_scored_point(p) for p in response.points]


    def search_commands_only(
            self,
            query: str,
            top_k: int = 3
            ) -> list[SearchResult]:
        """Convenience: restrict to command-chunk documents."""
        return self.search(query, top_k=top_k, doc_type="commands")

    def search_prose_only(
            self,
            query: str,
            top_k: int = 3
            ) -> list[SearchResult]:
        """Convenience: restrict to prose-chunk documents."""
        return self.search(query, top_k=top_k, doc_type="prose")

    def build_context(
            self,
            results: list[SearchResult],
            max_chars: int = 6000
            ) -> str:
        """
        Concatenate result context blocks up to a character budget.
        Passed directly into the LLM prompt.
        """
        blocks, total = [], 0
        for r in results:
            block = r.as_context_block()
            if total + len(block) > max_chars:
                break
            blocks.append(block)
            total += len(block)
        return "\n\n---\n\n".join(blocks)

    # ── Internal ────────────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        text = text.replace("\n", " ").strip()
        resp = self.openai.embeddings.create(input=[text], model=EMBED_MODEL)
        return resp.data[0].embedding


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_filter(doc_type: Optional[str]) -> Optional[Filter]:
    if doc_type is None:
        return None
    return Filter(
        must=[FieldCondition(key="type", match=MatchValue(value=doc_type))]
    )
