"""ChromaDB vector store manager — chunking, upsert, and retrieval."""

import logging
import os
import re

import chromadb
from chromadb.utils import embedding_functions

from src.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


def get_chroma_client():
    """Get persistent ChromaDB client."""
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def get_embedding_function():
    """Get sentence-transformers embedding function for ChromaDB."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )


def get_collection(client=None):
    """Get or create the articles collection with cosine similarity."""
    if client is None:
        client = get_chroma_client()
    return client.get_or_create_collection(
        name="optisigns_articles",
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def chunk_article(
    content: str,
    article_id: str,
    article_url: str,
    article_title: str,
    max_chunk: int = 1000,
    overlap: int = 100,
) -> list[dict]:
    """Split article content into chunks with metadata.

    Chunking strategy:
    1. Remove YAML frontmatter
    2. Split by ## headings (section-level)
    3. If section > max_chunk chars, split by paragraphs with overlap
    4. Each chunk gets article_id, url, title metadata for citations
    5. Skip trivially small chunks (<20 chars)
    """
    # Remove frontmatter
    content = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)

    # Split by headings (## or #)
    sections = re.split(r"\n(?=##?\s)", content)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= max_chunk:
            chunks.append(section)
        else:
            # Split long sections by paragraphs
            paragraphs = section.split("\n\n")
            current = ""
            for para in paragraphs:
                if len(current) + len(para) > max_chunk and current:
                    chunks.append(current.strip())
                    # Keep overlap from end of previous chunk
                    current = current[-overlap:] + "\n\n" + para
                else:
                    current = (current + "\n\n" + para) if current else para
            if current.strip():
                chunks.append(current.strip())

    # Build chunk dicts with metadata
    return [
        {
            "id": f"{article_id}_chunk_{i}",
            "document": chunk,
            "metadata": {
                "article_id": article_id,
                "article_url": article_url,
                "article_title": article_title,
                "chunk_index": i,
            },
        }
        for i, chunk in enumerate(chunks)
        if len(chunk) > 20  # skip trivially small chunks
    ]


def upsert_articles(
    articles_dir: str, article_ids: list[str] | None = None
) -> dict:
    """Load markdown files and upsert chunks into ChromaDB.

    If article_ids is provided, only process those articles (delta upload).
    Returns stats dict: {files_processed, chunks_upserted}.
    """
    collection = get_collection()
    total_chunks = 0
    files_processed = 0

    for filename in sorted(os.listdir(articles_dir)):
        if not filename.endswith(".md"):
            continue

        # Extract article_id from filename (format: {id}-{slug}.md)
        file_article_id = filename.split("-", 1)[0]

        if article_ids is not None and file_article_id not in article_ids:
            continue

        filepath = os.path.join(articles_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract URL and title from frontmatter
        url_match = re.search(r'url:\s*"(.+?)"', content)
        title_match = re.search(r'title:\s*"(.+?)"', content)
        article_url = url_match.group(1) if url_match else ""
        article_title = title_match.group(1) if title_match else ""

        # Remove old chunks for this article before re-inserting
        try:
            existing = collection.get(
                where={"article_id": file_article_id}
            )
            if existing and existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass  # Collection might be empty on first run

        chunks = chunk_article(
            content, file_article_id, article_url, article_title
        )

        if chunks:
            collection.add(
                ids=[c["id"] for c in chunks],
                documents=[c["document"] for c in chunks],
                metadatas=[c["metadata"] for c in chunks],
            )
            total_chunks += len(chunks)

        files_processed += 1

    logger.info(
        f"Processed {files_processed} files → {total_chunks} chunks upserted"
    )
    return {"files_processed": files_processed, "chunks_upserted": total_chunks}


def delete_articles(article_ids: list[str]) -> dict:
    """Remove chunks for deleted/unpublished articles from ChromaDB.

    Returns stats dict: {articles_removed, chunks_deleted}.
    """
    if not article_ids:
        return {"articles_removed": 0, "chunks_deleted": 0}

    collection = get_collection()
    total_chunks = 0
    articles_removed = 0

    for article_id in article_ids:
        try:
            existing = collection.get(where={"article_id": article_id})
            if existing and existing["ids"]:
                collection.delete(ids=existing["ids"])
                total_chunks += len(existing["ids"])
                articles_removed += 1
        except Exception:
            pass

    logger.info(
        f"Removed {articles_removed} articles → {total_chunks} chunks deleted"
    )
    return {"articles_removed": articles_removed, "chunks_deleted": total_chunks}


def query(question: str, n_results: int = 5) -> list[dict]:
    """Query the vector store for relevant article chunks.

    Returns list of dicts with keys: document, metadata, distance.
    """
    collection = get_collection()
    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append(
            {
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    return hits
