"""
streamlit_app.py
----------------
Git Helper — an agentic RAG chatbot that answers git questions using
the Pro Git book as its knowledge base.

Agent loop
----------
1. User sends a message.
2. We call the LLM with the user message + available tools.
3. If the LLM calls a tool, we run it and feed the result back.
4. We repeat until the LLM stops calling tools and returns a final answer.
5. We display the answer with any retrieved source sections.

Tools exposed to the agent
--------------------------
  search_git_docs      : semantic search over prose + command chunks
  search_git_commands  : semantic search restricted to command chunks only
  clarify_intent       : agent emits a clarifying question (stops the loop)
"""

from __future__ import annotations

import time
from monitor import log_query, log_feedback, get_recent_metrics

import json
import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from rag_helper import GitRAG, SearchResult

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)


# Page config

st.set_page_config(
    page_title="Git Helper",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Terminal-inspired palette: dark background, green accents, monospace code
st.markdown("""
<style>
  /* ── global ── */
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── sidebar ── */
  section[data-testid="stSidebar"] {
      background: #0d1117;
      border-right: 1px solid #21262d;
  }
  section[data-testid="stSidebar"] * { color: #e6edf3 !important; }

  /* ── chat messages ── */
  .stChatMessage { border-radius: 8px; margin-bottom: 0.5rem; }

  /* ── code blocks ── */
  code, pre { font-family: 'JetBrains Mono',
  'Fira Code', monospace !important; }

  /* ── destructive warning badge ── */
  .destructive-badge {
      display: inline-block;
      background: #ff6b6b22;
      color: #ff6b6b;
      border: 1px solid #ff6b6b55;
      border-radius: 4px;
      font-size: 0.75rem;
      padding: 2px 8px;
      margin-bottom: 0.5rem;
  }

  /* ── source pill ── */
  .source-pill {
      display: inline-block;
      background: #161b22;
      color: #8b949e;
      border: 1px solid #21262d;
      border-radius: 12px;
      font-size: 0.72rem;
      padding: 2px 10px;
      margin: 2px 3px 2px 0;
  }
</style>
""", unsafe_allow_html=True)


# Session state

def _init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []       # chat history shown in UI
    if "agent_history" not in st.session_state:
        st.session_state.agent_history = []  # full OpenAI message thread
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []   # SearchResult list from last turn


_init_state()

# Singleton clients

@st.cache_resource
def get_rag() -> GitRAG:
    return GitRAG.from_env()


@st.cache_resource
def get_openai() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


rag = get_rag()
client = get_openai()


# Agent tools

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_git_docs",
            "description": (
                "Search the Pro Git book for sections relevant to the user's "
                "question. Returns prose explanations and any associated shell "
                "commands. Use this for conceptual questions or when you need "
                "both explanation and commands."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language search query.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description":
                        "Number of results to retrieve (default 4).",
                        "default": 4,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_git_commands",
            "description": (
                "Search the Pro Git book restricted to command examples only. "
                "Use this when the user clearly wants the exact shell command "
                "and less prose explanation, e.g. "
                "'how do I cherry-pick a range'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description":
                        "Natural-language or command-fragment query.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description":
                        "Number of results to retrieve (default 3).",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clarify_intent",
            "description": (
                "Ask the user a clarifying question when their request is "
                "ambiguous and the answer would differ significantly "
                "depending on their intent. For example, 'undo' could mean "
                "reset or restore. Call this ONCE at most, then commit "
                "to an answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description":
                        "The clarifying question to ask the user.",
                    },
                },
                "required": ["question"],
            },
        },
    },
]

