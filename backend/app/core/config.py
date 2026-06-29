from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Google Gemini (primary LLM provider)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    # OpenRouter fields kept optional for backward-compatible .env files (unused)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "google/gemma-3-27b-it:free"
    KUBECONFIG_PATH: Optional[str] = None
    KUBECONFIG: Optional[str] = None
    INSFORGE_URL: Optional[str] = None
    INSFORGE_API_KEY: Optional[str] = None
    INSFORGE_ANON_KEY: Optional[str] = None

    @property
    def kubeconfig(self) -> Optional[str]:
        """Resolved kubeconfig path (KUBECONFIG env or KUBECONFIG_PATH)."""
        return self.KUBECONFIG or self.KUBECONFIG_PATH

    class Config:
        env_file = ".env"

settings = Settings()
