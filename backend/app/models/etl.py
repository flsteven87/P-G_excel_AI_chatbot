"""
ETL 相關的資料模型
定義檔案上傳、處理狀態和驗證相關的 Pydantic 模型
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ETLJobStatus(str, Enum):
    """ETL 工作狀態枚舉"""
    PENDING = "pending"
    PROCESSING = "processing"
    VALIDATING = "validating"
    LOADING = "loading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataQualityIssueType(str, Enum):
    """資料品質問題類型"""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATE_FORMAT = "invalid_date_format"
    NEGATIVE_QUANTITY = "negative_quantity"
    OVER_ALLOCATION = "over_allocation"
    DUPLICATE_RECORD = "duplicate_record"
    INVALID_SKU_FORMAT = "invalid_sku_format"
    INVALID_FACILITY_CODE = "invalid_facility_code"


class FileUploadRequest(BaseModel):
    """檔案上傳請求"""
    filename: str = Field(..., description="檔案名稱")
    content_type: str = Field(..., description="檔案內容類型")
    file_size: int = Field(..., description="檔案大小 (bytes)")

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        allowed_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv'
        ]
        if v not in allowed_types:
            raise ValueError(f'不支援的檔案類型: {v}')
        return v


class ETLJobCreate(BaseModel):
    """建立 ETL 工作請求"""
    source_file: str = Field(..., description="來源檔案名稱")
    sheet_name: str | None = Field(None, description="Excel Sheet 名稱")
    target_date: str | None = Field(None, description="目標快照日期 (YYYY-MM-DD)")
    overwrite_existing: bool = Field(False, description="是否覆蓋現有資料")
    validate_only: bool = Field(False, description="僅驗證不載入")

    @field_validator('target_date')
    @classmethod
    def validate_target_date(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError as e:
                raise ValueError('日期格式必須為 YYYY-MM-DD') from e
        return v


class DataQualityIssue(BaseModel):
    """資料品質問題"""
    type: str = Field(..., description="問題類型")  # 匹配前端期望
    message: str = Field(..., description="問題描述")
    column: str | None = Field(None, description="問題欄位名稱")  # 匹配前端期望
    row_number: int | None = Field(None, description="問題行號")
    # Additional fields for internal use
    issue_type: DataQualityIssueType | None = Field(None, description="內部問題類型")
    severity: str | None = Field(None, description="嚴重性: error, warning, info")
    current_value: str | None = Field(None, description="目前值")
    expected_value: str | None = Field(None, description="期望值")


class ETLValidationResult(BaseModel):
    """ETL 驗證結果"""
    is_valid: bool = Field(..., description="是否通過驗證")
    total_records: int = Field(..., description="總記錄數")  # 匹配前端期望
    valid_rows: int = Field(..., description="有效行數")
    error_count: int = Field(..., description="錯誤數量")
    warning_count: int = Field(..., description="警告數量")
    issues: list[DataQualityIssue] = Field(default_factory=list, description="品質問題列表")
    data_summary: dict[str, Any] = Field(default_factory=dict, description="資料摘要")


class ETLJobResponse(BaseModel):
    """ETL 工作回應"""
    job_id: UUID = Field(default_factory=uuid4, description="工作 ID")
    status: ETLJobStatus = Field(default=ETLJobStatus.PENDING, description="工作狀態")
    source_file: str = Field(..., description="來源檔案")
    sheet_name: str | None = Field(None, description="Sheet 名稱")
    target_date: str | None = Field(None, description="目標日期")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    started_at: datetime | None = Field(None, description="開始時間")
    completed_at: datetime | None = Field(None, description="完成時間")
    error_message: str | None = Field(None, description="錯誤訊息")
    validation_result: ETLValidationResult | None = Field(None, description="驗證結果")

    # 統計資訊
    rows_processed: int = Field(default=0, description="已處理行數")
    rows_inserted: int = Field(default=0, description="已插入行數")
    rows_updated: int = Field(default=0, description="已更新行數")
    rows_skipped: int = Field(default=0, description="已跳過行數")


class ETLProgressUpdate(BaseModel):
    """ETL 進度更新"""
    job_id: UUID
    status: ETLJobStatus
    progress_percentage: float = Field(..., ge=0, le=100, description="進度百分比")
    current_step: str = Field(..., description="目前步驟")
    message: str | None = Field(None, description="狀態訊息")
    updated_at: datetime = Field(default_factory=datetime.now)


class InventoryDataRow(BaseModel):
    """庫存資料行模型 - 用於驗證和轉換"""
    # 基本欄位
    date: str = Field(..., description="快照日期")
    sku: str = Field(..., description="產品代碼")
    descr: str | None = Field(None, description="產品描述")
    brand: str | None = Field(None, description="品牌")
    skugroup: str | None = Field(None, description="產品群組")

    # 地點相關
    facility: str = Field(..., description="倉庫代碼")
    loc: str = Field(..., description="庫位")
    sloc: str | None = Field(None, description="子庫位")

    # 數量相關
    qty: int = Field(..., ge=0, description="庫存數量")
    bqty: float = Field(..., ge=0, description="B數量")
    qty_allocated: int = Field(..., ge=0, description="已配置數量")
    case_cnt: int = Field(..., ge=0, description="箱數")
    buom: str | None = Field(None, description="基本單位")

    # 批號相關
    wms_lot: str | None = Field(None, description="WMS 批號")
    manf_date: str | None = Field(None, description="製造日期")
    receipt_date: str | None = Field(None, description="入庫日期")
    dc_stop_ship_date: str | None = Field(None, description="停出貨日期")
    shelf_life_days: int | None = Field(None, description="保存期限天數")
    stop_ship_lead_days: int | None = Field(None, description="停出貨提前天數")

    # 其他欄位
    ean: str | None = Field(None, description="EAN 條碼")
    itf14: str | None = Field(None, description="ITF14 條碼")
    reason: str | None = Field(None, description="原因")
    remark: str | None = Field(None, description="備註")
    source_row_key: str | None = Field(None, description="來源行鍵")

    @field_validator('qty_allocated')
    @classmethod
    def validate_allocation(cls, v, info: ValidationInfo):
        """驗證配置量不能超過庫存量"""
        if info.data and 'qty' in info.data and v and info.data['qty'] and v > info.data['qty']:
            raise ValueError(f'配置量 ({v}) 不能超過庫存量 ({info.data["qty"]})')
        return v


# File Management Models for Multi-Step Upload Flow

class SheetInfo(BaseModel):
    """工作表資訊 - 增強容錯版"""
    sheet_name: str = Field(..., description="工作表名稱")
    row_count: int = Field(default=0, description="行數")  # ✅ 添加預設值
    column_count: int = Field(default=0, description="欄位數")  # ✅ 添加預設值
    columns: list[str] = Field(default_factory=list, description="欄位名稱列表")  # ✅ 添加預設值
    sample_data: list[dict[str, Any]] | None = Field(None, description="樣本資料")
    validation_status: str = Field(default="pending", description="驗證狀態")
    validation_result: "ETLValidationResult | None" = Field(None, description="驗證結果")
    etl_status: str = Field(default="not_loaded", description="ETL 狀態")
    etl_job_id: str | None = Field(None, description="ETL 工作 ID")
    loaded_at: datetime | None = Field(None, description="載入時間")

    @field_validator('row_count', 'column_count', mode='before')
    @classmethod
    def ensure_non_negative_int(cls, v):
        """確保行數和欄位數為非負整數"""
        if v is None:
            return 0
        try:
            result = int(v)
            return max(0, result)  # 確保非負
        except (ValueError, TypeError):
            return 0


class UploadedFileInfo(BaseModel):
    """已上傳檔案資訊"""
    file_id: str = Field(..., description="檔案 ID")
    filename: str = Field(..., description="儲存檔案名稱（含時間戳）")
    original_filename: str = Field(..., description="原始檔案名稱")
    file_path: str | None = Field(None, description="檔案路徑")
    country: str = Field(..., description="國家代碼")
    file_size: int = Field(..., description="檔案大小")
    status: str = Field(default="uploaded", description="檔案狀態")
    upload_date: str = Field(..., description="上傳時間")
    sheets: list[SheetInfo] = Field(default_factory=list, description="工作表列表")


class FileAnalysisResult(BaseModel):
    """檔案分析結果"""
    file_id: str = Field(..., description="檔案 ID")
    sheets: list[SheetInfo] = Field(..., description="工作表資訊")
    analysis_completed_at: datetime = Field(default_factory=datetime.now, description="分析完成時間")


class SheetValidationRequest(BaseModel):
    """Sheet 驗證請求"""
    sheet_names: list[str] = Field(..., description="要驗證的工作表名稱列表")


class ConfirmUploadRequest(BaseModel):
    """確認上傳請求"""
    target_date: str | None = Field(None, description="目標日期 YYYY-MM-DD")


class ProcessSheetRequest(BaseModel):
    """處理 Sheet 請求"""
    target_date: str = Field(..., description="目標日期 YYYY-MM-DD")


class ETLStatistics(BaseModel):
    """ETL 統計資訊"""
    total_files_processed: int = Field(default=0, description="已處理檔案總數")
    total_rows_processed: int = Field(default=0, description="已處理行數總計")
    success_rate: float = Field(default=0.0, description="成功率")
    average_processing_time: float = Field(default=0.0, description="平均處理時間(秒)")
    last_successful_job: datetime | None = Field(None, description="最後成功工作時間")
    common_issues: dict[str, int] = Field(default_factory=dict, description="常見問題統計")
