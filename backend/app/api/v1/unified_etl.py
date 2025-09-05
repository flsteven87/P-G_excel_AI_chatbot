"""
Unified ETL API Endpoints
統一的 ETL API 端點，遵循 CLAUDE.md 的 4 層架構和 RESTful 設計
"""
import logging
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.unified_etl import (
    APIResponse,
    ETLJobInfo,
    SheetProcessingRequest,
    SheetValidationResult,
    UnifiedFileUploadResponse,
)
from app.services.unified_etl_service import unified_etl_service

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/etl-unified", tags=["ETL-Unified"])


@router.post("/files/upload", response_model=APIResponse[UnifiedFileUploadResponse])
async def upload_and_analyze_file(
    file: Annotated[UploadFile, File(..., description="要上傳的 Excel 文件")],
    country: Annotated[str, Form(..., description="國家代碼 (TW, SG, PM)")],
    auto_analyze: Annotated[bool, Form(True, description="是否自動分析工作表")] = True
) -> APIResponse[UnifiedFileUploadResponse]:
    """
    統一的文件上傳和分析端點

    整合原來分離的上傳和分析功能，提供一站式文件處理服務

    Features:
    - 文件上傳和存儲
    - 自動工作表結構分析
    - 統一的進度追蹤
    - 標準化的錯誤處理

    Args:
        file: Excel 文件 (.xlsx, .xls)
        country: 國家代碼
        auto_analyze: 是否自動分析工作表結構

    Returns:
        APIResponse[UnifiedFileUploadResponse]: 統一的響應格式
    """
    try:
        logger.info(f"收到文件上傳請求: {file.filename}, 國家: {country}")

        # 基本驗證
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能為空"
            )

        # 驗證文件格式
        allowed_extensions = {".xlsx", ".xls", ".csv"}
        file_extension = "." + file.filename.split(".")[-1].lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支援的文件格式。支援格式: {', '.join(allowed_extensions)}"
            )

        # 驗證文件大小 (50MB 限制)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小不能超過 50MB"
            )

        # 驗證國家代碼
        allowed_countries = {"TW", "SG", "PM"}
        if country not in allowed_countries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支援的國家代碼。支援: {', '.join(allowed_countries)}"
            )

        # 調用服務處理文件
        result = await unified_etl_service.upload_and_analyze_file(
            upload_file=file,
            country=country,
            auto_analyze=auto_analyze
        )

        # 根據結果決定響應狀態
        if result.status.value == "error":
            return APIResponse[UnifiedFileUploadResponse](
                success=False,
                data=result,
                message=result.error or "文件處理失敗",
                error_code=result.error_code
            )
        else:
            return APIResponse[UnifiedFileUploadResponse](
                success=True,
                data=result,
                message=f"文件處理成功，發現 {result.total_sheets} 個工作表"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上傳處理異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服務器內部錯誤: {str(e)}"
        ) from e


@router.post("/files/{file_id}/sheets/validate",
            response_model=APIResponse[dict[str, SheetValidationResult]])
async def validate_sheets(
    file_id: str,
    sheet_names: list[str]
) -> APIResponse[dict[str, SheetValidationResult]]:
    """
    驗證指定文件的工作表

    對選定的工作表執行數據品質驗證，檢查：
    - 必要欄位完整性
    - 數據類型正確性
    - 業務邏輯規則
    - 數據品質問題

    Args:
        file_id: 文件 ID
        sheet_names: 要驗證的工作表名稱列表

    Returns:
        APIResponse[dict[str, SheetValidationResult]]: 驗證結果
    """
    try:
        logger.info(f"收到工作表驗證請求: {file_id}, 工作表: {sheet_names}")

        if not sheet_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="請指定要驗證的工作表"
            )

        # 調用服務執行驗證
        results = await unified_etl_service.validate_sheets(file_id, sheet_names)

        # 統計驗證結果
        total_sheets = len(results)
        valid_sheets = sum(1 for r in results.values() if r.is_valid)

        return APIResponse[dict[str, SheetValidationResult]](
            success=True,
            data=results,
            message=f"驗證完成：{valid_sheets}/{total_sheets} 個工作表通過驗證"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"工作表驗證異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"驗證失敗: {str(e)}"
        ) from e


@router.post("/files/{file_id}/sheets/process",
            response_model=APIResponse[list[ETLJobInfo]])
async def process_sheets(
    file_id: str,
    request: SheetProcessingRequest
) -> APIResponse[list[ETLJobInfo]]:
    """
    處理工作表數據到數據庫

    將驗證通過的工作表數據載入到數據倉庫，支援：
    - 批量數據處理
    - 增量/全量更新模式
    - 數據轉換和清理
    - 異步作業追蹤

    Args:
        file_id: 文件 ID
        request: 處理請求詳情

    Returns:
        APIResponse[list[ETLJobInfo]]: ETL 作業信息
    """
    try:
        logger.info(f"收到工作表處理請求: {file_id}")

        if not request.sheet_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="請指定要處理的工作表"
            )

        # 調用服務執行處理
        jobs = await unified_etl_service.process_sheets(file_id, request)

        return APIResponse[list[ETLJobInfo]](
            success=True,
            data=jobs,
            message=f"已創建 {len(jobs)} 個 ETL 處理作業"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"工作表處理異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"處理失敗: {str(e)}"
        ) from e


@router.get("/files/{file_id}", response_model=APIResponse[UnifiedFileUploadResponse])
async def get_file_info(file_id: str) -> APIResponse[UnifiedFileUploadResponse]:
    """
    獲取文件詳細信息

    Args:
        file_id: 文件 ID

    Returns:
        APIResponse[UnifiedFileUploadResponse]: 文件信息
    """
    try:
        # TODO: 實現獲取文件信息的邏輯
        # 這需要從 Repository 層獲取數據
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="功能正在開發中"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取文件信息異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取失敗: {str(e)}"
        ) from e


@router.get("/jobs/{job_id}", response_model=APIResponse[ETLJobInfo])
async def get_job_status(job_id: str) -> APIResponse[ETLJobInfo]:
    """
    獲取 ETL 作業狀態

    Args:
        job_id: 作業 ID

    Returns:
        APIResponse[ETLJobInfo]: 作業狀態信息
    """
    try:
        # TODO: 實現獲取作業狀態的邏輯
        # 這需要從 Repository 層獲取數據
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="功能正在開發中"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取作業狀態異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取失敗: {str(e)}"
        ) from e


@router.post("/jobs/{job_id}/cancel", response_model=APIResponse[None])
async def cancel_job(job_id: str) -> APIResponse[None]:
    """
    取消 ETL 作業

    Args:
        job_id: 作業 ID

    Returns:
        APIResponse[None]: 取消結果
    """
    try:
        # TODO: 實現取消作業的邏輯
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="功能正在開發中"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消作業異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消失敗: {str(e)}"
        ) from e


@router.get("/health", response_model=APIResponse[dict])
async def health_check() -> APIResponse[dict]:
    """
    服務健康檢查

    Returns:
        APIResponse[dict]: 服務狀態
    """
    try:
        health_info = {
            "status": "healthy",
            "service": "unified-etl",
            "version": "1.0.0",
            "features": [
                "file_upload",
                "sheet_analysis",
                "data_validation",
                "etl_processing"
            ]
        }

        return APIResponse[dict](
            success=True,
            data=health_info,
            message="服務運行正常"
        )

    except Exception as e:
        logger.error(f"健康檢查異常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服務異常: {str(e)}"
        ) from e
