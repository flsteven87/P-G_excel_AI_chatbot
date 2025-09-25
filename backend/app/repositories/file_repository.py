"""
File Repository Layer
處理檔案管理相關的資料庫操作，遵循 Repository 模式
"""
import logging
from datetime import datetime
from typing import Any

from app.models.etl import SheetInfo, UploadedFileInfo
from app.repositories.supabase_base import SupabaseRepository

logger = logging.getLogger(__name__)


class FileRepository(SupabaseRepository):
    """檔案管理 Repository"""

    def __init__(self):
        super().__init__(table_name="uploaded_files", model_class=dict)

    async def create_file_record(
        self,
        filename: str,
        original_filename: str,
        country: str,
        file_size: int,
        file_path: str | None = None
    ) -> UploadedFileInfo:
        """創建檔案記錄"""
        try:
            file_data = {
                "filename": filename,
                "original_filename": original_filename,
                "country": country,
                "file_size": file_size,
                "file_path": file_path,
                "status": "uploaded",
                "upload_date": datetime.now().isoformat()
            }

            # ✅ Use base class method with proper error handling
            result = await super().create(file_data)

            return self._build_file_info(result)

        except Exception as e:
            logger.error(f"建立檔案記錄失敗: {e}")
            raise

    async def get_file_by_id(self, file_id: str) -> UploadedFileInfo | None:
        """取得檔案資訊"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("file_id", file_id)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result for all queries
            data = self._handle_supabase_result(result, allow_empty=True)

            if not data:
                return None

            # 取第一筆結果
            first_record = data[0] if isinstance(data, list) else data
            return self._build_file_info(first_record)

        except Exception as e:
            logger.error(f"取得檔案資訊失敗: {e}")
            raise

    async def list_all_files(self, limit: int = 100) -> list[UploadedFileInfo]:
        """列出所有檔案"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").order("upload_date", desc=True).limit(limit)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result for all queries
            data_list = self._handle_supabase_result(result, allow_empty=True)

            return [self._build_file_info(data) for data in data_list]

        except Exception as e:
            logger.error(f"列出檔案失敗: {e}")
            raise

    async def update_file_status(self, file_id: str, status: str, **kwargs) -> bool:
        """更新檔案狀態"""
        try:
            update_data = {"status": status, "updated_at": datetime.now().isoformat()}
            update_data.update(kwargs)

            client = await self.get_client()
            query = client.from_(self.table_name).update(update_data).eq("file_id", file_id)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result for all queries
            data = self._handle_supabase_result(result, allow_empty=True)
            return len(data) > 0 if isinstance(data, list) else data is not None

        except Exception as e:
            logger.error(f"更新檔案狀態失敗: {e}")
            raise

    async def update_sheets_data(self, file_id: str, sheets: list[SheetInfo]) -> bool:
        """更新工作表分析資料"""
        try:
            # ✅ 使用序列化安全的方式處理 SheetInfo
            from app.utils.serialization import convert_numpy_types

            sheets_data = []
            for sheet in sheets:
                # 先轉換為字典，然後進行序列化安全處理
                sheet_dict = sheet.model_dump()
                safe_sheet_dict = convert_numpy_types(sheet_dict)
                sheets_data.append(safe_sheet_dict)

            update_data = {
                "sheets_analyzed": True,
                "sheets_data": sheets_data,
                "status": "ready",
                "updated_at": datetime.now().isoformat()
            }

            client = await self.get_client()
            query = client.from_(self.table_name).update(update_data).eq("file_id", file_id)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result for all queries
            data = self._handle_supabase_result(result, allow_empty=True)
            return len(data) > 0 if isinstance(data, list) else data is not None

        except Exception as e:
            logger.error(f"更新工作表資料失敗: {e}")
            raise

    async def update_etl_jobs(self, file_id: str, etl_jobs: dict[str, Any]) -> bool:
        """更新 ETL 工作追蹤資料"""
        try:
            update_data = {
                "etl_jobs_data": etl_jobs,
                "updated_at": datetime.now().isoformat()
            }

            client = await self.get_client()
            query = client.from_(self.table_name).update(update_data).eq("file_id", file_id)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result for all queries
            data = self._handle_supabase_result(result, allow_empty=True)
            return len(data) > 0 if isinstance(data, list) else data is not None

        except Exception as e:
            logger.error(f"更新 ETL 工作追蹤失敗: {e}")
            raise

    def _build_file_info(self, data: dict) -> UploadedFileInfo:
        """建構 UploadedFileInfo 物件 - 修復版"""
        sheets = []
        if data.get("sheets_data"):
            for i, sheet_data in enumerate(data["sheets_data"]):
                try:

                    # ✅ 安全的資料類型檢查和轉換
                    safe_sheet_data = {
                        "sheet_name": str(sheet_data.get("sheet_name", f"Sheet_{i+1}")),
                        "row_count": self._safe_int_convert(sheet_data.get("row_count"), "row_count"),
                        "column_count": self._safe_int_convert(sheet_data.get("column_count"), "column_count"),
                        "columns": list(sheet_data.get("columns", [])),
                        "sample_data": sheet_data.get("sample_data", []),
                        "validation_status": str(sheet_data.get("validation_status", "pending")),
                        "validation_result": sheet_data.get("validation_result"),
                        "etl_status": str(sheet_data.get("etl_status", "not_loaded")),
                        "etl_job_id": sheet_data.get("etl_job_id"),
                        "loaded_at": sheet_data.get("loaded_at")
                    }

                    sheets.append(SheetInfo(**safe_sheet_data))

                except Exception as e:
                    logger.error(f"❌ 構造第 {i+1} 個 SheetInfo 失敗: {e}")
                    logger.error(f"原始資料: {sheet_data}")

                    # ✅ 創建錯誤恢復的最小 SheetInfo 而不是跳過
                    fallback_sheet = SheetInfo(
                        sheet_name=str(sheet_data.get("sheet_name", f"ErrorSheet_{i+1}")),
                        row_count=0,
                        column_count=0,
                        columns=[],
                        validation_status="error",
                        etl_status="failed"
                    )
                    sheets.append(fallback_sheet)

        return UploadedFileInfo(
            file_id=str(data["file_id"]),
            filename=data["filename"],
            original_filename=data.get("original_filename", data["filename"]),  # 向後相容
            file_path=data.get("file_path"),
            country=data["country"],
            file_size=data["file_size"],
            status=data["status"],
            upload_date=data["upload_date"],
            sheets=sheets
        )

    def _safe_int_convert(self, value: Any, field_name: str) -> int:
        """安全的整數轉換"""
        if value is None:
            return 0

        try:
            result = int(value)
            return max(0, result)
        except (ValueError, TypeError) as e:
            logger.warning(f"{field_name} 轉換失敗: {value} ({type(value)}), 錯誤: {e}")
            return 0
