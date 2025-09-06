"""
Vanna.AI service integration for natural language to SQL conversion.
Uses modern vanna.ai architecture with PostgreSQL and OpenAI integration.
"""
import asyncio
import logging
from typing import Any

import asyncpg
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

from ..config.vanna_prompts import VannaPromptConfig
from ..core.config import settings

logger = logging.getLogger(__name__)


class ProfessionalVannaAI(ChromaDB_VectorStore, OpenAI_Chat):
    """專業版 Vanna.AI，整合 P&G 庫存系統專業 prompt"""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize with professional P&G inventory prompts"""
        if not config:
            config = {}

        # Initialize vector store
        ChromaDB_VectorStore.__init__(self, config=config)

        # Initialize OpenAI chat
        OpenAI_Chat.__init__(self, config=config)

        # Load professional prompt configuration
        self.prompt_config = VannaPromptConfig()


class VannaService:
    """Service for integrating with vanna.ai for SQL generation and training."""

    def __init__(self):
        """Initialize VannaService with configuration."""
        self.model_name = settings.vanna_model_name or "excel-chatbot"
        self.openai_api_key = settings.openai_api_key or settings.vanna_api_key
        self._client: ProfessionalVannaAI | None = None
        self._initialized = False
        self.database_url = settings.database_url

    async def initialize(self) -> None:
        """Initialize vanna.ai client with OpenAI and ChromaDB."""
        if self._initialized:
            return

        if not VANNA_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vanna.ai service not available - please install required dependencies"
            )

        try:
            # Configuration for vanna.ai
            config = {
                'model': 'gpt-4o-mini',  # Use cost-effective model
                'api_key': self.openai_api_key,
                'path': f'./vanna_db/{self.model_name}',  # Local ChromaDB path
            }

            if not self.openai_api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OpenAI API key not configured"
                )

            # Initialize vanna client with professional prompts
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None,
                lambda: ProfessionalVannaAI(config=config)
            )


            # Apply professional P&G business context training
            try:
                if hasattr(self._client, 'prompt_config'):
                    # Train with professional business context
                    business_context = self._client.prompt_config.get_business_context()
                    await loop.run_in_executor(
                        None,
                        lambda: self._client.train(documentation=business_context)
                    )

                    # Train with SQL examples
                    sql_examples = self._client.prompt_config.get_sql_examples()
                    for example in sql_examples:
                        await loop.run_in_executor(
                            None,
                            lambda ex=example: self._client.train(
                                question=ex["question"],
                                sql=ex["sql"]
                            )
                        )

                    logger.info("Applied professional P&G business context and SQL examples")
                else:
                    logger.warning("Professional prompt config not available")
            except Exception as e:
                logger.warning(f"Failed to apply professional context: {e}")

            self._initialized = True
            logger.info(f"Custom Vanna.ai service initialized successfully with model: {config['model']}")

        except Exception as e:
            logger.error(f"Failed to initialize Vanna.ai service: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Vanna.ai initialization failed: {str(e)}"
            ) from e


    async def get_training_data_summary(self) -> dict[str, Any]:
        """Get summary of current training data."""
        await self.initialize()

        if not self._client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vanna.ai client not initialized"
            )

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vanna.ai client not initialized"
            )

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
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((Exception,))
    )
    async def train_with_documentation(self, documentation: str) -> bool:
        """Train vanna with business documentation and context."""
        await self.initialize()

        if not self._client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vanna.ai client not initialized"
            )

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
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((Exception,))
    )
    async def train_with_sql(self, question: str, sql: str) -> bool:
        """Train vanna with question-SQL pairs."""
        await self.initialize()

        if not self._client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vanna.ai client not initialized"
            )

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
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((Exception,))
    )
    async def generate_sql(self, question: str) -> str:
        """Generate SQL query from natural language question using vanna.ai."""
        await self.initialize()

        if not self._client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vanna.ai service not properly initialized"
            )

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
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not generate SQL query: {str(e)}"
            ) from e

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((Exception,))
    )
    async def execute_sql(self, sql: str) -> pd.DataFrame:
        """Execute SQL query against real Supabase database."""
        try:
            # Apply safety constraints before execution
            safe_sql = self._apply_safety_constraints(sql)

            # Execute SQL using real Supabase connection
            df = await self._execute_sql_via_supabase(safe_sql)

            if df is None or (hasattr(df, 'empty') and df.empty):
                logger.warning("SQL execution returned empty results")
                return pd.DataFrame()

            logger.info(f"SQL executed successfully, returned {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution failed: {str(e)}"
            ) from e

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
                "data": df.to_dict('records') if (hasattr(df, 'empty') and not df.empty) else [],
                "row_count": len(df) if hasattr(df, '__len__') else 0,
                "columns": list(df.columns) if (hasattr(df, 'columns') and hasattr(df, 'empty') and not df.empty) else [],
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
            ) from e

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

        # Add LIMIT if not present (keep existing LIMIT if present)
        if 'LIMIT' not in sql_upper:
            if sql.endswith(';'):
                sql = sql[:-1] + f' LIMIT {settings.default_query_limit};'
            else:
                sql += f' LIMIT {settings.default_query_limit}'

        return sql

    async def get_suggested_questions(self) -> list[str]:
        """Get suggested questions based on inventory data."""
        return [
            "顯示庫存量前10的產品",
            "按品牌統計總庫存量",
            "哪些產品庫存不足100件",
            "各倉庫的總庫存量",
            "即將停出貨的產品有哪些",
            "顯示所有產品的平均庫存",
            "庫存價值最高的前5個品牌",
            "哪些產品有分配但未出貨"
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

    async def _execute_sql_via_supabase(self, sql: str) -> pd.DataFrame:
        """Execute SQL directly via PostgreSQL connection."""
        conn = await asyncpg.connect(self.database_url)
        records = await conn.fetch(sql)
        await conn.close()

        if records:
            result_list = [dict(record) for record in records]
            return pd.DataFrame(result_list)
        else:
            return pd.DataFrame()



# Global vanna service instance
vanna_service = VannaService()