SYSTEM_PROMPT = """\
You are Git Helper, an expert assistant that helps developers use git
correctly. You answer questions by searching the Pro Git book and then
synthesising a clear, accurate answer.

ANSWER FORMAT — always structure your response like this:

**Command**
```bash
git <command> [options]
```

**What it does**
One or two sentences explaining the effect.

**When to use it**
Brief guidance on the right context.

**Caveats** *(omit if none)*
Warn about destructive operations, history rewriting, or surprising edge cases.

**Safer alternative** *(omit if none)*
Suggest a non-destructive option when relevant.

RULES
- Always call at least one search tool before answering.
Never answer from memory alone.
- If a command rewrites history or is hard to reverse,
say so explicitly in Caveats.
- Prefer modern git syntax (git switch / git restore) over
legacy (git checkout) for new users, but mention both.
- Keep answers focused. Do not pad with unnecessary background.
- If the question is genuinely ambiguous,
call clarify_intent once, then answer.
"""


# Tool execution

def run_tool(
        name: str,
        args: dict[str, Any]
        ) -> tuple[str, list[SearchResult]]:
    """Execute a tool call and return (json_result_string, search_results)."""
    results: list[SearchResult] = []

    if name == "search_git_docs":
        results = rag.search(args["query"], top_k=args.get("top_k", 4))
        payload = [
            {
                "score": round(r.score, 3),
                "chapter": r.chapter,
                "section": r.section,
                "text": r.text[:800],
                "commands": r.commands,
                "destructive": r.is_destructive,
            }
            for r in results
        ]

    elif name == "search_git_commands":
        results = rag.search_commands_only(
            args["query"], top_k=args.get("top_k", 3)
            )
        payload = [
            {
                "score": round(r.score, 3),
                "chapter": r.chapter,
                "section": r.section,
                "commands": r.commands,
                "destructive": r.is_destructive,
            }
            for r in results
        ]

    elif name == "clarify_intent":
        # Return the question as the tool result so the LLM surfaces it
        payload = {"clarification_needed": args["question"]}

    else:
        payload = {"error": f"Unknown tool: {name}"}

    return json.dumps(payload), results


# Agent loop

def run_agent(user_message: str) -> tuple[str, list[SearchResult]]:
    """
    Run the agentic loop for a single user turn.
    Returns (assistant_reply_text, all_search_results_used).
    """
    # Append user message to the thread
    st.session_state.agent_history.append(
        {"role": "user", "content": user_message}
        )

    all_results: list[SearchResult] = []
    max_iterations = 6   # safety cap — prevent infinite loops

    for _ in range(max_iterations):
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *st.session_state.agent_history,
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        # No tool call → final answer
        if not msg.tool_calls:
            reply = msg.content or ""
            st.session_state.agent_history.append(
                {"role": "assistant", "content": reply}
            )
            return reply, all_results

        # Tool calls → execute each, feed results back
        # Add the assistant message with tool_calls to history
        st.session_state.agent_history.append(
            msg.model_dump(exclude_unset=True)
            )

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result_str, results = run_tool(tc.function.name, args)
            all_results.extend(results)

            # Handle clarify_intent specially — surface question immediately
            if tc.function.name == "clarify_intent":
                question = args.get(
                    "question", "Could you clarify your question?"
                    )
                st.session_state.agent_history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })
                # Return the clarifying question as the reply
                return f"❓ {question}", all_results

            st.session_state.agent_history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

    return (
        "I wasn't able to find a confident answer. Please try rephrasing.",
        all_results
        )


# Rendering helpers

def render_sources(results: list[SearchResult]):
    if not results:
        return
    seen = set()
    unique = []
    for r in results:
        key = (r.chapter, r.section)
        if key not in seen:
            seen.add(key)
            unique.append(r)

    with st.expander(f"{len(unique)} source(s) from Pro Git", expanded=False):
        for r in unique:
            st.markdown(
                f'<span class="source-pill">{r.chapter} › {r.section}</span>',
                unsafe_allow_html=True,
            )
            if r.is_destructive:
                st.markdown(
                    '<span class="destructive-badge">'
                    'rewrites history / destructive</span>',
                    unsafe_allow_html=True,
                )
            st.caption(r.text[:300] + ("…" if len(r.text) > 300 else ""))
            st.divider()


