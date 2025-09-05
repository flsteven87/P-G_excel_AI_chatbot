"""
FastAPI dependencies for authentication, authorization, and common functionality.
"""
import logging

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.database import get_supabase_client
from ..core.security import security_manager
from ..models.user import User

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from JWT token."""
    try:
        # Verify token
        token_data = security_manager.verify_token(credentials.credentials)

        # Get user from database
        client = await get_supabase_client()
        response = client.table("users")\
            .select("*")\
            .eq("id", token_data["sub"])\
            .single()\
            .execute()

        if response.error or not response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user = User(**response.data)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_optional_user(
    authorization: str | None = Header(None)
) -> User | None:
    """Get current user if authenticated, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        credentials = HTTPAuthorizationCredentials(scheme="bearer", credentials=token)
        return await get_current_user(credentials)
    except Exception:
        return None


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user has admin privileges."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


class PaginationParams:
    """Common pagination parameters."""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


def get_pagination() -> PaginationParams:
    """Get pagination parameters dependency."""
    return Depends(PaginationParams)


async def validate_dataset_access(
    dataset_id: str,
    current_user: User = Depends(get_current_user)
) -> str:
    """Validate user has access to dataset."""
    try:
        client = await get_supabase_client()

        response = client.table("datasets")\
            .select("user_id")\
            .eq("id", dataset_id)\
            .single()\
            .execute()

        if response.error or not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        if response.data["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this dataset"
            )

        return dataset_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset access validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate dataset access"
        ) from e


async def validate_session_access(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> str:
    """Validate user has access to chat session."""
    try:
        client = await get_supabase_client()

        response = client.table("chat_sessions")\
            .select("user_id")\
            .eq("id", session_id)\
            .eq("is_active", True)\
            .single()\
            .execute()

        if response.error or not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

        if response.data["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )

        return session_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session access validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate session access"
        ) from e


class RateLimiter:
    """Simple rate limiting (in production, use Redis-based solution)."""
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}  # In production, use Redis

    async def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        # This is a simplified implementation
        # In production, use Redis with sliding window
        import time

        now = time.time()
        window_start = now - self.window_seconds

        if user_id not in self._requests:
            self._requests[user_id] = []

        # Clean old requests
        self._requests[user_id] = [
            req_time for req_time in self._requests[user_id]
            if req_time > window_start
        ]

        # Check limit
        if len(self._requests[user_id]) >= self.max_requests:
            return False

        # Record current request
        self._requests[user_id].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(current_user: User = Depends(get_current_user)):
    """Rate limiting dependency."""
    if not await rate_limiter.check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
