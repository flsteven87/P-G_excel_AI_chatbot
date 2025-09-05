"""
Unified ETL Service
統一的 ETL 業務服務，遵循 CLAUDE.md 的 4 層架構設計
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.models.unified_etl import (
    ETLJobInfo,
    ETLJobStatus,
    FileUploadProgress,
    FileUploadStatus,
    IssueLevel,
    SheetInfo,
    SheetProcessingRequest,
    SheetValidationResult,
    UnifiedFileUploadResponse,
    ValidationIssue,
)
from app.repositories.file_repository import FileRepository
from app.services.file_service import file_service

logger = logging.getLogger(__name__)


class UnifiedETLService:
    """
    統一的 ETL 業務服務

    職責：
    - 統一文件上傳和分析流程
    - 工作表驗證和處理
    - ETL 作業管理
    - 業務邏輯協調
    """

    def __init__(self):
        self._file_repo = FileRepository()
        self._storage_service = file_service

    async def upload_and_analyze_file(
        self,
        upload_file: UploadFile,
        country: str,
        auto_analyze: bool = True
    ) -> UnifiedFileUploadResponse:
        """
        統一的文件上傳和分析流程

        Args:
            upload_file: 上傳的文件
            country: 國家代碼
            auto_analyze: 是否自動分析工作表

        Returns:
            UnifiedFileUploadResponse: 統一的響應格式
        """
        try:
            # 生成文件 ID
            file_id = str(uuid4())

            logger.info(f"開始處理文件上傳: {upload_file.filename}, 國家: {country}")

            # 初始響應
            response = UnifiedFileUploadResponse(
                file_id=file_id,
                filename=upload_file.filename or "unknown",
                file_size=0,  # 暫時設為 0，稍後更新
                country=country,
                status=FileUploadStatus.UPLOADING,
                uploaded_at=datetime.utcnow(),
                progress=FileUploadProgress(
                    stage="uploading",
                    progress=10,
                    message="正在上傳文件..."
                )
            )

            # 1. 儲存文件
            storage_result = await self._storage_service.save_upload_file(upload_file)
            response.file_size = storage_result["file_size"]

            # 2. 創建資料庫記錄
            await self._file_repo.create_file_record(
                filename=storage_result["stored_filename"],
                original_filename=storage_result["original_filename"],
                country=country,
                file_size=storage_result["file_size"],
                file_path=storage_result["file_path"]
            )

            # 更新響應狀態
            response.status = FileUploadStatus.ANALYZING
            response.progress = FileUploadProgress(
                stage="analyzing",
                progress=50,
                message="正在分析工作表結構..."
            )

            # 3. 自動分析工作表（如果啟用）
            if auto_analyze:
                sheets = await self._analyze_excel_sheets(storage_result["file_path"])
                response.sheets = sheets
                response.total_sheets = len(sheets)
                response.analyzed_at = datetime.utcnow()

            # 4. 最終狀態
            response.status = FileUploadStatus.READY
            response.progress = FileUploadProgress(
                stage="completed",
                progress=100,
                message=f"文件處理完成，發現 {len(response.sheets)} 個工作表"
            )

            logger.info(f"文件處理成功: {file_id}")
            return response

        except Exception as e:
            logger.error(f"文件處理失敗: {e}")
            # Reason: 返回錯誤狀態而不是拋出異常，提供更好的用戶體驗
            return UnifiedFileUploadResponse(
                file_id=file_id,
                filename=upload_file.filename or "unknown",
                file_size=0,
                country=country,
                status=FileUploadStatus.ERROR,
                uploaded_at=datetime.utcnow(),
                error=str(e),
                error_code="UPLOAD_FAILED"
            )

    async def validate_sheets(
        self,
        file_id: str,
        sheet_names: list[str]
    ) -> dict[str, SheetValidationResult]:
        """
        驗證指定的工作表

        Args:
            file_id: 文件 ID
            sheet_names: 要驗證的工作表名稱列表

        Returns:
            dict[str, SheetValidationResult]: 驗證結果映射
        """
        try:
            logger.info(f"開始驗證工作表: {file_id}, 工作表: {sheet_names}")

            # 1. 獲取文件資訊
            file_info = await self._file_repo.get_file_by_id(file_id)
            if not file_info:
                raise ValueError(f"找不到文件: {file_id}")

            # 2. 讀取和驗證每個工作表
            results = {}
            file_path = self._get_full_file_path(file_info.file_path or file_info.filename)

            for sheet_name in sheet_names:
                try:
                    result = await self._validate_single_sheet(file_path, sheet_name)
                    results[sheet_name] = result
                    logger.info(f"工作表驗證完成: {sheet_name}, 有效: {result.is_valid}")
                except Exception as e:
                    logger.error(f"驗證工作表 {sheet_name} 失敗: {e}")
                    results[sheet_name] = SheetValidationResult(
                        sheet_name=sheet_name,
                        is_valid=False,
                        total_rows=0,
                        valid_rows=0,
                        issues=[ValidationIssue(
                            type="validation_error",
                            level=IssueLevel.ERROR,
                            message=f"工作表驗證失敗: {str(e)}"
                        )]
                    )

            return results

        except Exception as e:
            logger.error(f"工作表驗證失敗: {e}")
            raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}") from e

    async def process_sheets(
        self,
        file_id: str,
        request: SheetProcessingRequest
    ) -> list[ETLJobInfo]:
        """
        處理工作表數據到數據庫

        Args:
            file_id: 文件 ID
            request: 處理請求

        Returns:
            list[ETLJobInfo]: ETL 作業信息列表
        """
        try:
            logger.info(f"開始處理工作表: {file_id}, 工作表: {request.sheet_names}")

            jobs = []
            for sheet_name in request.sheet_names:
                job = ETLJobInfo(
                    job_id=uuid4(),
                    file_id=file_id,
                    sheet_name=sheet_name,
                    status=ETLJobStatus.PENDING,
                    created_at=datetime.utcnow(),
                    target_date=request.target_date,
                    overwrite_existing=request.overwrite_existing
                )

                # TODO: 實際的 ETL 處理邏輯
                # 這裡應該調用實際的 ETL 處理服務
                job.status = ETLJobStatus.PROCESSING
                job.started_at = datetime.utcnow()

                jobs.append(job)
                logger.info(f"ETL 作業已創建: {job.job_id}")

            return jobs

        except Exception as e:
            logger.error(f"工作表處理失敗: {e}")
            raise HTTPException(status_code=500, detail=f"處理失敗: {str(e)}") from e

    async def _analyze_excel_sheets(self, file_path: str) -> list[SheetInfo]:
        """
        分析 Excel 文件的工作表結構

        Args:
            file_path: 文件路徑

        Returns:
            list[SheetInfo]: 工作表資訊列表
        """
        try:
            full_path = self._get_full_file_path(file_path)

            # 讀取 Excel 文件
            excel_file = pd.ExcelFile(str(full_path))
            sheets = []

            for sheet_name in excel_file.sheet_names:
                # 讀取工作表樣本數據
                df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=5)

                # 生成樣本數據（處理 NaN 值）
                sample_data = []
                if not df.empty:
                    df_sample = df.head(3)
                    for _, row in df_sample.iterrows():
                        row_dict = {}
                        for col, value in row.items():
                            row_dict[col] = None if pd.isna(value) else self._convert_value(value)
                        sample_data.append(row_dict)

                # 創建工作表資訊
                sheet_info = SheetInfo(
                    sheet_name=sheet_name,
                    row_count=len(pd.read_excel(excel_file, sheet_name=sheet_name)),
                    column_count=len(df.columns),
                    columns=df.columns.tolist(),
                    sample_data=sample_data
                )
                sheets.append(sheet_info)

            return sheets

        except Exception as e:
            logger.error(f"分析 Excel 文件失敗: {e}")
            raise

    async def _validate_single_sheet(
        self,
        file_path: Path,
        sheet_name: str
    ) -> SheetValidationResult:
        """
        驗證單個工作表

        Args:
            file_path: 文件路徑
            sheet_name: 工作表名稱

        Returns:
            SheetValidationResult: 驗證結果
        """
        try:
            # 讀取工作表數據
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # 基本驗證邏輯
            issues = []
            total_rows = len(df)
            valid_rows = total_rows  # 簡化：暫時假設所有行都有效

            # 檢查必要欄位（示例）
            required_columns = ["Sku", "Qty"]  # 可配置
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                issues.append(ValidationIssue(
                    type="missing_columns",
                    level=IssueLevel.ERROR,
                    message=f"缺少必要欄位: {', '.join(missing_columns)}",
                    suggestion="請確保工作表包含所有必要欄位"
                ))

            # 檢查數據品質
            if "Qty" in df.columns:
                negative_qty = df[df["Qty"] < 0]
                if len(negative_qty) > 0:
                    issues.append(ValidationIssue(
                        type="negative_quantity",
                        level=IssueLevel.WARNING,
                        message=f"發現 {len(negative_qty)} 行負數數量",
                        column="Qty",
                        suggestion="請檢查數量數據的正確性"
                    ))

            # 生成數據摘要
            data_summary = {
                "total_rows": total_rows,
                "columns": len(df.columns),
                "has_required_fields": len(missing_columns) == 0,
                "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }

            if "Sku" in df.columns:
                data_summary["unique_skus"] = df["Sku"].nunique()

            return SheetValidationResult(
                sheet_name=sheet_name,
                is_valid=len([issue for issue in issues if issue.level == IssueLevel.ERROR]) == 0,
                total_rows=total_rows,
                valid_rows=valid_rows,
                issues=issues,
                data_summary=data_summary
            )

        except Exception as e:
            logger.error(f"驗證工作表 {sheet_name} 失敗: {e}")
            raise

    def _get_full_file_path(self, file_path: str) -> Path:
        """
        獲取完整的文件路徑

        Args:
            file_path: 相對文件路徑

        Returns:
            Path: 完整路徑
        """
        full_path = Path("uploads") / "inventory" / file_path
        if not full_path.exists():
            full_path = Path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"找不到文件: {file_path}")

        return full_path

    def _convert_value(self, value: Any) -> Any:
        """
        轉換值為可序列化的類型

        Args:
            value: 原始值

        Returns:
            Any: 轉換後的值
        """
        # 處理 pandas/numpy 類型
        if pd.isna(value):
            return None

        # 處理數值類型
        if hasattr(value, 'item'):  # numpy 類型
            return value.item()

        return value


# 創建服務實例
unified_etl_service = UnifiedETLService()
