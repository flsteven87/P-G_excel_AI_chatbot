"""
Chat repository with async Supabase operations.
Handles chat sessions and messages persistence.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ..models.chat import ChatMessage, ChatSession, MessageType, QueryStatus
from .supabase_base import SupabaseRepository

logger = logging.getLogger(__name__)


class ChatSessionRepository(SupabaseRepository):
    """Repository for ChatSession entities with async Supabase client."""

    def __init__(self):
        super().__init__(table_name="chat_sessions", model_class=ChatSession)

    async def get_active_sessions(self, user_id: UUID, limit: int = 20) -> list[ChatSession]:
        """Get active chat sessions for user."""
        try:
            filters = {"is_active": True}
            return await super().get_many(
                filters=filters,
                user_id=user_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Get active sessions failed: {e}")
            return []

    async def update_session_timestamp(self, session_id: UUID) -> bool:
        """Update session's last updated timestamp."""
        try:
            update_data = {"updated_at": datetime.utcnow().isoformat()}
            result = await super().update(session_id, update_data)
            return result is not None
        except Exception as e:
            logger.error(f"Session timestamp update failed: {e}")
            return False


class ChatMessageRepository(SupabaseRepository):
    """Repository for ChatMessage entities with async Supabase client."""

    def __init__(self):
        super().__init__(table_name="chat_messages", model_class=ChatMessage)

    async def get_session_messages(
        self,
        session_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[ChatMessage]:
        """Get messages from a chat session."""
        try:
            filters = {"session_id": session_id}
            return await super().get_many(
                filters=filters,
                user_id=user_id,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Get session messages failed: {e}")
            return []

    async def get_recent_context_messages(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> list[ChatMessage]:
        """Get recent messages for context building."""
        try:
            return await super().get_many(
                user_id=user_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Get context messages failed: {e}")
            return []

    async def create_message(
        self,
        user_id: UUID,
        content: str,
        message_type: MessageType,
        session_id: str | None = None,
        dataset_id: str | None = None,
        sql_query: str | None = None,
        query_results: dict[str, Any] | None = None,
        query_status: QueryStatus | None = None,
        error_message: str | None = None
    ) -> ChatMessage:
        """Create a new chat message."""
        try:
            message_data = {
                "content": content,
                "message_type": message_type.value,
                "created_at": datetime.utcnow().isoformat(),
                "dataset_id": dataset_id,
                "sql_query": sql_query,
                "query_results": query_results,
                "query_status": query_status.value if query_status else None,
                "error_message": error_message,
                "session_id": session_id
            }

            return await super().create(message_data, user_id=user_id)

        except Exception as e:
            logger.error(f"Message creation failed: {e}")
            raise

    async def get_successful_queries(
        self,
        user_id: UUID | None = None,
        limit: int = 100
    ) -> list[ChatMessage]:
        """Get successful queries for training purposes."""
        try:
            filters = {
                "message_type": MessageType.ASSISTANT.value,
                "query_status": QueryStatus.COMPLETED.value
            }

            # Use base class with additional SQL filter for non-null sql_query
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").match(filters)

            if user_id:
                query = query.eq("user_id", str(user_id))

            query = query.not_("sql_query", "is", None).limit(limit)
            result = await query.execute()

            # Use safe result handling
            data = self._handle_supabase_result(result, allow_empty=True)
            return self._build_models(data)

        except Exception as e:
            logger.error(f"Get successful queries failed: {e}")
            return []

    async def update_query_results(
        self,
        message_id: UUID,
        sql_query: str,
        query_results: dict[str, Any],
        query_status: QueryStatus,
        error_message: str | None = None
    ) -> bool:
        """Update message with query execution results."""
        try:
            update_data = {
                "sql_query": sql_query,
                "query_results": query_results,
                "query_status": query_status.value,
                "updated_at": datetime.utcnow().isoformat()
            }

            if error_message:
                update_data["error_message"] = error_message

            result = await super().update(message_id, update_data)
            return result is not None

        except Exception as e:
            logger.error(f"Query results update failed: {e}")
            return False


# Global repository instances
chat_session_repository = ChatSessionRepository()
chat_message_repository = ChatMessageRepository()
