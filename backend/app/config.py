import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    opencode_api_key: str = os.getenv("OPENCODE_API_KEY", "")
    opencode_base_url: str = os.getenv("OPENCODE_BASE_URL", "https://api.opencode.zen/v1")
    opencode_model: str = os.getenv("OPENCODE_MODEL", "gpt-4o-mini")
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    db_path: str = os.getenv("DB_PATH", "./data/chat.db")
    max_history: int = int(os.getenv("MAX_HISTORY", "12"))


settings = Settings()
