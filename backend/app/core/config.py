"""
Configuration settings for the Excel AI Chatbot application.
Uses manual environment variable management to avoid Pydantic Settings issues.
"""

import json
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        """Initialize settings with manual environment variable loading."""
        # Application Info
        self.app_name = "Excel AI Chatbot"
        self.version = "0.1.0"
        self.description = "Chat with your Excel/CSV data using AI"

        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Supabase Configuration - Optional in development
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.database_url = os.getenv("DATABASE_URL")

        # vanna.ai Configuration - Optional in development
        self.vanna_api_key = os.getenv("VANNA_API_KEY")
        self.vanna_model_name = os.getenv("VANNA_MODEL_NAME", "excel-chatbot")

        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Security Settings
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-min-32-chars")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        # Query Safety Limits
        self.statement_timeout_ms = int(os.getenv("STATEMENT_TIMEOUT_MS", "15000"))
        self.default_query_limit = int(os.getenv("DEFAULT_QUERY_LIMIT", "1000"))
        self.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

        # Storage Configuration
        self.storage_bucket = os.getenv("STORAGE_BUCKET", "user-uploads")

        # Redis Configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # CORS Settings - Handle comma-separated or JSON format
        cors_origins_env = os.getenv("CORS_ORIGINS")
        if cors_origins_env:
            try:
                # Try JSON format first
                self.cors_origins = json.loads(cors_origins_env)
            except json.JSONDecodeError:
                # Fall back to comma-separated
                self.cors_origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
        else:
            # Default CORS origins for development
            self.cors_origins = [
                "http://localhost:5173", "http://127.0.0.1:5173",
                "http://localhost:3000", "http://127.0.0.1:3000"
            ]

        # SQL Safety Settings
        self.allowed_sql_operations = ["SELECT", "WITH"]
        self.blocked_sql_keywords = [
            "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
            "TRUNCATE", "REPLACE", "MERGE", "EXEC", "EXECUTE"
        ]


# Global settings instance
settings = Settings()
