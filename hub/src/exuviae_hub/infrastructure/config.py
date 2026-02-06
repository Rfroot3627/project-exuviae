from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATA_ROOT: str = "data"
    SNAPSHOT_SUBDIR: str = "snapshots"
    LOG_SUBDIR: str = "logs"
    VISION_LOG_FILENAME: str = "vision.jsonl"

    class Config:
        env_prefix = "EXUVIAE_"

settings = Settings()
