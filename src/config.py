"""Centralized configuration from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
ZENDESK_BASE = os.getenv("ZENDESK_SUBDOMAIN", "support.optisigns.com")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
ARTICLES_DIR = os.getenv("ARTICLES_DIR", "./data/articles")
STATE_FILE = os.getenv("STATE_FILE", "./data/state.json")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
