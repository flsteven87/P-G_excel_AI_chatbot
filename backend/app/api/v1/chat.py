"""
Chat API endpoints for WebSocket and HTTP communication.
"""
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...core.security import security_manager
from ...models.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSession,
    ChatSessionCreate,
    QueryFeedback,
    QueryRequest,
)
from ...models.user import User
from ...services.chat_service import chat_service
from ...services.query_service import query_service
from ...services.vanna_service import vanna_service
from ...services.vanna_training import vanna_training_service
from ..dependencies import check_rate_limit, get_current_user, validate_session_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class VannaAskRequest(BaseModel):
    """Request model for vanna.ai ask endpoint"""
    question: str


class ConnectionManager:
    """WebSocket connection manager for real-time chat."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_sessions: dict[str, str] = {}  # user_id -> session_id mapping

    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        """Accept WebSocket connection and store it."""
        await websocket.accept()
        connection_id = f"{user_id}_{session_id}"
        self.active_connections[connection_id] = websocket
        self.user_sessions[user_id] = session_id
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, user_id: str, session_id: str):
        """Remove WebSocket connection."""
        connection_id = f"{user_id}_{session_id}"
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_message(self, user_id: str, session_id: str, message: dict[str, Any]):
        """Send message to specific user's WebSocket."""
        connection_id = f"{user_id}_{session_id}"
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                # Remove broken connection
                self.disconnect(user_id, session_id)


# Global connection manager
manager = ConnectionManager()


