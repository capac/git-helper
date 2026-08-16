"""
monitor.py
----------
Logs every query, its retrieved documents, and user feedback to PostgreSQL.
All functions are safe to call from Streamlit (no global connection held open).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

import psycopg2
from psycopg2.extras import RealDictCursor

if TYPE_CHECKING:
    from rag_helper import SearchResult


# Connection
def _get_conn():
    return psycopg2.connect(os.environ["POSTGRES_URL"])


@contextmanager
def _cursor():
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
            conn.commit()
    finally:
        conn.close()


# Write
def log_query(
    question: str,
    answer: str,
    results: list[SearchResult],
    response_time_ms: int,
    tool_calls_count: int = 0,
) -> int:
    """
    Persist a completed query and its retrieved docs.
    Returns the new query_id (stored in st.session_state for feedback linking).
    """
    with _cursor() as cur:
        cur.execute(
            """
            INSERT INTO queries (question, answer, response_time_ms, tool_calls_count)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (question, answer, response_time_ms, tool_calls_count),
        )
        query_id: int = cur.fetchone()["id"]

        for rank, r in enumerate(results, start=1):
            cur.execute(
                """
                INSERT INTO retrieved_docs
                    (query_id, rank, doc_id, score, chapter, section, doc_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (query_id, rank, r.doc_id, round(r.score, 4),
                 r.chapter, r.section, r.doc_type),
            )
    return query_id


def log_feedback(query_id: int, rating: int) -> None:
    """
    Record thumbs-up (rating=1) or thumbs-down (rating=-1).
    Uses ON CONFLICT to allow changing your mind within the same session.
    """
    with _cursor() as cur:
        cur.execute(
            """
            INSERT INTO feedback (query_id, rating)
            VALUES (%s, %s)
            ON CONFLICT (query_id) DO UPDATE SET rating = EXCLUDED.rating, ts = NOW()
            """,
            (query_id, rating),
        )


# Read (for optional in-app metrics panel)
def get_recent_metrics(days: int = 7) -> dict:
    """
    Returns hit_rate and mrr for the last `days` days.
    Used by the optional sidebar metrics panel in the Streamlit app.
    """
    with _cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_queries,
                COUNT(f.query_id) AS feedback_count,
                ROUND(
                    AVG(CASE WHEN f.rating = 1 THEN 1.0 ELSE 0.0 END)::NUMERIC, 3
                ) AS hit_rate,
                ROUND(
                    AVG(CASE WHEN f.rating = 1 THEN 1.0 ELSE 0.0 END)::NUMERIC, 3
                ) AS mrr,
                ROUND(AVG(q.response_time_ms)::NUMERIC, 0) AS avg_latency_ms
            FROM queries q
            LEFT JOIN feedback f ON f.query_id = q.id
            WHERE q.ts >= NOW() - INTERVAL '%s days'
            """,
            (days,),
        )
        row = cur.fetchone()
    return dict(row) if row else {}
