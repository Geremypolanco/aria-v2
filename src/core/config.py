from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    # Auth
    GOOGLE_CLIENT_ID: str = "475046725598-vm3b12e17kfarcs4@jucei7rrk32kruu.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = ""
    JWT_SECRET: str = "change-me-in-production"

    # AI
    ANTHROPIC_API_KEY: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # External tools (optional — Aria uses them when available)
    STRIPE_SECRET_KEY: str = ""
    GUMROAD_ACCESS_TOKEN: str = ""
    GROQ_API_KEY: str = ""
    HUGGINGFACE_TOKEN: str = ""
    NEWS_API_KEY: str = ""
    SERP_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    BUFFER_TOKEN: str = ""
    DID_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    CLOUDINARY_URL: str = ""
    AIRTABLE_ACCESS_TOKEN: str = ""
    MAILCHIMP_API_KEY: str = ""
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""
    FLY_IO_TOKEN: str = ""
    SHOPIFY_SHOP_URL: str = "voidline-38.myshopify.com"
    SHOPIFY_ACCESS_TOKEN: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
