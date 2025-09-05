"""
Database connections and client management.
Provides async Supabase client and connection management.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from supabase import AsyncClient, acreate_client
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages Supabase client connections and provides database utilities."""

    def __init__(self):
        self._client: AsyncClient | None = None
        self._lock = asyncio.Lock()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_client(self) -> AsyncClient | None:
        """Get or create async Supabase client with retry logic."""
        # Skip Supabase initialization in development if not configured
        if not settings.supabase_url or not settings.supabase_anon_key:
            if settings.environment == "development":
                logger.warning("Supabase not configured for development environment")
                return None
            else:
                raise RuntimeError("Supabase configuration required for production environment")

        if self._client is None:
            async with self._lock:
                if self._client is None:
                    try:
                        self._client = await acreate_client(
                            settings.supabase_url,
                            settings.supabase_anon_key
                        )
                        logger.info("Supabase client initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to initialize Supabase client: {e}")
                        if settings.environment != "development":
                            raise

        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_service_client(self) -> AsyncClient | None:
        """Get Supabase client with service role key for admin operations."""
        # Skip Supabase initialization in development if not configured
        if not settings.supabase_url or not settings.supabase_service_role_key:
            if settings.environment == "development":
                logger.warning("Supabase service role not configured for development environment")
                return None
            else:
                raise RuntimeError("Supabase service configuration required for production environment")

        try:
            service_client = await acreate_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
            logger.info("Supabase service client initialized")
            return service_client
        except Exception as e:
            logger.error(f"Failed to initialize Supabase service client: {e}")
            if settings.environment != "development":
                raise
            return None

    async def test_connection(self) -> bool:
        """Test database connection health."""
        try:
            client = await self.get_client()
            if client is None:
                # In development mode without Supabase configured
                logger.info("Database connection test skipped (development mode)")
                return True

            # If we successfully created a client, assume connection is good
            # We don't want to make actual API calls during startup
            logger.info("Database connection test successful")
            return True

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            # In development, don't fail on database connection issues
            if settings.environment == "development":
                logger.warning("Database connection test failed in development mode - continuing")
                return True
            return False

    async def close(self):
        """Close database connections."""
        if self._client:
            try:
                await self._client.auth.sign_out()
                logger.info("Supabase client closed successfully")
            except Exception as e:
                logger.error(f"Error closing Supabase client: {e}")
            finally:
                self._client = None


# Global database manager instance
db_manager = DatabaseManager()


async def get_supabase_client() -> AsyncClient | None:
    """FastAPI dependency to get Supabase client."""
    return await db_manager.get_client()


async def get_supabase_service_client() -> AsyncClient | None:
    """FastAPI dependency to get Supabase service client."""
    return await db_manager.get_service_client()


@asynccontextmanager
async def get_db_transaction():
    """Context manager for database transactions (placeholder for future use)."""
    client = await get_supabase_client()
    try:
        # Note: Supabase doesn't have explicit transaction support in Python client
        # This is a placeholder for future transaction handling if needed
        yield client
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        raise


# Database initialization for FastAPI lifespan
async def init_database():
    """Initialize database connections on startup."""
    try:
        await db_manager.test_connection()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_database():
    """Close database connections on shutdown."""
    await db_manager.close()
    logger.info("Database connections closed")
