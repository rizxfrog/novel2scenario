import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DATABASE_PATH = os.getenv("DATABASE_PATH", "novel2scenario.db")
AGENT_CONCURRENCY = int(os.getenv("AGENT_CONCURRENCY", "5"))
