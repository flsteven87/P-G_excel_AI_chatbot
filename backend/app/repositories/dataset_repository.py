"""
Dataset repository with async Supabase operations.
Handles dataset metadata persistence and retrieval.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from ..models.dataset import DatasetInfo, ProcessingStatus
from .supabase_base import SupabaseRepository

logger = logging.getLogger(__name__)


class DatasetRepository(SupabaseRepository):
    """Repository for Dataset entities with async Supabase client."""

    def __init__(self):
        super().__init__(table_name="datasets", model_class=DatasetInfo)

    async def get_by_table_name(
        self,
        table_name: str,
        user_id: UUID
    ) -> DatasetInfo | None:
        """Get dataset by table name for a specific user."""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("table_name", table_name).eq("user_id", str(user_id))
            result = await query.execute()

            # Use safe result handling
            data = self._handle_supabase_result(result, allow_empty=True, expect_single=True)

            if not data:
                return None

            return self.model_class(**data)

        except Exception as e:
            logger.error(f"Get by table name failed: {e}")
            return None

    async def create_dataset(self, dataset_data: dict[str, Any], user_id: UUID) -> DatasetInfo:
        """Create a new dataset record."""
        try:
            dataset_data.update({
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "processing_status": ProcessingStatus.UPLOADED.value
            })

            return await super().create(dataset_data, user_id=user_id)

        except Exception as e:
            logger.error(f"Dataset creation failed: {e}")
            raise

    async def get_user_datasets(
        self,
        user_id: UUID,
        status_filter: ProcessingStatus | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[DatasetInfo]:
        """Get datasets for a specific user."""
        try:
            filters = {}
            if status_filter:
                filters["processing_status"] = status_filter.value

            return await super().get_many(
                filters=filters,
                user_id=user_id,
                limit=limit,
                offset=offset
            )

        except Exception as e:
            logger.error(f"Get user datasets failed: {e}")
            return []

    async def update_processing_status(
        self,
        dataset_id: UUID,
        status: ProcessingStatus,
        error_message: str | None = None
    ) -> bool:
        """Update dataset processing status."""
        try:
            update_data = {
                "processing_status": status.value,
                "updated_at": datetime.utcnow().isoformat()
            }

            if error_message:
                update_data["error_message"] = error_message

            result = await super().update(dataset_id, update_data)
            return result is not None

        except Exception as e:
            logger.error(f"Processing status update failed: {e}")
            return False

    async def update_row_count(self, dataset_id: UUID, row_count: int) -> bool:
        """Update dataset row count after processing."""
        try:
            update_data = {
                "row_count": row_count,
                "updated_at": datetime.utcnow().isoformat()
            }

            result = await super().update(dataset_id, update_data)
            return result is not None

        except Exception as e:
            logger.error(f"Row count update failed: {e}")
            return False


# Global repository instance
dataset_repository = DatasetRepository()
