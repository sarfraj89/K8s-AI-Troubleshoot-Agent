from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BACKEND_URL: str
    CLUSTER_ID: str
    AGENT_TOKEN: str
    AGENT_VERSION: str = "0.1.0"
    POLL_INTERVAL_SECONDS: int = 8


settings = Settings()
