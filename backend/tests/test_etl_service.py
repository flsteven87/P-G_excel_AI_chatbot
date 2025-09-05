"""
ETL 服務單元測試
測試 ETL 資料驗證、轉換和載入功能
"""
import asyncio

import pandas as pd
import pytest

from app.models.etl import DataQualityIssueType, ETLJobStatus
from app.services.etl_service import ETLFileProcessor, ETLService, ETLValidationService


class TestETLValidationService:
    """ETL 驗證服務測試"""

    def setup_method(self):
        """測試設置"""
        self.validation_service = ETLValidationService()

    def test_validate_valid_dataframe(self):
        """測試有效資料驗證"""
        # 準備測試資料
        data = {
            'Date': ['2025/08/28', '2025/08/28'],
            'Sku': ['TW001', 'TW002'],
            'Facility': ['E230', 'E230'],
            'Loc': ['A01', 'A02'],
            'Qty': [100, 200],
            'BQty': [50.0, 100.0],
            'QtyAllocated': [10, 20],
            'CaseCnt': [5, 10]
        }
        df = pd.DataFrame(data)

        # 執行驗證
        result = self.validation_service.validate_dataframe(df, "test_sheet")

        # 驗證結果
        assert result.is_valid is True
        assert result.total_rows == 2
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.data_summary['total_rows'] == 2
        assert result.data_summary['sheet_name'] == "test_sheet"

    def test_validate_missing_required_columns(self):
        """測試缺少必要欄位"""
        # 準備缺少必要欄位的資料
        data = {
            'Date': ['2025/08/28'],
            'Sku': ['TW001'],
            # 缺少 Facility, Loc, Qty
        }
        df = pd.DataFrame(data)

        # 執行驗證
        result = self.validation_service.validate_dataframe(df)

        # 驗證結果
        assert result.is_valid is False
        assert result.error_count > 0

        # 檢查錯誤類型
        missing_field_errors = [
            issue for issue in result.issues
            if issue.issue_type == DataQualityIssueType.MISSING_REQUIRED_FIELD
        ]
        assert len(missing_field_errors) >= 3  # Facility, Loc, Qty

    def test_validate_negative_quantities(self):
        """測試負數量驗證"""
        data = {
            'Date': ['2025/08/28'],
            'Sku': ['TW001'],
            'Facility': ['E230'],
            'Loc': ['A01'],
            'Qty': [-100],  # 負值
            'BQty': [50.0],
            'QtyAllocated': [10],
            'CaseCnt': [5]
        }
        df = pd.DataFrame(data)

        result = self.validation_service.validate_dataframe(df)

        assert result.is_valid is False
        negative_qty_errors = [
            issue for issue in result.issues
            if issue.issue_type == DataQualityIssueType.NEGATIVE_QUANTITY
        ]
        assert len(negative_qty_errors) > 0

    def test_validate_over_allocation(self):
        """測試配置量超過庫存量"""
        data = {
            'Date': ['2025/08/28'],
            'Sku': ['TW001'],
            'Facility': ['E230'],
            'Loc': ['A01'],
            'Qty': [100],
            'BQty': [50.0],
            'QtyAllocated': [150],  # 超過 Qty
            'CaseCnt': [5]
        }
        df = pd.DataFrame(data)

        result = self.validation_service.validate_dataframe(df)

        assert result.is_valid is False
        over_allocation_errors = [
            issue for issue in result.issues
            if issue.issue_type == DataQualityIssueType.OVER_ALLOCATION
        ]
        assert len(over_allocation_errors) > 0

    def test_validate_invalid_dates(self):
        """測試無效日期格式"""
        data = {
            'Date': ['invalid_date'],
            'Sku': ['TW001'],
            'Facility': ['E230'],
            'Loc': ['A01'],
            'Qty': [100],
            'BQty': [50.0],
            'QtyAllocated': [10],
            'CaseCnt': [5],
            'Manf_Date': ['not_a_date']
        }
        df = pd.DataFrame(data)

        result = self.validation_service.validate_dataframe(df)

        # 應該有日期格式警告
        date_errors = [
            issue for issue in result.issues
            if issue.issue_type == DataQualityIssueType.INVALID_DATE_FORMAT
        ]
        assert len(date_errors) > 0


