import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_AUTH_HEADER = os.getenv("OPENAI_AUTH_HEADER", "")
OPENAI_CUSTOM_HEADERS = os.getenv("OPENAI_CUSTOM_HEADERS", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "novel2scenario.db")
AGENT_CONCURRENCY = int(os.getenv("AGENT_CONCURRENCY", "5"))
