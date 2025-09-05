"""
Vanna.AI service integration for natural language to SQL conversion.
Uses modern vanna.ai architecture with PostgreSQL and OpenAI integration.
"""
import asyncio
import logging
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Import vanna with proper error handling
try:
    from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
    from vanna.openai.openai_chat import OpenAI_Chat
    VANNA_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Vanna.ai imports failed: {e}")
    VANNA_AVAILABLE = False

from ..core.config import settings

logger = logging.getLogger(__name__)


class VannaAI(ChromaDB_VectorStore, OpenAI_Chat):
    """Custom Vanna.AI class combining ChromaDB vector store with OpenAI chat."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Vanna with ChromaDB and OpenAI."""
        if not config:
            config = {}

        # Initialize vector store
        ChromaDB_VectorStore.__init__(self, config=config)

        # Initialize OpenAI chat
        OpenAI_Chat.__init__(self, config=config)


class VannaService:
    """Service for integrating with vanna.ai for SQL generation and training."""

    def __init__(self):
        """Initialize VannaService with configuration."""
        self.model_name = settings.vanna_model_name or "excel-chatbot"
        self.openai_api_key = settings.openai_api_key or settings.vanna_api_key
        self._client: VannaAI | None = None
        self._initialized = False
        self.database_url = settings.database_url

    async def initialize(self) -> None:
        """Initialize vanna.ai client with OpenAI and ChromaDB."""
        if self._initialized:
            return

        if not VANNA_AVAILABLE:
            if settings.environment == "development":
                logger.warning("Vanna.ai not available - using mock service for development")
                self._initialized = True
                return
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Vanna.ai service not available"
                )

        try:
            # Configuration for vanna.ai
            config = {
                'model': 'gpt-4o-mini',  # Use cost-effective model
                'api_key': self.openai_api_key,
                'path': f'./vanna_db/{self.model_name}',  # Local ChromaDB path
            }

            if not self.openai_api_key:
                if settings.environment == "development":
                    logger.warning("No OpenAI API key - using mock service for development")
                    self._initialized = True
                    return
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="OpenAI API key not configured"
                    )

            # Initialize vanna client
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None,
                lambda: VannaAI(config=config)
            )

            # Connect to PostgreSQL database if URL is available
            if self.database_url:
                await self._connect_to_database()

            self._initialized = True
            logger.info(f"Vanna.ai service initialized successfully with model: {config['model']}")

        except Exception as e:
            logger.error(f"Failed to initialize Vanna.ai service: {e}")
            if settings.environment == "development":
                logger.warning("Falling back to mock service for development")
                self._initialized = True
                return
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Vanna.ai initialization failed: {str(e)}"
            )

    async def _connect_to_database(self) -> None:
        """Connect vanna to the PostgreSQL database."""
        if not self._client or not self.database_url:
            return

        try:
            # Parse database URL components for PostgreSQL connection
            # DATABASE_URL format: postgresql://user:password@host:port/dbname
            import urllib.parse as urlparse

            parsed = urlparse.urlparse(self.database_url)

            connection_params = {
                'host': parsed.hostname,
                'dbname': parsed.path.lstrip('/'),
                'user': parsed.username,
                'password': parsed.password,
                'port': parsed.port or 5432
            }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.connect_to_postgres(**connection_params)
            )

            logger.info("Successfully connected vanna to PostgreSQL database")

        except Exception as e:
            logger.error(f"Failed to connect vanna to database: {e}")
            # Don't raise exception - vanna can work without direct DB connection

    async def get_training_data_summary(self) -> dict[str, Any]:
        """Get summary of current training data."""
        await self.initialize()

        if not self._client:
            return {"status": "mock_mode", "training_data": 0}

        try:
            loop = asyncio.get_event_loop()
            training_data = await loop.run_in_executor(
                None,
                lambda: self._client.get_training_data()
            )

            return {
                "status": "active",
                "training_data_count": len(training_data) if training_data else 0,
                "model_name": self.model_name
            }

        except Exception as e:
            logger.warning(f"Failed to get training data summary: {e}")
            return {"status": "error", "error": str(e)}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((Exception,))
    )
    async def train_with_ddl(self, ddl: str, table_name: str) -> bool:
        """Train vanna with DDL statements for table schema."""
        await self.initialize()

        if not self._client:
            logger.info(f"Mock training with DDL for table: {table_name}")
            return True

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.train(ddl=ddl)
            )

            logger.info(f"Successfully trained vanna with DDL for table: {table_name}")
            return True

        except Exception as e:
            logger.error(f"DDL training failed for {table_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training failed: {str(e)}"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((Exception,))
    )
    async def train_with_documentation(self, documentation: str) -> bool:
        """Train vanna with business documentation and context."""
        await self.initialize()

        if not self._client:
            logger.info(f"Mock training with documentation: {documentation[:100]}...")
            return True

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.train(documentation=documentation)
            )

            logger.info("Successfully trained with documentation")
            return True

        except Exception as e:
            logger.error(f"Documentation training failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training failed: {str(e)}"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((Exception,))
    )
    async def train_with_sql(self, question: str, sql: str) -> bool:
        """Train vanna with question-SQL pairs."""
        await self.initialize()

        if not self._client:
            logger.info(f"Mock training with SQL: {question[:50]}...")
            return True

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.train(question=question, sql=sql)
            )

            logger.info(f"Successfully trained with question-SQL pair: {question[:50]}...")
            return True

        except Exception as e:
            logger.error(f"SQL training failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training failed: {str(e)}"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((Exception,))
    )
    async def generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question."""
        await self.initialize()

        # Mock mode for development
        if not self._client:
            logger.info(f"Generating mock SQL for: {question[:100]}...")
            return self._generate_mock_sql(question)

        try:
            loop = asyncio.get_event_loop()
            sql = await loop.run_in_executor(
                None,
                lambda: self._client.generate_sql(question=question)
            )

            if not sql or sql.strip() == "":
                raise ValueError("Empty SQL query generated")

            # Apply safety constraints
            safe_sql = self._apply_safety_constraints(sql)

            logger.info(f"Successfully generated SQL for: {question[:100]}...")
            return safe_sql

        except Exception as e:
            logger.error(f"SQL generation failed for question '{question[:50]}...': {e}")

            # Fallback to mock in development
            if settings.environment == "development":
                logger.warning("Falling back to mock SQL generation")
                return self._generate_mock_sql(question)

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not generate SQL query: {str(e)}"
            )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((Exception,))
    )
    async def execute_sql(self, sql: str) -> pd.DataFrame:
        """Execute SQL query and return results as pandas DataFrame."""
        await self.initialize()

        if not self._client:
            # Return mock data for development
            logger.info("Returning mock data for SQL execution")
            return self._generate_mock_dataframe(sql)

        try:
            # Apply safety constraints before execution
            safe_sql = self._apply_safety_constraints(sql)

            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: self._client.run_sql(safe_sql)
            )

            if df is None or df.empty:
                logger.warning("SQL execution returned empty results")
                return pd.DataFrame()

            logger.info(f"SQL executed successfully, returned {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")

            # Return mock data in development
            if settings.environment == "development":
                logger.warning("Returning mock data due to execution failure")
                return self._generate_mock_dataframe(sql)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution failed: {str(e)}"
            )

    async def ask(self, question: str) -> dict[str, Any]:
        """Complete ask workflow: generate SQL and execute it."""
        await self.initialize()

        try:
            # Generate SQL from question
            sql = await self.generate_sql(question)

            # Execute SQL and get results
            df = await self.execute_sql(sql)

            return {
                "question": question,
                "sql": sql,
                "results": df.to_dict('records') if not df.empty else [],
                "row_count": len(df),
                "columns": list(df.columns) if not df.empty else [],
                "status": "success"
            }

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Ask workflow failed for question '{question[:50]}...': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query processing failed: {str(e)}"
            )

    def _apply_safety_constraints(self, sql: str) -> str:
        """Apply safety constraints to SQL query."""
        sql = sql.strip()

        # Check for dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'REPLACE']
        sql_upper = sql.upper()

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"Dangerous SQL operation '{keyword}' not allowed")

        # Ensure SELECT only
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            raise ValueError("Only SELECT and WITH queries are allowed")

        # Add LIMIT if not present
        if 'LIMIT' not in sql_upper:
            if sql.endswith(';'):
                sql = sql[:-1] + f' LIMIT {settings.default_query_limit};'
            else:
                sql += f' LIMIT {settings.default_query_limit}'

        return sql

    def _generate_mock_sql(self, question: str) -> str:
        """Generate mock SQL for development and testing."""
        question_lower = question.lower()
        limit = settings.default_query_limit

        # Pattern matching for different question types
        if any(word in question_lower for word in ['total', 'sum', 'count']):
            return f"SELECT COUNT(*) as total_count FROM sample_data LIMIT {limit};"
        elif any(word in question_lower for word in ['average', 'mean', 'avg']):
            return f"SELECT AVG(value) as average_value FROM sample_data LIMIT {limit};"
        elif any(word in question_lower for word in ['top', 'highest', 'maximum', 'best']):
            return "SELECT * FROM sample_data ORDER BY value DESC LIMIT 10;"
        elif any(word in question_lower for word in ['bottom', 'lowest', 'minimum', 'worst']):
            return "SELECT * FROM sample_data ORDER BY value ASC LIMIT 10;"
        elif 'group' in question_lower or 'category' in question_lower:
            return f"SELECT category, COUNT(*) as count FROM sample_data GROUP BY category LIMIT {limit};"
        elif 'trend' in question_lower or 'time' in question_lower:
            return f"SELECT date, SUM(value) as total_value FROM sample_data GROUP BY date ORDER BY date LIMIT {limit};"
        else:
            return f"SELECT * FROM sample_data LIMIT {limit};"

    def _generate_mock_dataframe(self, sql: str) -> pd.DataFrame:
        """Generate mock DataFrame for development and testing."""
        sql_lower = sql.lower()

        # Create different mock data based on SQL patterns
        if 'count(*)' in sql_lower:
            return pd.DataFrame({'total_count': [42]})
        elif 'avg(' in sql_lower:
            return pd.DataFrame({'average_value': [67.8]})
        elif 'group by' in sql_lower:
            return pd.DataFrame({
                'category': ['A', 'B', 'C', 'D'],
                'count': [15, 23, 8, 12]
            })
        elif 'order by' in sql_lower and 'desc' in sql_lower:
            return pd.DataFrame({
                'id': [1, 2, 3, 4, 5],
                'name': ['Item A', 'Item B', 'Item C', 'Item D', 'Item E'],
                'value': [95, 87, 76, 65, 54]
            })
        elif 'date' in sql_lower:
            return pd.DataFrame({
                'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
                'total_value': [120, 150, 98]
            })
        else:
            # Default mock data
            return pd.DataFrame({
                'id': [1, 2, 3, 4, 5],
                'name': ['Sample A', 'Sample B', 'Sample C', 'Sample D', 'Sample E'],
                'value': [10, 20, 30, 40, 50],
                'category': ['X', 'Y', 'X', 'Z', 'Y']
            })

    async def get_suggested_questions(self) -> list[str]:
        """Get suggested questions based on training data."""
        return [
            "What is the total number of records?",
            "Show me the average values by category",
            "What are the top 10 items by value?",
            "How has the trend changed over time?",
            "Which categories have the highest counts?"
        ]

    async def train_with_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        description: str = ""
    ) -> bool:
        """Train vanna with a pandas DataFrame."""
        await self.initialize()

        try:
            # Generate DDL from DataFrame structure
            ddl = self._generate_ddl_from_dataframe(df, table_name)
            await self.train_with_ddl(ddl, table_name)

            # Train with description if provided
            if description:
                doc = f"Table '{table_name}': {description}"
                await self.train_with_documentation(doc)

            # Generate and train with sample questions
            sample_questions = self._generate_sample_questions(df, table_name)
            for question, sql in sample_questions:
                await self.train_with_sql(question, sql)

            logger.info(f"Successfully trained with DataFrame for table: {table_name}")
            return True

        except Exception as e:
            logger.error(f"DataFrame training failed for {table_name}: {e}")
            return False

    def _generate_ddl_from_dataframe(self, df: pd.DataFrame, table_name: str) -> str:
        """Generate DDL statement from DataFrame structure."""
        columns = []

        for col_name, dtype in df.dtypes.items():
            if 'int' in str(dtype):
                col_type = 'INTEGER'
            elif 'float' in str(dtype):
                col_type = 'DECIMAL'
            elif 'bool' in str(dtype):
                col_type = 'BOOLEAN'
            elif 'datetime' in str(dtype):
                col_type = 'TIMESTAMP'
            elif 'date' in str(dtype):
                col_type = 'DATE'
            else:
                col_type = 'TEXT'

            columns.append(f"  {col_name} {col_type}")

        ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"
        return ddl

    def _generate_sample_questions(
        self,
        df: pd.DataFrame,
        table_name: str
    ) -> list[tuple[str, str]]:
        """Generate sample questions and SQL for training."""
        questions = []
        limit = settings.default_query_limit

        # Basic count
        questions.append((
            "How many records are there?",
            f"SELECT COUNT(*) FROM {table_name} LIMIT {limit};"
        ))

        # Find numeric columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if numeric_cols:
            col = numeric_cols[0]
            questions.extend([
                (f"What is the average {col}?", f"SELECT AVG({col}) FROM {table_name} LIMIT {limit};"),
                (f"What is the total {col}?", f"SELECT SUM({col}) FROM {table_name} LIMIT {limit};"),
                (f"Show top 10 by {col}", f"SELECT * FROM {table_name} ORDER BY {col} DESC LIMIT 10;")
            ])

        # Find categorical columns
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        if text_cols and numeric_cols:
            text_col = text_cols[0]
            num_col = numeric_cols[0]
            questions.append((
                f"Show {num_col} by {text_col}",
                f"SELECT {text_col}, SUM({num_col}) FROM {table_name} GROUP BY {text_col} LIMIT {limit};"
            ))

        return questions


# Global vanna service instance
vanna_service = VannaService()
