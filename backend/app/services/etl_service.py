"""
ETL Service Layer
處理 ETL 業務邏輯，包含檔案處理、資料驗證、轉換和載入
"""
import asyncio
import io
import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

import pandas as pd

from app.models.etl import (
    DataQualityIssue,
    DataQualityIssueType,
    ETLJobResponse,
    ETLJobStatus,
    ETLValidationResult,
)
from app.repositories.etl_repository import ETLJobRepository, InventoryRepository
from app.utils.serialization import (
    safe_count,
    safe_nunique,
    safe_tolist,
)

logger = logging.getLogger(__name__)


class ETLValidationService:
    """資料驗證服務 - 調整為適合實際業務需求"""

    def __init__(self):
        # ✅ 只保留真正必要的欄位，Brand 和 REASON 允許為空
        self.required_columns = ['Date', 'Sku', 'Facility', 'Loc', 'Qty']
        # ✅ 包含所有數值欄位，允許負值（如 Remaining month）
        self.numeric_columns = ['Qty', 'BQty', 'QtyAllocated', 'CaseCnt', 'WMS Lot', 'Shelflife', 'Stop Ship Lead time']
        self.date_columns = ['Date', 'Manf_Date', 'Expiry', 'DC Stop Ship Date']
        # ✅ 可選欄位，允許為空值
        self.optional_columns = ['Brand', 'REASON', 'Lottable09']

    def validate_dataframe(self, df: pd.DataFrame, sheet_name: str = None) -> ETLValidationResult:
        """驗證 DataFrame 資料品質"""
        try:
            issues = []

            # 1. 檢查必要欄位
            issues.extend(self._validate_required_columns(df))

            # 2. 檢查資料類型和格式
            issues.extend(self._validate_data_types(df))

            # 3. 檢查日期格式
            issues.extend(self._validate_dates(df))

            # 4. 檢查業務邏輯
            issues.extend(self._validate_business_logic(df))

            # 5. 檢查重複記錄
            issues.extend(self._validate_duplicates(df))

            # 統計結果
            error_count = len([i for i in issues if i.severity == 'error'])
            warning_count = len([i for i in issues if i.severity == 'warning'])
            valid_rows = len(df) - len({i.row_number for i in issues if i.severity == 'error'})

            # 生成資料摘要
            data_summary = self._generate_data_summary(df, sheet_name)

            return ETLValidationResult(
                is_valid=error_count == 0,
                total_records=len(df),  # 正確使用 total_records 欄位
                valid_rows=max(0, valid_rows),
                error_count=error_count,
                warning_count=warning_count,
                issues=issues,
                data_summary=data_summary
            )

        except Exception as e:
            logger.error(f"資料驗證失敗: {e}")
            return ETLValidationResult(
                is_valid=False,
                total_records=len(df) if df is not None else 0,  # 正確使用 total_records 欄位
                valid_rows=0,
                error_count=1,
                warning_count=0,
                issues=[DataQualityIssue(
                    type="missing_required_field",  # 匹配前端期望
                    message=f"驗證過程發生錯誤: {str(e)}",
                    row_number=0,
                    issue_type=DataQualityIssueType.MISSING_REQUIRED_FIELD,
                    severity="error"
                )],
                data_summary={}
            )

    def _validate_required_columns(self, df: pd.DataFrame) -> list[DataQualityIssue]:
        """檢查必要欄位 - 只檢查真正關鍵的欄位"""
        issues = []

        # 檢查欄位是否存在
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        for col in missing_columns:
            issues.append(DataQualityIssue(
                type="missing_required_field",
                message=f"缺少必要欄位: {col}",
                column=col,
                row_number=0,
                issue_type=DataQualityIssueType.MISSING_REQUIRED_FIELD,
                severity="error"
            ))

        # ✅ 只檢查真正關鍵欄位的空值，排除允許為空的欄位
        for col in self.required_columns:
            if col in df.columns:
                # 對於字串欄位，檢查是否為空字串或空值
                if col in ['Date', 'Facility', 'Loc']:
                    empty_rows = df[(df[col].isnull()) | (df[col].astype(str).str.strip() == '')].index.tolist()
                else:
                    # 對於數值欄位，只檢查 null
                    empty_rows = df[df[col].isnull()].index.tolist()

                # ✅ 限制報告的錯誤數量，避免過多警告
                for row_idx in empty_rows[:10]:  # 只報告前10個
                    issues.append(DataQualityIssue(
                        type="missing_required_field",
                        message=f"必要欄位 {col} 為空值",
                        column=col,
                        row_number=row_idx + 1,
                        issue_type=DataQualityIssueType.MISSING_REQUIRED_FIELD,
                        severity="error"
                    ))

                if len(empty_rows) > 10:
                    issues.append(DataQualityIssue(
                        type="missing_required_field",
                        message=f"欄位 {col} 還有額外 {len(empty_rows) - 10} 筆空值記錄",
                        column=col,
                        row_number=0,
                        issue_type=DataQualityIssueType.MISSING_REQUIRED_FIELD,
                        severity="warning"
                    ))

        return issues

    def _validate_data_types(self, df: pd.DataFrame) -> list[DataQualityIssue]:
        """檢查資料類型 - 放寬限制，適合業務需求"""
        issues = []

        for col in self.numeric_columns:
            if col in df.columns:
                non_numeric_rows = []
                negative_count = 0

                for idx, value in df[col].items():
                    if pd.notna(value):
                        try:
                            float_val = float(str(value).replace(',', ''))
                            # ✅ 只有庫存相關欄位不允許負值，其他欄位（如 Remaining month）允許負值
                            if col in ['Qty', 'BQty', 'QtyAllocated', 'CaseCnt'] and float_val < 0:
                                negative_count += 1
                                if negative_count <= 5:  # 只報告前5個負值
                                    issues.append(DataQualityIssue(
                                        type="negative_quantity",
                                        message=f"{col} 為負值: {value} (行 {idx + 1})",
                                        column=col,
                                        row_number=idx + 1,
                                        issue_type=DataQualityIssueType.NEGATIVE_QUANTITY,
                                        severity="warning",  # ✅ 改為警告而非錯誤
                                        current_value=str(value)
                                    ))
                        except (ValueError, TypeError):
                            non_numeric_rows.append((idx, value))

                # ✅ 限制報告非數值錯誤的數量
                for idx, value in non_numeric_rows[:5]:  # 只報告前5個
                    issues.append(DataQualityIssue(
                        type="invalid_data_format",
                        message=f"{col} 包含非數值資料: {value}",
                        column=col,
                        row_number=idx + 1,
                        issue_type=DataQualityIssueType.INVALID_SKU_FORMAT,
                        severity="error",
                        current_value=str(value)
                    ))

                # 批量報告剩餘問題
                if len(non_numeric_rows) > 5:
                    issues.append(DataQualityIssue(
                        type="invalid_data_format",
                        message=f"{col} 還有額外 {len(non_numeric_rows) - 5} 筆非數值資料",
                        column=col,
                        row_number=0,
                        issue_type=DataQualityIssueType.INVALID_SKU_FORMAT,
                        severity="warning"
                    ))

                if negative_count > 5:
                    issues.append(DataQualityIssue(
                        type="negative_quantity",
                        message=f"{col} 還有額外 {negative_count - 5} 筆負值記錄",
                        column=col,
                        row_number=0,
                        issue_type=DataQualityIssueType.NEGATIVE_QUANTITY,
                        severity="warning"
                    ))

        return issues

    def _validate_dates(self, df: pd.DataFrame) -> list[DataQualityIssue]:
        """檢查日期格式"""
        issues = []

        for col in self.date_columns:
            if col in df.columns:
                for idx, value in df[col].items():
                    if pd.notna(value) and str(value).strip():
                        try:
                            if col == 'Receipt Date':
                                # 處理 Receipt Date 的特殊格式 (YYYYMMDD)
                                date_str = str(value).strip()
                                if len(date_str) >= 8 and date_str[:8].isdigit():
                                    pd.to_datetime(date_str[:8], format='%Y%m%d')
                                else:
                                    raise ValueError("Invalid receipt date format")
                            else:
                                # 標準日期格式
                                pd.to_datetime(str(value).strip(), format='%Y/%m/%d')
                        except (ValueError, TypeError):
                            issues.append(DataQualityIssue(
                                type="invalid_date_format",
                                message=f"{col} 日期格式不正確: {value}",
                                column=col,
                                row_number=idx + 1,
                                issue_type=DataQualityIssueType.INVALID_DATE_FORMAT,
                                severity="warning",
                                current_value=str(value)
                            ))

        return issues

    def _validate_business_logic(self, df: pd.DataFrame) -> list[DataQualityIssue]:
        """檢查業務邏輯"""
        issues = []

        # 檢查配置量不能超過庫存量
        if 'Qty' in df.columns and 'QtyAllocated' in df.columns:
            for idx, row in df.iterrows():
                try:
                    qty = float(str(row['Qty']).replace(',', '')) if pd.notna(row['Qty']) else 0
                    qty_allocated = float(str(row['QtyAllocated']).replace(',', '')) if pd.notna(row['QtyAllocated']) else 0

                    if qty_allocated > qty:
                        issues.append(DataQualityIssue(
                            type="over_allocation",
                            message=f"配置量 ({qty_allocated}) 超過庫存量 ({qty})",
                            column="QtyAllocated",
                            row_number=idx + 1,
                            issue_type=DataQualityIssueType.OVER_ALLOCATION,
                            severity="error",
                            current_value=f"Allocated: {qty_allocated}, Available: {qty}"
                        ))
                except (ValueError, TypeError):
                    continue

        return issues

    def _validate_duplicates(self, df: pd.DataFrame) -> list[DataQualityIssue]:
        """檢查重複記錄 - 更精確的重複檢查邏輯"""
        issues = []

        # ✅ 更精確的唯一性檢查：必須包含 WMS Lot 來區分不同批次
        key_columns = ['Date', 'Sku', 'Facility', 'Loc', 'SLOC', 'WMS Lot']
        available_columns = [col for col in key_columns if col in df.columns and col is not None]

        if len(available_columns) >= 4:  # 至少要有基本的4個欄位
            # 找出重複的記錄
            duplicated_rows = df.duplicated(subset=available_columns, keep=False)
            duplicate_indices = df[duplicated_rows].index.tolist()

            # ✅ 限制報告的重複記錄數量
            reported_duplicates = 0
            for idx in duplicate_indices:
                if reported_duplicates < 10:  # 只報告前10個
                    issues.append(DataQualityIssue(
                        type="duplicate_record",
                        message=f"可能重複記錄 (基於: {', '.join(available_columns)})",
                        row_number=idx + 1,
                        issue_type=DataQualityIssueType.DUPLICATE_RECORD,
                        severity="info"  # ✅ 改為信息級別
                    ))
                    reported_duplicates += 1

            # 批量報告剩餘重複記錄
            if len(duplicate_indices) > 10:
                issues.append(DataQualityIssue(
                    type="duplicate_record",
                    message=f"總共發現 {len(duplicate_indices)} 筆可能重複的記錄",
                    row_number=0,
                    issue_type=DataQualityIssueType.DUPLICATE_RECORD,
                    severity="info"
                ))

        return issues

    def _generate_data_summary(self, df: pd.DataFrame, sheet_name: str = None) -> dict[str, Any]:
        """生成資料摘要（簡化版，確保序列化安全）"""
        try:
            summary = {
                "sheet_name": sheet_name or "Unknown",
                "total_rows": int(len(df)),
                "total_columns": int(len(df.columns)),
                "columns": list(df.columns),
            }

            # 基本統計資訊
            if not df.empty:
                # SKU 統計
                if 'Sku' in df.columns:
                    summary["unique_skus"] = safe_nunique(df['Sku'])
                    summary["sample_skus"] = safe_tolist(df['Sku'], 3)

                # 品牌統計
                if 'Brand' in df.columns:
                    summary["unique_brands"] = safe_nunique(df['Brand'])

                # 倉庫統計
                if 'Facility' in df.columns:
                    summary["unique_facilities"] = safe_nunique(df['Facility'])

                # 數量統計 (仅記錄數，不計算總和避免問題)
                if 'Qty' in df.columns:
                    summary["has_quantity_data"] = True
                    summary["qty_records"] = safe_count(df['Qty'])
                else:
                    summary["has_quantity_data"] = False

            return summary

        except Exception as e:
            logger.error(f"生成資料摘要失敗: {e}")
            return {
                "sheet_name": sheet_name or "Unknown",
                "total_rows": int(len(df)) if df is not None else 0,
                "total_columns": 0,
                "error": str(e)
            }