def render_chat_history():
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                render_sources(msg["sources"])
            if msg.get("query_id"):
                render_feedback(msg["query_id"], key_suffix=str(i))


@st.fragment
def render_feedback(query_id: int, key_suffix: str):
    col1, col2, _ = st.columns([1, 1, 8])
    with col1:
        if st.button("👍", key=f"up_{key_suffix}"):
            log_feedback(query_id, 1)
            st.toast("Thanks for the feedback!", icon="✅")
    with col2:
        if st.button("👎", key=f"down_{key_suffix}"):
            log_feedback(query_id, -1)
            st.toast("Noted — we'll use this to improve.", icon="📝")

# Sidebar

with st.sidebar:
    st.markdown("## Git Helper")
    st.markdown(
        "Ask anything about git in plain English. "
        "Powered by the [Pro Git book](https://git-scm.com/book/en/v2)."
    )
    st.divider()

    st.markdown("**Quick questions**")
    QUICK_QUESTIONS = [
        "Undo my last commit but keep the changes",
        "Apply a single commit from another branch",
        "See which commits changed a specific file",
        "Squash my last 3 commits into one",
        "Safely delete a remote branch",
        "Find who last changed a line of code",
    ]
    for q in QUICK_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state["_quick_q"] = q

    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent_history = []
        st.session_state.last_sources = []
        st.rerun()

    metrics = get_recent_metrics(days=7)
    if metrics and metrics.get("feedback_count", 0) > 0:
        st.markdown("**Last 7 days**")
        col1, col2 = st.columns(2)
        col1.markdown(
            f"""
            <div style="text-align: center;">
                <div style="font-size: 14px; color: #666;">Hit Rate</div>
                <div style="font-size: 18px; font-weight: 600;">
                    {float(metrics['hit_rate']):.0%}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col2.markdown(
            f"""
            <div style="text-align: center;">
                <div style="font-size: 14px; color: #666;">Average Latency</div>
                <div style="font-size: 18px; font-weight: 600;">
                    {int(metrics['avg_latency_ms'])} ms
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            f"{metrics['total_queries']} queries · "
            f"{metrics['feedback_count']} rated"
            )

    st.markdown(
        "<div style='color:#484f58; font-size:0.7rem; margin-top:1rem;'>"
        "Content sourced from the Pro Git book, CC BY-NC-SA 3.0"
        "</div>",
        unsafe_allow_html=True,
    )


# Main UI

st.title("Git Helper")
st.caption("Ask in plain English — get the right git command, explained.")

render_chat_history()

# Handle quick-question buttons from sidebar
user_input: str | None = None
if "_quick_q" in st.session_state:
    user_input = st.session_state.pop("_quick_q")

chat_input = st.chat_input("e.g. How do I revert a pushed commit?")
if chat_input:
    user_input = chat_input

if user_input:
    # Show the user bubble immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Run the agent with a spinner
    with st.chat_message("assistant"):
        with st.spinner("Searching Pro Git…"):
            try:
                t0 = time.monotonic()
                reply, sources = run_agent(user_input)
                elapsed_ms = int((time.monotonic() - t0) * 1000)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()

        st.markdown(reply)
        render_sources(sources)

        # Count tool calls made this turn
        tool_calls_count = sum(
            1 for m in st.session_state.agent_history
            if isinstance(m, dict) and m.get("role") == "tool"
        )

        query_id = log_query(
            question = user_input,
            answer = reply,
            results = sources,
            response_time_ms = elapsed_ms,
            tool_calls_count = tool_calls_count,
        )

        # Render feedback buttons right now, in this same script run
        render_feedback(query_id, key_suffix="latest")

    st.session_state.messages.append(
        {"role": "assistant", "content": reply,
        "sources": sources, "query_id": query_id}
    )
    st.session_state.last_sources = sources
    st.rerun()
