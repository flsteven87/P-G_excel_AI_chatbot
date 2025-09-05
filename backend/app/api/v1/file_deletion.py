"""
Simple File Deletion API
簡化的檔案硬刪除 API
"""
import logging

from fastapi import APIRouter, HTTPException, status

from app.services.file_deletion import file_deletion_service

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/files", tags=["Simple-File-Deletion"])


@router.delete("/{file_id}/hard-delete")
async def hard_delete_file(file_id: str) -> dict:
    """
    硬刪除檔案

    完全刪除檔案和相關數據：
    - 刪除物理檔案
    - 刪除資料庫記錄
    - 刪除相關 sheets 資料

    Args:
        file_id: 檔案 ID

    Returns:
        dict: 刪除結果
    """
    try:
        logger.info(f"收到硬刪除請求: {file_id}")

        result = await file_deletion_service.delete_file_completely(file_id)

        if result["success"]:
            return {
                "success": True,
                "data": result,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

    except ValueError as e:
        logger.warning(f"檔案不存在: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"硬刪除檔案異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除失敗: {str(e)}"
        ) from e


@router.post("/{file_id}/confirm-delete")
async def confirm_delete_file(file_id: str) -> dict:
    """
    確認刪除檔案（返回檔案基本資訊）

    Args:
        file_id: 檔案 ID

    Returns:
        dict: 檔案資訊，用於確認
    """
    try:
        from app.repositories.file_repository import FileRepository

        file_repo = FileRepository()
        file_info = await file_repo.get_file_by_id(file_id)

        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到檔案: {file_id}"
            )

        return {
            "success": True,
            "data": {
                "file_id": file_info.file_id,
                "filename": file_info.filename,
                "file_size": file_info.file_size,
                "upload_date": file_info.upload_date,
                "country": file_info.country,
                "sheets_count": len(file_info.sheets) if file_info.sheets else 0
            },
            "message": "確認檔案資訊"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"確認刪除檔案異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取檔案資訊失敗: {str(e)}"
        ) from e
