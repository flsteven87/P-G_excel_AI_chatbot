"""
File upload and dataset management API endpoints.
"""
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from ...models.dataset import (
    DataPreview,
    DatasetInfo,
    DatasetListResponse,
    DataSummary,
    FileProcessingResult,
)
from ...models.user import User
from ...services.file_service import file_service
from ...services.vanna_service import vanna_service
from ..dependencies import PaginationParams, get_current_user, validate_dataset_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileProcessingResult)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataset_name: str = "Untitled Dataset",
    description: str | None = None,
    current_user: User = Depends(get_current_user)
):
    """
    Upload Excel/CSV file and create dataset.
    Processing happens in background after initial validation.
    """
    try:
        logger.info(f"File upload started: {file.filename} by user {current_user.id}")

        # Process file and create dataset
        result = await file_service.process_uploaded_file(
            file=file,
            dataset_name=dataset_name,
            user_id=current_user.id,
            description=description
        )

        # Update user statistics in background
        background_tasks.add_task(
            update_user_stats,
            current_user.id,
            dataset_count_increment=1,
            storage_increment_mb=result.rows_inserted * 0.001  # Rough estimate
        )

        logger.info(f"File processing completed: {result.dataset_id}")
        return result

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets(
    pagination: PaginationParams = Depends(PaginationParams),
    current_user: User = Depends(get_current_user)
):
    """List user's datasets."""
    try:
        from ...core.database import get_supabase_client

        client = await get_supabase_client()

        # Get datasets with pagination
        response = client.table("datasets")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .order("created_at", desc=True)\
            .range(pagination.offset, pagination.offset + pagination.limit - 1)\
            .execute()

        if response.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve datasets"
            )

        datasets = [DatasetInfo(**dataset) for dataset in response.data or []]

        # Get total count
        count_response = client.table("datasets")\
            .select("id", count="exact")\
            .eq("user_id", current_user.id)\
            .execute()

        total_count = count_response.count if count_response else 0
        has_more = pagination.offset + len(datasets) < total_count

        return DatasetListResponse(
            datasets=datasets,
            total_count=total_count,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve datasets"
        )


@router.get("/datasets/{dataset_id}", response_model=DatasetInfo)
async def get_dataset(
    dataset_id: str = Depends(validate_dataset_access),
    current_user: User = Depends(get_current_user)
):
    """Get dataset information."""
    try:
        from ...core.database import get_supabase_client

        client = await get_supabase_client()

        response = client.table("datasets")\
            .select("*")\
            .eq("id", dataset_id)\
            .eq("user_id", current_user.id)\
            .single()\
            .execute()

        if response.error or not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        return DatasetInfo(**response.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dataset"
        )


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    background_tasks: BackgroundTasks,
    dataset_id: str = Depends(validate_dataset_access),
    current_user: User = Depends(get_current_user)
):
    """Delete a dataset."""
    try:
        from ...core.database import get_supabase_service_client

        client = await get_supabase_service_client()

        # Get dataset info first
        dataset_response = client.table("datasets")\
            .select("*")\
            .eq("id", dataset_id)\
            .single()\
            .execute()

        if dataset_response.error or not dataset_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        dataset = DatasetInfo(**dataset_response.data)

        # Delete the database table
        drop_sql = f'DROP TABLE IF EXISTS "{dataset.table_name}";'
        client.rpc('execute_sql', {'sql': drop_sql}).execute()

        # Delete storage file
        client.storage.from_(dataset.file_path.split('/')[0]).remove([dataset.file_path])

        # Delete dataset record
        response = client.table("datasets")\
            .delete()\
            .eq("id", dataset_id)\
            .execute()

        if response.error:
            raise Exception("Failed to delete dataset record")

        # Update user statistics in background
        background_tasks.add_task(
            update_user_stats,
            current_user.id,
            dataset_count_increment=-1,
            storage_increment_mb=-dataset.file_size_bytes / (1024 * 1024)
        )

        return {"message": "Dataset deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset: {str(e)}"
        )


