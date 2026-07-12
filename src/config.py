import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    opencode_api_key: str = os.getenv("OPENCODE_API_KEY", "")
    opencode_api_base: str = os.getenv("OPENCODE_API_BASE", "https://opencode.ai/zen/v1")
    opencode_model: str = os.getenv("OPENCODE_MODEL", "north-mini-code-free")

    twitter_handle: str = os.getenv("TWITTER_HANDLE", "")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    instagram_username: str = os.getenv("INSTAGRAM_USERNAME", "")
    instagram_password: str = os.getenv("INSTAGRAM_PASSWORD", "")

    data_dir: str = os.getenv("DATA_DIR", "data")


settings = Settings()
