"""
Pydantic models for dataset and file management.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Supported file types."""
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"


class ProcessingStatus(str, Enum):
    """Status of file processing."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ColumnType(str, Enum):
    """Database column types."""
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"


class ColumnInfo(BaseModel):
    """Information about a database column."""
    name: str = Field(..., description="Column name")
    type: ColumnType = Field(..., description="Column data type")
    nullable: bool = Field(True, description="Whether column allows NULL values")
    description: str | None = Field(None, description="Human-readable column description")
    sample_values: list[Any] | None = Field(None, description="Sample values from the column")
    unique_count: int | None = Field(None, description="Number of unique values")
    null_count: int | None = Field(None, description="Number of null values")


class DatasetInfo(BaseModel):
    """Dataset information model."""
    id: str = Field(..., description="Dataset identifier")
    name: str = Field(..., description="Dataset name")
    table_name: str = Field(..., description="Database table name")
    columns: list[ColumnInfo] = Field(..., description="Column information")
    row_count: int = Field(..., description="Number of rows in dataset")
    file_path: str = Field(..., description="Original file path in storage")
    file_type: FileType = Field(..., description="Original file type")
    file_size_bytes: int = Field(..., description="Original file size in bytes")
    user_id: str = Field(..., description="Owner user ID")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: str | None = Field(None, description="Error message if processing failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DatasetCreate(BaseModel):
    """Schema for creating a new dataset."""
    name: str = Field(..., min_length=1, max_length=255, description="Dataset name")
    description: str | None = Field(None, description="Dataset description")


class DatasetResponse(BaseModel):
    """Response schema for dataset operations."""
    dataset: DatasetInfo
    training_status: str | None = Field(None, description="Vanna.ai training status")


class FileUpload(BaseModel):
    """File upload information."""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    size_bytes: int = Field(..., description="File size in bytes")


class FileProcessingResult(BaseModel):
    """Result of file processing operation."""
    dataset_id: str = Field(..., description="Created dataset ID")
    table_name: str = Field(..., description="Created table name")
    columns_created: list[ColumnInfo] = Field(..., description="Created columns")
    rows_inserted: int = Field(..., description="Number of rows inserted")
    processing_time_seconds: float = Field(..., description="Processing time")
    warnings: list[str] | None = Field(None, description="Processing warnings")


class DataPreview(BaseModel):
    """Preview of dataset data."""
    dataset_id: str = Field(..., description="Dataset identifier")
    columns: list[str] = Field(..., description="Column names")
    rows: list[dict[str, Any]] = Field(..., description="Sample rows")
    total_rows: int = Field(..., description="Total number of rows")
    has_more: bool = Field(..., description="Whether there are more rows")


class DataSummary(BaseModel):
    """Statistical summary of dataset."""
    dataset_id: str = Field(..., description="Dataset identifier")
    numeric_columns: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Statistics for numeric columns (mean, std, min, max, etc.)"
    )
    categorical_columns: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Statistics for categorical columns (value_counts, etc.)"
    )
    missing_data: dict[str, int] = Field(
        default_factory=dict,
        description="Count of missing values per column"
    )
    data_types: dict[str, str] = Field(
        default_factory=dict,
        description="Data type for each column"
    )


class DatasetListResponse(BaseModel):
    """Response for listing datasets."""
    datasets: list[DatasetInfo] = Field(..., description="List of datasets")
    total_count: int = Field(..., description="Total number of datasets")
    has_more: bool = Field(..., description="Whether there are more datasets")


class TableSchema(BaseModel):
    """Database table schema information."""
    table_name: str = Field(..., description="Table name")
    schema_name: str = Field("public", description="Schema name")
    columns: list[ColumnInfo] = Field(..., description="Column definitions")
    primary_key: list[str] | None = Field(None, description="Primary key columns")
    foreign_keys: list[dict[str, Any]] | None = Field(None, description="Foreign key relationships")
    indexes: list[str] | None = Field(None, description="Index names")
