"""
Query execution service with safety constraints and performance monitoring.
Handles secure SQL execution with timeouts, limits, and result formatting.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import asyncpg
import pandas as pd
from fastapi import HTTPException, status

from ..core.config import settings
from ..core.security import privacy_manager, sql_validator
from ..models.chat import QueryResponse

logger = logging.getLogger(__name__)


class QueryExecutionError(Exception):
    """Custom exception for query execution errors."""
    pass


class QueryService:
    """Service for executing SQL queries with safety constraints."""

    def __init__(self):
        self.statement_timeout = settings.statement_timeout_ms
        self.default_limit = settings.default_query_limit
        self.max_result_size = 10 * 1024 * 1024  # 10MB max result size

    async def execute_query(
        self,
        sql_query: str,
        user_id: str,
        dataset_id: str | None = None,
        timeout_ms: int | None = None
    ) -> QueryResponse:
        """
        Execute SQL query with safety constraints and return formatted results.
        """
        start_time = time.time()
        query_timeout = timeout_ms or self.statement_timeout

        try:
            # Validate and sanitize query
            safe_query = sql_validator.sanitize_query(sql_query)
            logger.info(f"Executing query for user {user_id}: {safe_query[:100]}...")

            # Execute query with timeout
            results, columns = await self._execute_with_timeout(
                safe_query, user_id, query_timeout
            )

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Format results
            formatted_results = self._format_results(results, columns)

            # Apply privacy masking if needed
            masked_results = self._apply_privacy_masking(formatted_results)

            # Generate chart suggestions
            chart_suggestions = self._generate_chart_suggestions(masked_results, columns)

            response = QueryResponse(
                sql_query=safe_query,
                results=masked_results,
                execution_time_ms=execution_time_ms,
                row_count=len(results) if results else 0,
                columns=columns,
                chart_suggestions=chart_suggestions
            )

            logger.info(f"Query executed successfully: {len(results)} rows in {execution_time_ms:.2f}ms")
            return response

        except TimeoutError:
            logger.warning(f"Query timeout after {query_timeout}ms for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Query execution timeout after {query_timeout / 1000} seconds"
            )
        except HTTPException:
            # Re-raise FastAPI exceptions
            raise
        except Exception as e:
            logger.error(f"Query execution failed for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution failed: {str(e)}"
            )

    async def _execute_with_timeout(
        self,
        query: str,
        user_id: str,
        timeout_ms: int
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Execute query with timeout protection."""
        try:
            # Use asyncpg for direct PostgreSQL connection with timeout
            conn_str = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')

            async def _run_query():
                try:
                    conn = await asyncpg.connect(conn_str)

                    # Set statement timeout at connection level
                    await conn.execute(f"SET statement_timeout = {timeout_ms}")

                    # Add user context for RLS (Row Level Security)
                    # Note: This would need proper JWT token handling in production
                    await conn.execute("SELECT set_config('request.jwt.claim.sub', $1, true)", user_id)

                    # Execute the query
                    rows = await conn.fetch(query)

                    # Convert to list of dictionaries
                    results = []
                    columns = []

                    if rows:
                        columns = list(rows[0].keys())
                        for row in rows:
                            result_row = {}
                            for key, value in row.items():
                                # Handle different data types
                                if value is None:
                                    result_row[key] = None
                                elif isinstance(value, int | float | str | bool):
                                    result_row[key] = value
                                elif isinstance(value, datetime):
                                    result_row[key] = value.isoformat()
                                else:
                                    result_row[key] = str(value)
                            results.append(result_row)

                    await conn.close()
                    return results, columns

                except asyncpg.exceptions.QueryCanceledError:
                    raise TimeoutError("Query was canceled due to timeout")
                except Exception as e:
                    logger.error(f"Database query error: {e}")
                    raise QueryExecutionError(f"Database error: {str(e)}")

            # Execute with timeout
            return await asyncio.wait_for(
                _run_query(),
                timeout=timeout_ms / 1000  # Convert to seconds
            )

        except TimeoutError:
            logger.warning(f"Query timeout after {timeout_ms}ms")
            raise
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise QueryExecutionError(str(e))

    def _format_results(
        self,
        results: list[dict[str, Any]],
        columns: list[str]
    ) -> dict[str, Any]:
        """Format query results for API response."""
        if not results:
            return {
                "data": [],
                "columns": columns,
                "total_rows": 0,
                "has_more": False
            }

        # Check if results exceed size limit
        result_size = len(str(results).encode('utf-8'))
        has_more = result_size > self.max_result_size

        if has_more:
            # Truncate results to fit size limit
            truncated_results = []
            current_size = 0
            for row in results:
                row_size = len(str(row).encode('utf-8'))
                if current_size + row_size > self.max_result_size:
                    break
                truncated_results.append(row)
                current_size += row_size
            results = truncated_results

        return {
            "data": results,
            "columns": columns,
            "total_rows": len(results),
            "has_more": has_more,
            "metadata": {
                "result_size_bytes": result_size,
                "truncated": has_more
            }
        }

    def _apply_privacy_masking(self, formatted_results: dict[str, Any]) -> dict[str, Any]:
        """Apply privacy masking to sensitive data."""
        if not formatted_results.get("data"):
            return formatted_results

        # Create a copy to avoid modifying original
        masked_results = formatted_results.copy()
        masked_data = []

        for row in formatted_results["data"]:
            masked_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    # Apply PII masking
                    masked_value = privacy_manager.mask_pii(value)
                    masked_row[key] = masked_value
                else:
                    masked_row[key] = value
            masked_data.append(masked_row)

        masked_results["data"] = masked_data
        return masked_results

    def _generate_chart_suggestions(
        self,
        formatted_results: dict[str, Any],
        columns: list[str]
    ) -> list[dict[str, Any]]:
        """Generate chart visualization suggestions based on query results."""
        if not formatted_results.get("data") or len(formatted_results["data"]) == 0:
            return []

        suggestions = []
        data = formatted_results["data"]

        # Analyze column types
        numeric_columns = []
        text_columns = []
        date_columns = []

        if data:
            sample_row = data[0]
            for col in columns:
                if col in sample_row:
                    value = sample_row[col]
                    if isinstance(value, int | float):
                        numeric_columns.append(col)
                    elif isinstance(value, str):
                        # Check if it looks like a date
                        try:
                            pd.to_datetime(value)
                            date_columns.append(col)
                        except (ValueError, TypeError):
                            text_columns.append(col)

        # Generate suggestions based on data structure
        if numeric_columns and text_columns:
            # Bar chart for categorical vs numeric
            suggestions.append({
                "type": "bar",
                "title": f"{numeric_columns[0]} by {text_columns[0]}",
                "x_axis": text_columns[0],
                "y_axis": numeric_columns[0],
                "description": "Bar chart showing distribution across categories"
            })

        if len(numeric_columns) >= 2:
            # Scatter plot for numeric vs numeric
            suggestions.append({
                "type": "scatter",
                "title": f"{numeric_columns[0]} vs {numeric_columns[1]}",
                "x_axis": numeric_columns[0],
                "y_axis": numeric_columns[1],
                "description": "Scatter plot showing correlation between variables"
            })

        if date_columns and numeric_columns:
            # Line chart for time series
            suggestions.append({
                "type": "line",
                "title": f"{numeric_columns[0]} over time",
                "x_axis": date_columns[0],
                "y_axis": numeric_columns[0],
                "description": "Line chart showing trends over time"
            })

        if text_columns and len({row[text_columns[0]] for row in data if text_columns[0] in row}) <= 10:
            # Pie chart for categorical distribution
            suggestions.append({
                "type": "pie",
                "title": f"Distribution of {text_columns[0]}",
                "category": text_columns[0],
                "description": "Pie chart showing categorical distribution"
            })

        # Limit to top 3 suggestions
        return suggestions[:3]

    async def validate_query_access(
        self,
        query: str,
        user_id: str,
        dataset_id: str | None = None
    ) -> bool:
        """Validate user has access to execute query on specified tables."""
        try:
            # Extract table names from query (basic implementation)
            query_upper = query.upper()

            # This is a simplified approach - in production, you'd want proper SQL parsing
            if "FROM" in query_upper:
                # Basic table name extraction
                parts = query_upper.split("FROM")[1].split()
                if parts:
                    table_name = parts[0].strip('"').strip("'")

                    # Check if user has access to this table
                    if not table_name.startswith(f"user_{user_id}_"):
                        logger.warning(f"User {user_id} attempted to access unauthorized table: {table_name}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Query access validation failed: {e}")
            return False

    async def explain_query(self, query: str, user_id: str) -> dict[str, Any]:
        """Get query execution plan for performance analysis."""
        try:
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"

            results, _ = await self._execute_with_timeout(
                explain_query, user_id, self.statement_timeout
            )

            if results:
                return {
                    "execution_plan": results[0],
                    "query": query
                }

            return {"execution_plan": None, "query": query}

        except Exception as e:
            logger.error(f"Query explain failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to explain query"
            )

    async def get_query_cost(self, query: str, user_id: str) -> dict[str, Any]:
        """Estimate query execution cost."""
        try:
            cost_query = f"EXPLAIN (FORMAT JSON) {query}"

            results, _ = await self._execute_with_timeout(
                cost_query, user_id, 5000  # Quick timeout for cost estimation
            )

            if results and results[0]:
                plan = results[0].get('Plan', {})
                return {
                    "estimated_cost": plan.get('Total Cost', 0),
                    "estimated_rows": plan.get('Plan Rows', 0),
                    "query": query
                }

            return {"estimated_cost": 0, "estimated_rows": 0, "query": query}

        except Exception as e:
            logger.warning(f"Query cost estimation failed: {e}")
            return {"estimated_cost": 0, "estimated_rows": 0, "query": query}


# Global query service instance
query_service = QueryService()