class ETLFileProcessor:
    """檔案處理服務"""

    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.max_file_size = 50 * 1024 * 1024  # 50MB

    async def process_excel_file(self, file_content: bytes, filename: str) -> dict[str, pd.DataFrame]:
        """處理 Excel 檔案，返回所有 sheet 的 DataFrame"""
        try:
            file_obj = io.BytesIO(file_content)

            # 讀取所有 sheet
            excel_file = pd.ExcelFile(file_obj, engine='openpyxl')
            dataframes = {}

            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_obj, sheet_name=sheet_name, engine='openpyxl')
                    if not df.empty:
                        dataframes[sheet_name] = df
                        logger.info(f"成功讀取 sheet '{sheet_name}': {len(df)} 筆資料")
                except Exception as sheet_error:
                    logger.error(f"讀取 sheet '{sheet_name}' 失敗: {sheet_error}")
                    continue

            return dataframes

        except Exception as e:
            logger.error(f"處理 Excel 檔案失敗: {e}")
            raise ValueError(f"無法處理 Excel 檔案: {str(e)}")

    async def process_csv_file(self, file_content: bytes, filename: str) -> dict[str, pd.DataFrame]:
        """處理 CSV 檔案"""
        try:
            file_obj = io.StringIO(file_content.decode('utf-8-sig'))
            df = pd.read_csv(file_obj)

            return {filename: df}

        except Exception as e:
            logger.error(f"處理 CSV 檔案失敗: {e}")
            raise ValueError(f"無法處理 CSV 檔案: {str(e)}")


