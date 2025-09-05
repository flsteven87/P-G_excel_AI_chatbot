"""
Pydantic models for user management and authentication.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles in the system."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class SubscriptionTier(str, Enum):
    """Subscription tiers."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class User(BaseModel):
    """User model."""
    id: str = Field(..., description="User identifier")
    email: EmailStr = Field(..., description="User email address")
    full_name: str | None = Field(None, description="User full name")
    role: UserRole = Field(UserRole.USER, description="User role")
    subscription_tier: SubscriptionTier = Field(SubscriptionTier.FREE, description="Subscription tier")
    is_active: bool = Field(True, description="Whether user account is active")
    is_verified: bool = Field(False, description="Whether email is verified")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: datetime | None = Field(None, description="Last login timestamp")

    # Usage statistics
    total_queries: int = Field(0, description="Total number of queries executed")
    total_datasets: int = Field(0, description="Total number of datasets uploaded")
    storage_used_mb: float = Field(0.0, description="Storage used in MB")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str | None = Field(None, description="User full name")


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    full_name: str | None = Field(None, description="User full name")
    email: EmailStr | None = Field(None, description="User email address")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Response schema for user operations."""
    user: User
    access_token: str | None = Field(None, description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class TokenData(BaseModel):
    """Token payload data."""
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")


class UserSession(BaseModel):
    """User session information."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Session expiration")
    ip_address: str | None = Field(None, description="User IP address")
    user_agent: str | None = Field(None, description="User agent string")
    is_active: bool = Field(True, description="Whether session is active")


class UserPreferences(BaseModel):
    """User preferences and settings."""
    user_id: str = Field(..., description="User identifier")
    theme: str = Field("light", description="UI theme preference")
    language: str = Field("en", description="Language preference")
    timezone: str = Field("UTC", description="Timezone preference")
    email_notifications: bool = Field(True, description="Email notification preference")
    default_query_limit: int = Field(100, description="Default query result limit")
    preferred_chart_types: list[str] = Field(
        default_factory=lambda: ["bar", "line", "pie"],
        description="Preferred chart types"
    )
    auto_save_queries: bool = Field(True, description="Auto-save query history")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserStats(BaseModel):
    """User usage statistics."""
    user_id: str = Field(..., description="User identifier")
    queries_today: int = Field(0, description="Queries executed today")
    queries_this_month: int = Field(0, description="Queries executed this month")
    datasets_count: int = Field(0, description="Total datasets")
    storage_used_mb: float = Field(0.0, description="Storage used in MB")
    last_activity: datetime | None = Field(None, description="Last activity timestamp")

    # Subscription limits
    query_limit_daily: int = Field(100, description="Daily query limit")
    query_limit_monthly: int = Field(1000, description="Monthly query limit")
    storage_limit_mb: float = Field(100.0, description="Storage limit in MB")
    dataset_limit: int = Field(10, description="Maximum number of datasets")


class PasswordReset(BaseModel):
    """Password reset request."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
