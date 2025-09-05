"""
Chat service for managing conversations, message history, and context.
Integrates vanna.ai and query execution for complete chat functionality.
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status

from ..models.chat import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSession,
    ChatSessionCreate,
    MessageType,
    QueryStatus,
)
from ..repositories.chat_repository import (
    chat_message_repository,
    chat_session_repository,
)
from .query_service import query_service
from .vanna_service import vanna_service

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and message processing."""

    def __init__(self):
        self.max_context_messages = 10
        self.max_message_length = 5000
        self.session_repo = chat_session_repository
        self.message_repo = chat_message_repository

    async def create_chat_session(
        self,
        user_id: UUID,
        session_data: ChatSessionCreate
    ) -> ChatSession:
        """Create a new chat session."""
        try:
            session_dict = {
                "user_id": str(user_id),
                "title": session_data.title or "New Chat",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True,
                "message_count": 0
            }

            session = await self.session_repo.create(session_dict, user_id=user_id)
            logger.info(f"Created chat session {session.id} for user {user_id}")
            return session

        except Exception as e:
            logger.error(f"Chat session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat session"
            ) from e

    async def get_chat_session(self, session_id: str, user_id: UUID) -> ChatSession:
        """Get chat session by ID."""
        try:
            session_uuid = UUID(session_id)
            session = await self.session_repo.get(session_uuid, user_id=user_id)

            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )

            return session

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format"
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get chat session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve chat session"
            ) from e

    async def list_chat_sessions(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> list[ChatSession]:
        """List user's chat sessions."""
        try:
            return await self.session_repo.get_active_sessions(user_id, limit)
        except Exception as e:
            logger.error(f"Failed to list chat sessions: {e}")
            return []

    async def process_user_message(
        self,
        session_id: str,
        user_id: UUID,
        message_data: ChatMessageCreate
    ) -> ChatMessageResponse:
        """Process user message and generate AI response."""
        try:
            # Validate session
            await self.get_chat_session(session_id, user_id)

            # Create user message
            user_message = await self.message_repo.create_message(
                user_id=user_id,
                content=message_data.content,
                message_type=MessageType.USER,
                session_id=session_id,
                dataset_id=message_data.dataset_id
            )

            # Generate AI response
            ai_response = await self._generate_ai_response(
                user_message, user_id, message_data.context
            )

            # Update session timestamp
            await self.session_repo.update_session_timestamp(UUID(session_id))

            # Get suggestions for follow-up questions
            suggestions = await vanna_service.get_suggested_questions()

            return ChatMessageResponse(
                message=ai_response,
                suggestions=suggestions
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            # Create error message
            error_message = await self.message_repo.create_message(
                user_id=user_id,
                content="I encountered an error processing your message. Please try again.",
                message_type=MessageType.ERROR,
                session_id=session_id,
                error_message=str(e)
            )

            return ChatMessageResponse(
                message=error_message,
                suggestions=[]
            )

    async def get_session_messages(
        self,
        session_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[ChatMessage]:
        """Get messages from a chat session."""
        try:
            return await self.message_repo.get_session_messages(
                session_id, user_id, limit, offset
            )
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []

    async def _generate_ai_response(
        self,
        user_message: ChatMessage,
        user_id: UUID,
        additional_context: str | None = None
    ) -> ChatMessage:
        """Generate AI response to user message."""
        try:
            # Get conversation context
            context = await self._build_conversation_context(
                user_message, user_id, additional_context
            )

            # Create processing message
            await self.message_repo.create_message(
                user_id=user_id,
                content="Let me analyze your question...",
                message_type=MessageType.ASSISTANT,
                session_id=user_message.session_id,
                query_status=QueryStatus.PROCESSING,
                dataset_id=user_message.dataset_id
            )

            try:
                # Generate SQL using vanna.ai with context
                full_question = f"{user_message.content}\n\nContext: {context}" if context else user_message.content
                sql_query = await vanna_service.generate_sql(full_question)

                # Execute the query
                query_response = await query_service.execute_query(
                    sql_query=sql_query,
                    user_id=str(user_id),
                    dataset_id=user_message.dataset_id
                )

                # Create successful response message
                success_content = self._format_success_response(query_response)

                return await self.message_repo.create_message(
                    user_id=user_id,
                    content=success_content,
                    message_type=MessageType.ASSISTANT,
                    session_id=user_message.session_id,
                    sql_query=sql_query,
                    query_results=query_response.dict(),
                    query_status=QueryStatus.COMPLETED,
                    dataset_id=user_message.dataset_id
                )

            except Exception as query_error:
                # Update processing message to show error
                error_content = f"I couldn't process your question. {str(query_error)}"

                return await self.message_repo.create_message(
                    user_id=user_id,
                    content=error_content,
                    message_type=MessageType.ASSISTANT,
                    session_id=user_message.session_id,
                    query_status=QueryStatus.FAILED,
                    error_message=str(query_error),
                    dataset_id=user_message.dataset_id
                )

        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            raise

    async def _build_conversation_context(
        self,
        current_message: ChatMessage,
        user_id: UUID,
        additional_context: str | None = None
    ) -> str:
        """Build conversation context from recent messages."""
        try:
            # Get recent messages for context
            recent_messages = await self.message_repo.get_recent_context_messages(
                user_id, self.max_context_messages
            )

            context_parts = []

            if additional_context:
                context_parts.append(f"Additional context: {additional_context}")

            if recent_messages:
                context_parts.append("Recent conversation:")
                for msg in reversed(recent_messages[-5:]):  # Last 5 messages
                    role = "User" if msg.message_type == MessageType.USER else "Assistant"
                    content = msg.content[:200]  # Truncate long messages
                    context_parts.append(f"{role}: {content}")

            return "\n".join(context_parts)

        except Exception as e:
            logger.warning(f"Failed to build conversation context: {e}")
            return additional_context or ""

    def _format_success_response(self, query_response) -> str:
        """Format successful query response into natural language."""
        row_count = query_response.row_count
        execution_time = query_response.execution_time_ms

        if row_count == 0:
            return "Your query completed successfully, but no results were found."
        elif row_count == 1:
            return f"I found 1 result for your query (executed in {execution_time:.0f}ms)."
        else:
            return f"I found {row_count} results for your query (executed in {execution_time:.0f}ms)."

    async def delete_session(self, session_id: str, user_id: UUID) -> bool:
        """Soft delete a chat session."""
        try:
            session_uuid = UUID(session_id)
            update_data = {"is_active": False}
            result = await self.session_repo.update(session_uuid, update_data, user_id=user_id)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False


# Global chat service instance
chat_service = ChatService()
