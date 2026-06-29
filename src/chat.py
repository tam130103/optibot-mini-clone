"""DeepSeek-powered RAG chat with ChromaDB retrieval."""

import logging

from openai import OpenAI

from src.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from src.vector_store import query as vector_query

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
"""


def get_client() -> OpenAI:
    """Get DeepSeek client (OpenAI-compatible SDK)."""
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )


def build_context(
    question: str, n_results: int = 5
) -> tuple[str, list[str]]:
    """Retrieve relevant chunks from ChromaDB and format as context.

    Returns (context_text, list_of_unique_article_urls).
    """
    hits = vector_query(question, n_results=n_results)

    context_parts = []
    urls = []
    seen_urls = set()

    for hit in hits:
        meta = hit["metadata"]
        url = meta.get("article_url", "")
        title = meta.get("article_title", "")

        context_parts.append(
            f"[Article: {title}]\n"
            f"[URL: {url}]\n"
            f"{hit['document']}\n"
        )

        if url and url not in seen_urls:
            seen_urls.add(url)
            urls.append(url)

    return "\n---\n".join(context_parts), urls[:3]


def ask(
    question: str, conversation_history: list[dict] | None = None
) -> str:
    """Ask a question with RAG context from ChromaDB + DeepSeek.

    Retrieves relevant chunks, builds a prompt with context, and sends
    to DeepSeek for answer generation. Appends article URLs if the model
    doesn't include them.
    """
    client = get_client()
    context, urls = build_context(question)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"CONTEXT from knowledge base:\n\n{context}\n\n"
                "Use ONLY these chunks to answer. If the answer isn't in "
                "the context, say 'I don't have enough information to "
                "answer that question.'"
            ),
        },
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content

    # Append article URLs if not already cited in the answer
    if urls and "Article URL:" not in answer:
        url_lines = "\n".join(f"Article URL: {u}" for u in urls)
        answer += f"\n\n{url_lines}"

    return answer
