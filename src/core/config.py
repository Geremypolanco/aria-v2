from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    # Auth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    JWT_SECRET: str = "change-me-in-production"

    # AI — Core
    ANTHROPIC_API_KEY: str = ""

    # AI — Fast reasoning
    GROQ_API_KEY: str = ""

    # AI — Image generation
    FAL_API_KEY: str = ""           # fal.ai — FLUX (primary)
    STABILITY_API_KEY: str = ""     # Stability AI (fallback)

    # AI — Video generation
    REPLICATE_API_KEY: str = ""     # Replicate (minimax/video-01)

    # AI — Audio / TTS
    ELEVENLABS_API_KEY: str = ""    # ElevenLabs (primary)
    OPENAI_API_KEY: str = ""        # OpenAI TTS (fallback)

    # AI — Models & inference
    HUGGINGFACE_API_KEY: str = ""   # HuggingFace Hub + Inference

    # Web search
    BRAVE_API_KEY: str = ""         # Brave Search API

    # Commerce
    STRIPE_SECRET_KEY: str = ""
    GUMROAD_ACCESS_TOKEN: str = ""
    SHOPIFY_SHOP_URL: str = "voidline-38.myshopify.com"
    SHOPIFY_ACCESS_TOKEN: str = ""
    TELEGRAM_BOT_TOKEN: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
