"""
Security utilities for authentication, authorization, and data protection.
"""
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Handles security operations for the application."""

    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.token_expire_minutes = settings.access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise credentials_exception


class SQLSecurityValidator:
    """Validates SQL queries for security threats."""

    def __init__(self):
        self.allowed_operations = settings.allowed_sql_operations
        self.blocked_keywords = settings.blocked_sql_keywords

        # Compile regex patterns for SQL injection detection
        self.injection_patterns = [
            r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)",
            r"UNION\s+SELECT",
            r"--\s*",
            r"/\*.*?\*/",
            r"'.*';\s*(DROP|DELETE|INSERT|UPDATE)",
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.injection_patterns]

    def validate_sql_query(self, query: str) -> bool:
        """
        Validate SQL query for security compliance.
        Returns True if query is safe, raises HTTPException if not.
        """
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty query not allowed"
            )

        query_upper = query.upper().strip()

        # Check if query starts with allowed operations
        starts_with_allowed = any(
            query_upper.startswith(op) for op in self.allowed_operations
        )

        if not starts_with_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Query must start with one of: {', '.join(self.allowed_operations)}"
            )

        # Check for blocked keywords
        for keyword in self.blocked_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Blocked keyword '{keyword}' found in query"
                )

        # Check for SQL injection patterns
        for pattern in self.compiled_patterns:
            if pattern.search(query):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Potentially malicious SQL pattern detected"
                )

        # Ensure LIMIT clause is present
        if "LIMIT" not in query_upper:
            query += f" LIMIT {settings.default_query_limit}"

        return True

    def sanitize_query(self, query: str) -> str:
        """Sanitize and add safety constraints to SQL query."""
        self.validate_sql_query(query)

        query = query.strip()

        # Add LIMIT if not present
        if "LIMIT" not in query.upper():
            query += f" LIMIT {settings.default_query_limit}"

        return query


class DataPrivacyManager:
    """Handles data privacy and PII protection."""

    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    }

    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PII_PATTERNS.items()
        }

    def detect_pii(self, text: str) -> dict[str, list[str]]:
        """Detect PII patterns in text."""
        detected = {}
        for pii_type, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[pii_type] = matches
        return detected

    def mask_pii(self, text: str) -> str:
        """Mask detected PII in text."""
        for pii_type, pattern in self.compiled_patterns.items():
            if pii_type == "email":
                text = pattern.sub("***@***.***", text)
            elif pii_type == "phone":
                text = pattern.sub("***-***-****", text)
            elif pii_type == "ssn":
                text = pattern.sub("***-**-****", text)
            elif pii_type == "credit_card":
                text = pattern.sub("****-****-****-****", text)
        return text

    def generate_user_hash(self, user_id: str) -> str:
        """Generate a hash for user identification."""
        return hashlib.sha256(f"{user_id}{settings.secret_key}".encode()).hexdigest()[:16]


# Authentication dependencies
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current user from JWT token

    For now, returns a mock user. In production, this should:
    1. Verify JWT token
    2. Get user from database
    3. Return user object
    """
    try:
        # Verify token
        payload = security_manager.verify_token(credentials.credentials)

        # For demo purposes, return mock user
        # In production, fetch user from database using payload['sub']
        return {
            "id": payload.get("sub", "demo_user"),
            "email": "demo@example.com",
            "name": "Demo User"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict | None:
    """Get current user but allow None for public endpoints"""
    try:
        return await get_current_user(credentials)
    except Exception:
        return None


# Global security instances
security_manager = SecurityManager()
sql_validator = SQLSecurityValidator()
privacy_manager = DataPrivacyManager()
