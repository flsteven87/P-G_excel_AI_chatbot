"""
Pydantic models for chat functionality.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class QueryStatus(str, Enum):
    """Status of query execution."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatMessage(BaseModel):
    """Chat message model."""
    id: str = Field(..., description="Unique message identifier")
    user_id: str = Field(..., description="User identifier")
    content: str = Field(..., description="Message content")
    message_type: MessageType = Field(..., description="Type of message")
    sql_query: str | None = Field(None, description="Generated SQL query")
    query_results: dict[str, Any] | None = Field(None, description="Query execution results")
    query_status: QueryStatus | None = Field(None, description="Status of query execution")
    error_message: str | None = Field(None, description="Error message if query failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    dataset_id: str | None = Field(None, description="Associated dataset ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message."""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    dataset_id: str | None = Field(None, description="Associated dataset ID")
    context: str | None = Field(None, description="Additional context for the query")


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    message: ChatMessage
    suggestions: list[str] | None = Field(None, description="Suggested follow-up questions")


class QueryRequest(BaseModel):
    """Schema for query execution requests."""
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")
    dataset_id: str = Field(..., description="Dataset to query against")
    context: str | None = Field(None, description="Additional context")
    user_id: str = Field(..., description="User making the request")


class QueryResponse(BaseModel):
    """Schema for query execution response."""
    sql_query: str = Field(..., description="Generated SQL query")
    results: dict[str, Any] = Field(..., description="Query execution results")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
    row_count: int = Field(..., description="Number of rows returned")
    columns: list[str] = Field(..., description="Column names in results")
    chart_suggestions: list[dict[str, Any]] | None = Field(
        None, description="Suggested chart visualizations"
    )


class ChatSession(BaseModel):
    """Chat session model."""
    id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    title: str = Field(..., description="Session title")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Whether session is active")
    message_count: int = Field(0, description="Number of messages in session")


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session."""
    title: str | None = Field("New Chat", description="Session title")


class QueryFeedback(BaseModel):
    """User feedback on query results."""
    message_id: str = Field(..., description="Message ID being rated")
    user_id: str = Field(..., description="User providing feedback")
    is_helpful: bool = Field(..., description="Whether the response was helpful")
    corrected_sql: str | None = Field(None, description="User-corrected SQL query")
    feedback_text: str | None = Field(None, description="Additional feedback text")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WebSocketMessage(BaseModel):
    """WebSocket message schema."""
    type: str = Field(..., description="Message type")
    payload: dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
