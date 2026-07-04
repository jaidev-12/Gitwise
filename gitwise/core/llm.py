"""Talk to the LLM with retrieved context.

Uses Groq's free-tier API (OpenAI-compatible), so no cost to run.
Sign up for a free key at https://console.groq.com
"""
from groq import Groq

from gitwise.config import GROQ_API_KEY, LLM_MODEL

SYSTEM_PROMPT = """You are GitWise, an assistant that explains codebases in plain English.
You are given retrieved code/doc snippets from a specific repository plus a user question.
Answer using ONLY the provided context. Reference specific file names when relevant.
If the context doesn't contain enough information to answer confidently, say so plainly
instead of guessing. Keep answers concise and beginner-friendly unless the question is
clearly from an experienced developer."""


class LLMError(Exception):
    pass


def answer_question(question: str, hits: list[dict]) -> str:
    if not GROQ_API_KEY:
        raise LLMError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
            "then `export GROQ_API_KEY=...` before running `gitwise query`."
        )

    context_blocks = []
    for hit in hits:
        context_blocks.append(f"--- {hit['file_path']} ---\n{hit['text']}")
    context = "\n\n".join(context_blocks) if context_blocks else "(no relevant context found)"

    user_message = f"Context:\n{context}\n\nQuestion:\n{question}"

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()
