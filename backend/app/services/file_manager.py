"""
File Manager Service
整合檔案儲存和資料庫管理的完整檔案管理服務
"""
import logging

import pandas as pd
from fastapi import UploadFile

from app.models.etl import SheetInfo, UploadedFileInfo
from app.repositories.file_repository import FileRepository
from app.services.file_service import file_service

logger = logging.getLogger(__name__)


class FileManagerService:
    """完整的檔案管理服務，整合儲存和資料庫操作"""

    def __init__(self):
        self.file_repository = FileRepository()
        self.storage_service = file_service

    async def upload_file(self, upload_file: UploadFile, country: str) -> UploadedFileInfo:
        """
        完整的檔案上傳流程：儲存檔案 + 建立資料庫記錄

        Args:
            upload_file: 上傳的檔案
            country: 國家代碼 (TW, SG, PM)

        Returns:
            UploadedFileInfo: 已上傳檔案資訊
        """
        try:
            logger.info(f"開始上傳檔案: {upload_file.filename}, 國家: {country}")

            # 1. 儲存檔案到本地存儲
            storage_result = await self.storage_service.save_upload_file(upload_file)

            # 2. 在資料庫中建立記錄
            file_info = await self.file_repository.create_file_record(
                filename=storage_result["stored_filename"],
                original_filename=storage_result["original_filename"],
                country=country,
                file_size=storage_result["file_size"],
                file_path=storage_result["file_path"]
            )

            logger.info(f"檔案上傳成功: {file_info.file_id}")
            return file_info

        except Exception as e:
            logger.error(f"檔案上傳失敗: {e}")
            raise

    async def analyze_file_sheets(self, file_id: str) -> list[SheetInfo]:
        """
        分析檔案中的工作表結構

        Args:
            file_id: 檔案 ID

        Returns:
            list[SheetInfo]: 工作表資訊列表
        """
        try:
            logger.info(f"開始分析檔案工作表: {file_id}")

            # 1. 取得檔案資訊
            file_info = await self.file_repository.get_file_by_id(file_id)
            if not file_info:
                raise ValueError(f"找不到檔案: {file_id}")

            # 2. 讀取檔案並分析工作表
            # 使用 file_path (如果有) 或者建構完整路徑
            file_path = file_info.file_path or file_info.filename
            sheets = await self._analyze_excel_file(file_path)

            # 3. 更新資料庫中的工作表資訊
            await self.file_repository.update_sheets_data(file_id, sheets)

            logger.info(f"檔案分析完成: {file_id}, 發現 {len(sheets)} 個工作表")
            return sheets

        except Exception as e:
            logger.error(f"檔案分析失敗: {e}")
            raise

    async def list_files(self) -> list[UploadedFileInfo]:
        """
        列出所有已上傳的檔案

        Returns:
            list[UploadedFileInfo]: 檔案列表
        """
        try:
            return await self.file_repository.list_all_files()
        except Exception as e:
            logger.error(f"列出檔案失敗: {e}")
            raise

    async def get_file_info(self, file_id: str) -> UploadedFileInfo | None:
        """
        取得檔案詳細資訊

        Args:
            file_id: 檔案 ID

        Returns:
            UploadedFileInfo: 檔案資訊
        """
        try:
            return await self.file_repository.get_file_by_id(file_id)
        except Exception as e:
            logger.error(f"取得檔案資訊失敗: {e}")
            raise

    async def confirm_file_upload(self, file_id: str, target_date: str | None = None) -> UploadedFileInfo:
        """
        確認檔案上傳，完成多步驟流程

        Args:
            file_id: 檔案 ID
            target_date: 目標處理日期

        Returns:
            UploadedFileInfo: 更新後的檔案資訊
        """
        try:
            logger.info(f"確認檔案上傳: {file_id}, 目標日期: {target_date}")

            # 更新檔案狀態為已確認
            await self.file_repository.update_file_status(
                file_id,
                "confirmed",
                target_date=target_date
            )

            # 返回更新後的檔案資訊
            file_info = await self.file_repository.get_file_by_id(file_id)
            if not file_info:
                raise ValueError(f"找不到檔案: {file_id}")

            return file_info

        except Exception as e:
            logger.error(f"確認檔案上傳失敗: {e}")
            raise

    async def _analyze_excel_file(self, file_path: str) -> list[SheetInfo]:
        """
        分析 Excel 檔案的工作表結構

        Args:
            file_path: 檔案路徑

        Returns:
            list[SheetInfo]: 工作表資訊
        """
        try:
            from pathlib import Path

            # 構建完整檔案路徑
            full_path = Path("uploads") / "inventory" / file_path
            if not full_path.exists():
                # 如果路徑不存在，嘗試直接使用檔案路徑
                full_path = Path(file_path)

            if not full_path.exists():
                raise FileNotFoundError(f"找不到檔案: {file_path}")

            # 讀取 Excel 檔案的所有工作表
            excel_file = pd.ExcelFile(str(full_path))
            sheets = []

            for sheet_name in excel_file.sheet_names:
                # 讀取工作表的前幾行來分析結構
                df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=5)

                # 處理 NaN 值，替換為 None 以便 JSON 序列化
                if not df.empty:
                    df_sample = df.head(3)
                    # 將 NaN 值轉換為 None，以便 JSON 序列化
                    sample_data = []
                    for _, row in df_sample.iterrows():
                        row_dict = {}
                        for col, value in row.items():
                            # 檢查是否為 NaN 並轉換為 None
                            row_dict[col] = None if pd.isna(value) else value
                        sample_data.append(row_dict)
                else:
                    sample_data = []

                sheet_info = SheetInfo(
                    sheet_name=sheet_name,
                    row_count=len(pd.read_excel(excel_file, sheet_name=sheet_name)),
                    column_count=len(df.columns),
                    columns=df.columns.tolist(),
                    sample_data=sample_data,
                    validation_status="pending",
                    etl_status="not_loaded"
                )
                sheets.append(sheet_info)

            return sheets

        except Exception as e:
            logger.error(f"分析 Excel 檔案失敗: {e}")
            raise


# 建立服務實例
file_manager = FileManagerService()