@router.get("/datasets/{dataset_id}/preview", response_model=DataPreview)
async def preview_dataset(
    dataset_id: str = Depends(validate_dataset_access),
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get preview of dataset data."""
    try:
        from ...services.query_service import query_service

        # Get dataset info
        dataset = await get_dataset(dataset_id, current_user)

        # Query sample data
        preview_sql = f'SELECT * FROM "{dataset.table_name}" LIMIT {limit + 1}'

        result = await query_service.execute_query(
            sql_query=preview_sql,
            user_id=current_user.id,
            dataset_id=dataset_id
        )

        rows = result.results.get("data", [])
        has_more = len(rows) > limit

        if has_more:
            rows = rows[:limit]

        return DataPreview(
            dataset_id=dataset_id,
            columns=result.columns,
            rows=rows,
            total_rows=dataset.row_count,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f"Failed to preview dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview dataset"
        )


@router.get("/datasets/{dataset_id}/summary", response_model=DataSummary)
async def get_dataset_summary(
    dataset_id: str = Depends(validate_dataset_access),
    current_user: User = Depends(get_current_user)
):
    """Get statistical summary of dataset."""
    try:
        from ...services.query_service import query_service

        # Get dataset info
        dataset = await get_dataset(dataset_id, current_user)

        summary = DataSummary(dataset_id=dataset_id)

        # Get basic statistics for each column
        for column in dataset.columns:
            col_name = column.name

            if column.type.value in ["integer", "float"]:
                # Numeric statistics
                stats_sql = f'''
                SELECT
                    AVG("{col_name}") as mean,
                    STDDEV("{col_name}") as std,
                    MIN("{col_name}") as min,
                    MAX("{col_name}") as max,
                    COUNT(DISTINCT "{col_name}") as unique_count,
                    COUNT(*) - COUNT("{col_name}") as null_count
                FROM "{dataset.table_name}"
                '''

                result = await query_service.execute_query(
                    sql_query=stats_sql,
                    user_id=current_user.id,
                    dataset_id=dataset_id
                )

                if result.results.get("data"):
                    stats = result.results["data"][0]
                    summary.numeric_columns[col_name] = {
                        "mean": stats.get("mean"),
                        "std": stats.get("std"),
                        "min": stats.get("min"),
                        "max": stats.get("max"),
                        "unique_count": stats.get("unique_count"),
                    }
                    summary.missing_data[col_name] = stats.get("null_count", 0)

            elif column.type.value == "text":
                # Categorical statistics
                value_counts_sql = f'''
                SELECT "{col_name}" as value, COUNT(*) as count
                FROM "{dataset.table_name}"
                WHERE "{col_name}" IS NOT NULL
                GROUP BY "{col_name}"
                ORDER BY count DESC
                LIMIT 10
                '''

                result = await query_service.execute_query(
                    sql_query=value_counts_sql,
                    user_id=current_user.id,
                    dataset_id=dataset_id
                )

                if result.results.get("data"):
                    value_counts = {
                        row["value"]: row["count"]
                        for row in result.results["data"]
                    }
                    summary.categorical_columns[col_name] = {
                        "value_counts": value_counts,
                        "unique_count": len(value_counts)
                    }

                # Get null count
                null_count_sql = f'''
                SELECT COUNT(*) - COUNT("{col_name}") as null_count
                FROM "{dataset.table_name}"
                '''

                result = await query_service.execute_query(
                    sql_query=null_count_sql,
                    user_id=current_user.id,
                    dataset_id=dataset_id
                )

                if result.results.get("data"):
                    summary.missing_data[col_name] = result.results["data"][0].get("null_count", 0)

            # Add data type info
            summary.data_types[col_name] = column.type.value

        return summary

    except Exception as e:
        logger.error(f"Failed to get dataset summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dataset summary"
        )


@router.post("/datasets/{dataset_id}/retrain")
async def retrain_dataset(
    background_tasks: BackgroundTasks,
    dataset_id: str = Depends(validate_dataset_access),
    current_user: User = Depends(get_current_user)
):
    """Retrain vanna.ai model with dataset."""
    try:
        # Get dataset info
        dataset = await get_dataset(dataset_id, current_user)

        # Schedule retraining in background
        background_tasks.add_task(
            retrain_vanna_with_dataset,
            dataset
        )

        return {"message": "Dataset retraining scheduled"}

    except Exception as e:
        logger.error(f"Failed to schedule retraining: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule retraining"
        )


# Background task functions

async def update_user_stats(
    user_id: str,
    dataset_count_increment: int = 0,
    storage_increment_mb: float = 0.0
):
    """Update user statistics."""
    try:
        from ...core.database import get_supabase_service_client

        client = await get_supabase_service_client()

        # Update user stats
        client.table("users")\
            .update({
                "total_datasets": f"total_datasets + {dataset_count_increment}",
                "storage_used_mb": f"storage_used_mb + {storage_increment_mb}"
            })\
            .eq("id", user_id)\
            .execute()

        logger.info(f"Updated user stats for {user_id}")

    except Exception as e:
        logger.error(f"Failed to update user stats: {e}")


async def retrain_vanna_with_dataset(dataset: DatasetInfo):
    """Background task to retrain vanna.ai with dataset."""
    try:
        success = await vanna_service.train_with_dataset(dataset)
        if success:
            logger.info(f"Vanna retraining completed for dataset: {dataset.id}")
        else:
            logger.error(f"Vanna retraining failed for dataset: {dataset.id}")

    except Exception as e:
        logger.error(f"Vanna retraining error for dataset {dataset.id}: {e}")
