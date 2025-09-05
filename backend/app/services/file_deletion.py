"""
Simple File Deletion Service
簡化的檔案硬刪除服務
"""
import logging
from pathlib import Path

from app.repositories.file_repository import FileRepository

logger = logging.getLogger(__name__)


class FileDeletionService:
    """
    簡化的檔案硬刪除服務

    功能：
    1. 刪除檔案記錄（從 uploaded_files 表）
    2. 刪除相關 sheets 資料
    3. 刪除物理檔案
    """

    def __init__(self):
        self._file_repo = FileRepository()

    async def delete_file_completely(self, file_id: str) -> dict:
        """
        完全刪除檔案（硬刪除）

        Args:
            file_id: 檔案 ID

        Returns:
            dict: 刪除結果
        """
        try:
            logger.info(f"開始硬刪除檔案: {file_id}")

            # 1. 獲取檔案資訊
            file_info = await self._file_repo.get_file_by_id(file_id)
            if not file_info:
                raise ValueError(f"找不到檔案: {file_id}")

            deleted_items = []
            storage_freed = 0

            # 2. 刪除物理檔案
            if file_info.file_path:
                file_path = Path(file_info.file_path)
                if file_path.exists():
                    storage_freed = file_path.stat().st_size
                    file_path.unlink()
                    deleted_items.append(str(file_path))
                    logger.info(f"物理檔案已刪除: {file_path}")

            # 3. 刪除資料庫記錄（直接從表中刪除）
            await self._delete_file_record(file_id)
            deleted_items.append(f"database_record:{file_id}")
            logger.info(f"資料庫記錄已刪除: {file_id}")

            result = {
                "success": True,
                "file_id": file_id,
                "filename": file_info.filename,
                "deleted_items": deleted_items,
                "storage_freed": storage_freed,
                "message": f"檔案 {file_info.filename} 已完全刪除"
            }

            logger.info(f"檔案硬刪除完成: {file_id}")
            return result

        except Exception as e:
            logger.error(f"檔案硬刪除失敗: {e}")
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "message": f"刪除失敗: {str(e)}"
            }

    async def _delete_file_record(self, file_id: str):
        """直接從資料庫刪除檔案記錄"""
        try:
            # 使用 FileRepository 的刪除方法
            from app.repositories.supabase_base import SupabaseRepository

            # 創建臨時 repository 實例來執行刪除
            repo = SupabaseRepository(table_name="uploaded_files", model_class=dict)

            # 獲取客戶端並執行刪除操作
            client = await repo.get_client()
            result = await client.from_("uploaded_files").delete().eq("file_id", file_id).execute()

            # 處理結果
            if result.data:
                logger.info(f"已從資料庫刪除檔案記錄: {file_id}, 刪除了 {len(result.data)} 條記錄")
            else:
                logger.warning(f"沒有找到要刪除的記錄: {file_id}")

        except Exception as e:
            logger.error(f"刪除資料庫記錄失敗: {e}")
            raise


# 建立服務實例
file_deletion_service = FileDeletionService()