@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session."""
    return await chat_service.create_chat_session(current_user.id, session_data)


@router.get("/sessions", response_model=list[ChatSession])
async def list_chat_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """List user's chat sessions."""
    return await chat_service.list_chat_sessions(current_user.id, limit, skip)


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str = Depends(validate_session_access),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session."""
    return await chat_service.get_chat_session(session_id, current_user.id)


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str = Depends(validate_session_access),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session."""
    success = await chat_service.delete_session(session_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
    return {"message": "Session deleted successfully"}


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    session_id: str = Depends(validate_session_access),
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """Send a message in a chat session."""
    return await chat_service.process_user_message(
        session_id, current_user.id, message_data
    )


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str = Depends(validate_session_access),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get messages from a chat session."""
    messages = await chat_service.get_session_messages(
        session_id, current_user.id, limit, skip
    )
    return {"messages": messages}


@router.post("/feedback")
async def submit_feedback(
    feedback: QueryFeedback,
    current_user: User = Depends(get_current_user)
):
    """Submit feedback on query results."""
    feedback.user_id = current_user.id
    success = await vanna_service.process_feedback(feedback)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process feedback"
        )

    return {"message": "Feedback submitted successfully"}


@router.post("/query/direct")
async def execute_direct_query(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """Execute a direct SQL query without chat context."""
    query_request.user_id = current_user.id

    try:
        # Generate SQL using vanna.ai
        sql_query = await vanna_service.generate_sql(query_request.question)

        # Execute query
        result = await query_service.execute_query(
            sql_query=sql_query,
            user_id=current_user.id,
            dataset_id=query_request.dataset_id
        )

        return result

    except Exception as e:
        logger.error(f"Direct query execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    token: str  # Pass token as query parameter
):
    """WebSocket endpoint for real-time chat."""
    try:
        # Verify token (simplified - in production, use proper token validation)
        token_data = security_manager.verify_token(token)
        user_id = token_data["sub"]

        # Validate session access
        await chat_service.get_chat_session(session_id, user_id)

        # Connect WebSocket
        await manager.connect(websocket, user_id, session_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Process different message types
                if message_data.get("type") == "chat_message":
                    # Handle chat message
                    await handle_websocket_chat_message(
                        websocket, session_id, user_id, message_data
                    )
                elif message_data.get("type") == "typing":
                    # Handle typing indicator (could broadcast to other users)
                    pass
                elif message_data.get("type") == "ping":
                    # Handle ping/pong for connection health
                    await websocket.send_text(json.dumps({"type": "pong"}))

        except WebSocketDisconnect:
            manager.disconnect(user_id, session_id)
            logger.info(f"WebSocket disconnected: {user_id}_{session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)


async def handle_websocket_chat_message(
    websocket: WebSocket,
    session_id: str,
    user_id: str,
    message_data: dict[str, Any]
):
    """Handle chat message received via WebSocket."""
    try:
        # Send processing status
        await manager.send_message(user_id, session_id, {
            "type": "status",
            "status": "processing",
            "message": "Processing your message..."
        })

        # Create message object
        chat_message = ChatMessageCreate(
            content=message_data.get("content", ""),
            dataset_id=message_data.get("dataset_id"),
            context=message_data.get("context")
        )

        # Process message
        response = await chat_service.process_user_message(
            session_id, user_id, chat_message
        )

        # Send response back via WebSocket
        await manager.send_message(user_id, session_id, {
            "type": "message_response",
            "message": response.message.dict(),
            "suggestions": response.suggestions
        })

    except Exception as e:
        logger.error(f"WebSocket message handling failed: {e}")

        # Send error message
        await manager.send_message(user_id, session_id, {
            "type": "error",
            "message": "Failed to process your message",
            "error": str(e)
        })


@router.get("/vanna/status")
async def get_vanna_status(current_user: User = Depends(get_current_user)):
    """Get vanna.ai service status and training summary."""
    try:
        await vanna_service.initialize()
        status_info = await vanna_service.get_training_data_summary()
        suggestions = await vanna_service.get_suggested_questions()

        return {
            "service_status": "active" if status_info.get("status") == "active" else "mock_mode",
            "training_data_count": status_info.get("training_data_count", 0),
            "model_name": status_info.get("model_name", "unknown"),
            "suggested_questions": suggestions,
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get vanna status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        ) from e


@router.post("/vanna/ask")
async def ask_vanna_direct(
    request: VannaAskRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """Direct interaction with vanna.ai - ask question and get SQL + results."""
    question = request.question
    if not question or len(question.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must be at least 3 characters long"
        )

    try:
        # Use vanna's complete ask workflow
        start_time = datetime.utcnow()
        result = await vanna_service.ask(question.strip())
        end_time = datetime.utcnow()

        processing_time = (end_time - start_time).total_seconds() * 1000

        return {
            "question": result["question"],
            "sql": result["sql"],
            "results": result["results"],
            "row_count": result["row_count"],
            "columns": result["columns"],
            "processing_time_ms": processing_time,
            "timestamp": end_time.isoformat(),
            "service_mode": "vanna_ai" if result.get("status") == "success" else "mock"
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Vanna ask failed for question '{question[:50]}...': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        ) from e


@router.post("/vanna/train/ddl")
async def train_vanna_with_ddl(
    ddl: str,
    table_name: str,
    current_user: User = Depends(get_current_user)
):
    """Train vanna.ai with DDL statements."""
    if not ddl or not table_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both DDL and table_name are required"
        )

    try:
        success = await vanna_service.train_with_ddl(ddl.strip(), table_name.strip())

        if success:
            return {
                "message": f"Successfully trained vanna with DDL for table: {table_name}",
                "table_name": table_name,
                "trained_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Training failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DDL training failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        ) from e


@router.post("/vanna/train/documentation")
async def train_vanna_with_docs(
    documentation: str,
    current_user: User = Depends(get_current_user)
):
    """Train vanna.ai with business documentation."""
    if not documentation or len(documentation.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Documentation must be at least 10 characters long"
        )

    try:
        success = await vanna_service.train_with_documentation(documentation.strip())

        if success:
            return {
                "message": "Successfully trained vanna with documentation",
                "documentation_length": len(documentation),
                "trained_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Training failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Documentation training failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        ) from e


@router.post("/vanna/train/sql")
async def train_vanna_with_sql(
    question: str,
    sql: str,
    current_user: User = Depends(get_current_user)
):
    """Train vanna.ai with question-SQL pairs."""
    if not question or not sql:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both question and SQL are required"
        )

    try:
        success = await vanna_service.train_with_sql(question.strip(), sql.strip())

        if success:
            return {
                "message": "Successfully trained vanna with question-SQL pair",
                "question": question[:100] + "..." if len(question) > 100 else question,
                "trained_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Training failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL training failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        ) from e


@router.post("/vanna/initialize")
async def initialize_vanna_training(
    current_user: User = Depends(get_current_user)
):
    """初始化 vanna.ai 訓練資料 - 使用庫存資料模型"""
    try:
        success = await vanna_training_service.initialize_training()

        if success:
            # 檢查訓練狀態
            status_info = await vanna_service.get_training_data_summary()

            return {
                "message": "vanna.ai 訓練資料初始化完成",
                "status": "success",
                "training_data_count": status_info.get("training_data_count", 0),
                "initialized_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="訓練初始化失敗"
            )

    except Exception as e:
        logger.error(f"Vanna training initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"訓練初始化失敗: {str(e)}"
        ) from e


@router.post("/sessions/{session_id}/export")
async def export_chat_session(
    session_id: str = Depends(validate_session_access),
    format: str = "json",
    current_user: User = Depends(get_current_user)
):
    """Export chat session data."""
    try:
        # Get session and messages
        session = await chat_service.get_chat_session(session_id, current_user.id)
        messages = await chat_service.get_session_messages(session_id, current_user.id, 1000)

        export_data = {
            "session": session.dict(),
            "messages": [msg.dict() for msg in messages],
            "exported_at": datetime.utcnow().isoformat()
        }

        if format == "json":
            def generate_json():
                yield json.dumps(export_data, indent=2)

            return StreamingResponse(
                generate_json(),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=chat_session_{session_id}.json"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format"
            )

    except Exception as e:
        logger.error(f"Chat export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export chat session"
        ) from e