class TestETLFileProcessor:
    """ETL 檔案處理器測試"""

    def setup_method(self):
        """測試設置"""
        self.file_processor = ETLFileProcessor()

    @pytest.mark.asyncio
    async def test_process_csv_file(self):
        """測試 CSV 檔案處理"""
        # 準備 CSV 內容
        csv_content = """Date,Sku,Facility,Loc,Qty,BQty,QtyAllocated,CaseCnt
2025/08/28,TW001,E230,A01,100,50.0,10,5
2025/08/28,TW002,E230,A02,200,100.0,20,10"""

        csv_bytes = csv_content.encode('utf-8')

        # 處理檔案
        dataframes = await self.file_processor.process_csv_file(csv_bytes, "test.csv")

        # 驗證結果
        assert "test.csv" in dataframes
        df = dataframes["test.csv"]
        assert len(df) == 2
        assert list(df.columns) == ['Date', 'Sku', 'Facility', 'Loc', 'Qty', 'BQty', 'QtyAllocated', 'CaseCnt']

    @pytest.mark.asyncio
    async def test_process_invalid_csv(self):
        """測試無效 CSV 檔案"""
        invalid_csv = b"invalid,csv,content\nwith,missing,data"

        with pytest.raises(ValueError, match="無法處理 CSV 檔案"):
            await self.file_processor.process_csv_file(invalid_csv, "invalid.csv")


class TestETLService:
    """ETL 主服務測試"""

    def setup_method(self):
        """測試設置"""
        self.etl_service = ETLService()

    @pytest.mark.asyncio
    async def test_create_etl_job(self):
        """測試建立 ETL 工作"""
        # 準備測試 CSV 內容
        csv_content = """Date,Sku,Facility,Loc,Qty,BQty,QtyAllocated,CaseCnt
2025/08/28,TW001,E230,A01,100,50.0,10,5"""
        csv_bytes = csv_content.encode('utf-8')

        # 建立工作（僅驗證模式）
        job = await self.etl_service.create_etl_job(
            file_content=csv_bytes,
            filename="test.csv",
            validate_only=True
        )

        # 驗證工作建立
        assert job.job_id is not None
        assert job.status == ETLJobStatus.PENDING
        assert job.source_file == "test.csv"

        # 等待工作完成（簡單輪詢）
        for _ in range(10):
            current_job = self.etl_service.get_job_status(str(job.job_id))
            if current_job and current_job.status in [ETLJobStatus.COMPLETED, ETLJobStatus.FAILED]:
                break
            await asyncio.sleep(0.1)

        # 驗證最終狀態
        final_job = self.etl_service.get_job_status(str(job.job_id))
        assert final_job is not None
        assert final_job.validation_result is not None

    def test_get_job_status(self):
        """測試取得工作狀態"""
        # 測試不存在的工作
        result = self.etl_service.get_job_status("nonexistent_job_id")
        assert result is None

    def test_list_active_jobs(self):
        """測試列出活躍工作"""
        jobs = self.etl_service.list_active_jobs()
        assert isinstance(jobs, list)

    @pytest.mark.asyncio
    async def test_cancel_job(self):
        """測試取消工作"""
        # 測試取消不存在的工作
        success = await self.etl_service.cancel_job("nonexistent_job_id")
        assert success is False


# Integration Test
class TestETLIntegration:
    """ETL 整合測試"""

    @pytest.mark.asyncio
    async def test_full_etl_workflow_validation_only(self):
        """測試完整 ETL 工作流程（僅驗證）"""
        etl_service = ETLService()

        # 準備良好的測試資料
        csv_content = """Date,Sku,Descr,Facility,Loc,SLOC,Qty,BQty,QtyAllocated,CaseCnt,Brand,Skugroup,BUom
2025/08/28,TW001,測試產品A,E230,A01,A01-01,1000,500.0,100,50,TestBrand,TestGroup,PCS
2025/08/28,TW002,測試產品B,E230,A02,A02-01,2000,800.0,200,100,TestBrand,TestGroup,PCS"""

        csv_bytes = csv_content.encode('utf-8-sig')

        # 執行 ETL（僅驗證）
        job = await etl_service.create_etl_job(
            file_content=csv_bytes,
            filename="integration_test.csv",
            target_date="2025-08-28",
            validate_only=True
        )

        # 等待完成
        max_wait_time = 30  # 30 秒超時
        for _i in range(max_wait_time):
            current_job = etl_service.get_job_status(str(job.job_id))
            if current_job and current_job.status in [ETLJobStatus.COMPLETED, ETLJobStatus.FAILED]:
                break
            await asyncio.sleep(1)

        # 驗證結果
        final_job = etl_service.get_job_status(str(job.job_id))
        assert final_job is not None
        assert final_job.status == ETLJobStatus.COMPLETED
        assert final_job.validation_result is not None
        assert final_job.validation_result.is_valid is True
        assert final_job.validation_result.total_rows == 2

        print(f"ETL 整合測試完成: {final_job.validation_result.total_rows} 筆資料驗證通過")


if __name__ == "__main__":
    # 執行簡單測試
    pytest.main([__file__, "-v"])
