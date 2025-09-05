"""
Unified ETL Models
統一的 ETL 系統數據模型，遵循 CLAUDE.md 的 snake_case 命名規範
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FileUploadStatus(str, Enum):
    """文件上傳狀態枚舉"""
    PENDING = "pending"
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    READY = "ready"
    ERROR = "error"


class ValidationStatus(str, Enum):
    """驗證狀態枚舉"""
    PENDING = "pending"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"


class ETLJobStatus(str, Enum):
    """ETL 作業狀態枚舉"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IssueLevel(str, Enum):
    """問題嚴重性等級"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """驗證問題詳情"""
    type: str = Field(..., description="問題類型")
    level: IssueLevel = Field(..., description="嚴重性等級")
    message: str = Field(..., description="問題描述")
    column: str | None = Field(None, description="相關欄位")
    row_number: int | None = Field(None, description="相關行號")
    suggestion: str | None = Field(None, description="修復建議")


class SheetValidationResult(BaseModel):
    """工作表驗證結果"""
    sheet_name: str = Field(..., description="工作表名稱")
    is_valid: bool = Field(..., description="是否通過驗證")
    total_rows: int = Field(..., description="總行數")
    valid_rows: int = Field(..., description="有效行數")
    issues: list[ValidationIssue] = Field(default_factory=list, description="發現的問題")
    data_summary: dict[str, Any] = Field(default_factory=dict, description="數據摘要")


class SheetInfo(BaseModel):
    """工作表基本資訊"""
    sheet_name: str = Field(..., description="工作表名稱")
    row_count: int = Field(..., description="行數")
    column_count: int = Field(..., description="列數")
    columns: list[str] = Field(..., description="欄位名稱列表")
    sample_data: list[dict[str, Any]] = Field(default_factory=list, description="樣本數據")
    validation_result: SheetValidationResult | None = Field(None, description="驗證結果")


class FileUploadProgress(BaseModel):
    """文件上傳進度"""
    stage: str = Field(..., description="當前階段")
    progress: int = Field(..., description="進度百分比 (0-100)")
    message: str = Field(..., description="進度描述")
    details: dict[str, Any] = Field(default_factory=dict, description="額外詳情")


class UnifiedFileUploadResponse(BaseModel):
    """統一的文件上傳響應格式"""
    # 基本資訊
    file_id: str = Field(..., description="文件唯一識別符")
    filename: str = Field(..., description="原始檔名")
    file_size: int = Field(..., description="檔案大小 (bytes)")
    country: str = Field(..., description="國家代碼")

    # 狀態資訊
    status: FileUploadStatus = Field(..., description="上傳狀態")
    progress: FileUploadProgress | None = Field(None, description="進度資訊")

    # 時間戳記
    uploaded_at: datetime = Field(..., description="上傳時間")
    analyzed_at: datetime | None = Field(None, description="分析完成時間")

    # 工作表資訊
    sheets: list[SheetInfo] = Field(default_factory=list, description="工作表列表")
    total_sheets: int = Field(0, description="工作表總數")

    # 驗證資訊
    validation_summary: dict[str, Any] = Field(default_factory=dict, description="整體驗證摘要")

    # 錯誤處理
    error: str | None = Field(None, description="錯誤信息")
    error_code: str | None = Field(None, description="錯誤代碼")


class ETLJobInfo(BaseModel):
    """ETL 作業資訊"""
    job_id: UUID = Field(..., description="作業 ID")
    file_id: str = Field(..., description="關聯的文件 ID")
    sheet_name: str = Field(..., description="處理的工作表")

    # 狀態資訊
    status: ETLJobStatus = Field(..., description="作業狀態")
    progress: int = Field(0, description="進度百分比")

    # 處理統計
    total_records: int = Field(0, description="總記錄數")
    processed_records: int = Field(0, description="已處理記錄數")
    successful_records: int = Field(0, description="成功記錄數")
    failed_records: int = Field(0, description="失敗記錄數")

    # 時間戳記
    created_at: datetime = Field(..., description="創建時間")
    started_at: datetime | None = Field(None, description="開始時間")
    completed_at: datetime | None = Field(None, description="完成時間")

    # 處理選項
    target_date: str | None = Field(None, description="目標處理日期")
    overwrite_existing: bool = Field(False, description="是否覆蓋現有數據")

    # 錯誤處理
    error_message: str | None = Field(None, description="錯誤信息")
    error_details: dict[str, Any] = Field(default_factory=dict, description="錯誤詳情")


class FileUploadRequest(BaseModel):
    """文件上傳請求"""
    country: str = Field(..., description="國家代碼")
    auto_analyze: bool = Field(True, description="是否自動分析")
    validate_sheets: bool = Field(True, description="是否驗證工作表")
    target_date: str | None = Field(None, description="目標處理日期")


class SheetProcessingRequest(BaseModel):
    """工作表處理請求"""
    sheet_names: list[str] = Field(..., description="要處理的工作表名稱")
    target_date: str = Field(..., description="目標處理日期")
    overwrite_existing: bool = Field(False, description="是否覆蓋現有數據")
    validate_before_processing: bool = Field(True, description="處理前是否驗證")


# 響應包裝器
class APIResponse[T](BaseModel):
    """統一的 API 響應包裝器"""
    success: bool = Field(..., description="是否成功")
    data: T | None = Field(None, description="響應數據")
    message: str = Field("", description="響應信息")
    error_code: str | None = Field(None, description="錯誤代碼")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="響應時間戳")
