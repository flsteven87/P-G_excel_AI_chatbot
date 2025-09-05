# Excel AI Chatbot Backend

FastAPI backend for Excel/CSV AI chatbot with vanna.ai integration.

## Features

- Natural language to SQL conversion using vanna.ai
- Secure file upload and processing for Excel/CSV files
- Real-time chat interface with WebSocket support
- Query execution with safety constraints and timeouts
- User authentication and data isolation with RLS
- Interactive data visualizations and chart suggestions

## Tech Stack

- FastAPI for the web framework
- vanna.ai for SQL generation
- Supabase for database, storage, and authentication
- pandas/pyarrow for data processing
- asyncio for async operations

## Development

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Lint code
uv run ruff check app/

# Type checking
uv run mypy app/
```