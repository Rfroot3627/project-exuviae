from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATA_ROOT: str = "data"
    SNAPSHOT_SUBDIR: str = "snapshots"

    class Config:
        env_prefix = "EXUVIAE_"

settings = Settings()
