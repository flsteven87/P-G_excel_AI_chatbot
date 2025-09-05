"""檔案服務層"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class FileStorageService:
    """檔案儲存服務"""

    def __init__(self):
        self.upload_dir = Path("uploads")
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {'.xlsx', '.xls', '.csv'}

        # 確保上傳目錄存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        (self.upload_dir / "inventory").mkdir(exist_ok=True)

    async def save_upload_file(self, upload_file, user_id: str | None = None) -> dict[str, Any]:
        """儲存上傳檔案"""
        try:
            # 生成唯一檔名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid4())[:8]
            stored_filename = f"{timestamp}_{unique_id}_{upload_file.filename}"

            file_path = self.upload_dir / "inventory" / stored_filename

            # 儲存檔案
            await upload_file.seek(0)
            with open(file_path, "wb") as f:
                while chunk := await upload_file.read(8192):
                    f.write(chunk)

            return {
                "original_filename": upload_file.filename,
                "stored_filename": stored_filename,
                "file_path": str(file_path),
                "file_size": upload_file.size,
                "upload_time": datetime.now(),
                "upload_status": "success"
            }
        except Exception as e:
            logger.error(f"檔案儲存失敗: {e}")
            raise


# 建立服務實例
file_service = FileStorageService()