class ETLService:
    """ETL 主服務類"""

    def __init__(self):
        self.validation_service = ETLValidationService()
        self.file_processor = ETLFileProcessor()
        self.job_repository = ETLJobRepository()
        self.inventory_repository = InventoryRepository()
        self.active_jobs: dict[str, ETLJobResponse] = {}

    async def create_etl_job(
        self,
        file_content: bytes,
        filename: str,
        sheet_name: str | None = None,
        target_date: str | None = None,
        validate_only: bool = False,
        file_id: str | None = None
    ) -> ETLJobResponse:
        """建立 ETL 工作"""
        try:
            job_id = str(uuid4())

            # 建立工作記錄
            job = ETLJobResponse(
                job_id=UUID(job_id),
                status=ETLJobStatus.PENDING,
                source_file=filename,
                sheet_name=sheet_name,
                target_date=target_date,
                created_at=datetime.now()
            )

            # 儲存 file_id 用於後續狀態更新 (透過 active_jobs 中的額外屬性)
            if file_id:
                self.active_jobs[f"{job_id}_file_id"] = file_id

            self.active_jobs[job_id] = job

            # 異步處理檔案
            asyncio.create_task(self._process_etl_job(job_id, file_content, validate_only))

            return job

        except Exception as e:
            logger.error(f"建立 ETL 工作失敗: {e}")
            raise

    async def _process_etl_job(self, job_id: str, file_content: bytes, validate_only: bool):
        """處理 ETL 工作的主流程"""
        job = self.active_jobs[job_id]

        try:
            # 1. 更新狀態為處理中
            job.status = ETLJobStatus.PROCESSING
            job.started_at = datetime.now()

            # 2. 處理檔案
            await self._update_progress(job_id, 10, "正在讀取檔案...")

            if job.source_file.endswith(('.xlsx', '.xls')):
                dataframes = await self.file_processor.process_excel_file(file_content, job.source_file)
            elif job.source_file.endswith('.csv'):
                dataframes = await self.file_processor.process_csv_file(file_content, job.source_file)
            else:
                raise ValueError(f"不支援的檔案格式: {job.source_file}")

            # 3. 選擇要處理的 sheet
            if job.sheet_name and job.sheet_name in dataframes:
                target_df = dataframes[job.sheet_name]
                sheet_name = job.sheet_name
            else:
                # 選擇第一個有資料的 sheet
                sheet_name, target_df = next(iter(dataframes.items()))
                job.sheet_name = sheet_name

            await self._update_progress(job_id, 20, f"正在驗證資料 (Sheet: {sheet_name})...")

            # 4. 驗證資料
            job.status = ETLJobStatus.VALIDATING
            validation_result = self.validation_service.validate_dataframe(target_df, sheet_name)
            job.validation_result = validation_result

            if not validation_result.is_valid:
                job.status = ETLJobStatus.FAILED
                job.error_message = f"資料驗證失敗: {validation_result.error_count} 個錯誤"
                job.completed_at = datetime.now()
                return

            # 5. 如果只是驗證，到此結束
            if validate_only:
                job.status = ETLJobStatus.COMPLETED
                job.completed_at = datetime.now()
                return

            # 6. 載入資料
            job.status = ETLJobStatus.LOADING
            await self._update_progress(job_id, 50, "正在載入資料到 staging...")

            # 轉換 DataFrame 為字典列表
            data_rows = target_df.to_dict('records')

            # 插入到 staging 表
            source_file_key = f"{job.source_file}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            staging_count = await self.inventory_repository.insert_staging_data(data_rows, source_file_key)
            job.rows_processed = staging_count

            await self._update_progress(job_id, 70, "正在處理維度資料...")

            # 處理維度表
            await self.inventory_repository.process_staging_to_dimensions(source_file_key)

            await self._update_progress(job_id, 85, "正在載入事實表...")

            # 處理事實表
            target_date_obj = datetime.strptime(job.target_date, '%Y-%m-%d').date() if job.target_date else date.today()
            fact_count = await self.inventory_repository.process_staging_to_facts(source_file_key, target_date_obj)
            job.rows_inserted = fact_count

            await self._update_progress(job_id, 95, "正在清理暫存資料...")

            # 清理 staging 資料
            await self.inventory_repository.cleanup_staging_data(source_file_key)

            # 7. 完成
            job.status = ETLJobStatus.COMPLETED
            job.completed_at = datetime.now()

            await self._update_progress(job_id, 100, "ETL 處理完成!")

            # 8. 更新檔案中的 Sheet 狀態
            await self._update_sheet_status(job_id, job.source_file, job.sheet_name, "loaded", job.completed_at)

        except Exception as e:
            logger.error(f"ETL 工作 {job_id} 處理失敗: {e}")
            job.status = ETLJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()

            # 更新 Sheet 狀態為失敗
            await self._update_sheet_status(job_id, job.source_file, job.sheet_name, "failed", job.completed_at)

    async def _update_progress(self, job_id: str, percentage: float, message: str):
        """更新處理進度"""
        if job_id in self.active_jobs:
            logger.info(f"ETL Job {job_id}: {percentage}% - {message}")
            # 這裡可以實作 WebSocket 或其他即時通知機制

    async def _update_sheet_status(self, job_id: str, source_file: str, sheet_name: str,
                                 etl_status: str, completed_at: datetime | None = None):
        """更新檔案中 Sheet 的 ETL 狀態"""
        try:
            from app.repositories.file_repository import FileRepository

            # 從 active_jobs 中取得 file_id
            file_id_key = f"{job_id}_file_id"
            file_id = self.active_jobs.get(file_id_key)

            if not file_id:
                logger.warning(f"無法找到 job {job_id} 對應的 file_id，跳過狀態更新")
                return

            file_repo = FileRepository()

            # 取得目前的檔案資料
            current_file = await file_repo.get_file_by_id(file_id)
            if not current_file:
                logger.warning(f"找不到檔案 {file_id}，無法更新 sheet 狀態")
                return

            # 更新對應的 sheet 狀態
            updated_sheets = []
            sheet_updated = False

            for sheet in current_file.sheets:
                if sheet.sheet_name == sheet_name:
                    # 更新這個 sheet 的 ETL 狀態
                    # 使用序列化安全的方式
                    from app.utils.serialization import convert_numpy_types

                    sheet_dict = sheet.model_dump()
                    sheet_dict['etl_status'] = etl_status
                    sheet_dict['etl_job_id'] = job_id
                    if completed_at:
                        sheet_dict['loaded_at'] = completed_at.isoformat()

                    # 確保所有值都是可序列化的
                    safe_sheet_dict = convert_numpy_types(sheet_dict)
                    updated_sheets.append(safe_sheet_dict)
                    sheet_updated = True
                    logger.info(f"將更新 sheet '{sheet_name}' 狀態: {sheet.etl_status} -> {etl_status}")
                else:
                    # 確保其他 sheets 也是序列化安全的
                    from app.utils.serialization import convert_numpy_types
                    safe_other_sheet = convert_numpy_types(sheet.model_dump())
                    updated_sheets.append(safe_other_sheet)

            if not sheet_updated:
                logger.warning(f"在檔案 {file_id} 中找不到 sheet '{sheet_name}'")
                return

            # 更新資料庫
            from app.models.etl import SheetInfo
            sheet_objects = [SheetInfo(**sheet_data) for sheet_data in updated_sheets]
            success = await file_repo.update_sheets_data(file_id, sheet_objects)

            if success:
                logger.info(f"✅ Sheet 狀態更新成功: {sheet_name} -> {etl_status}")
            else:
                logger.error(f"❌ Sheet 狀態更新失敗: {sheet_name}")

        except Exception as e:
            logger.error(f"更新 Sheet 狀態時發生異常: {e}")
            # 不拋出異常，避免影響主要的 ETL 流程

    async def get_job_status(self, job_id: str) -> ETLJobResponse | None:
        """取得工作狀態"""
        return self.active_jobs.get(job_id)

    async def list_active_jobs(self) -> list[ETLJobResponse]:
        """列出活躍的工作"""
        return list(self.active_jobs.values())

    async def cancel_job(self, job_id: str) -> bool:
        """取消工作"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in [ETLJobStatus.PENDING, ETLJobStatus.PROCESSING]:
                job.status = ETLJobStatus.CANCELLED
                job.completed_at = datetime.now()
                return True
        return False
