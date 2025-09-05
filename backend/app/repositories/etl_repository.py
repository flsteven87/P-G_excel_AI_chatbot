"""
ETL Repository Layer
處理 ETL 相關的資料庫操作，遵循 Repository 模式
"""
import logging
from datetime import date, datetime
from typing import Any

from app.models.etl import (
    ETLJobStatus,
)
from app.repositories.supabase_base import SupabaseRepository

logger = logging.getLogger(__name__)


class ETLJobRepository(SupabaseRepository):
    """ETL 工作記錄 Repository"""

    def __init__(self):
        # 這裡我們使用一個虛擬表格來記錄 ETL 工作狀態
        # 實際上可以創建一個專門的 etl_jobs 表格
        super().__init__(table_name="tw_stg_inventory_sg", model_class=dict)

    async def create_job_record(self, job_data: dict) -> dict:
        """建立 ETL 工作記錄"""
        try:
            # 在 staging 表中插入工作記錄標識
            record = {
                "source_file": job_data["source_file"],
                "status": job_data["status"],
                "loaded_at": datetime.now().isoformat()
            }

            # ✅ Use base class method with proper error handling
            return await super().create(record)

        except Exception as e:
            logger.error(f"建立 ETL 工作記錄失敗: {e}")
            raise

    async def update_job_status(self, job_id: str, status: ETLJobStatus, **kwargs) -> bool:
        """更新工作狀態"""
        try:
            update_data = {
                "status": status.value,
                "processed_at": datetime.now().isoformat()
            }
            update_data.update(kwargs)

            # 使用基類方法，但需要自定義查詢條件
            client = await self.get_client()
            query = client.from_(self.table_name).update(update_data).eq("source_file", job_id)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result for all queries
            data = self._handle_supabase_result(result, allow_empty=True)
            return data is not None

        except Exception as e:
            logger.error(f"更新工作狀態失敗: {e}")
            return False


class InventoryRepository(SupabaseRepository):
    """庫存資料 Repository - 處理維度和事實表的插入"""

    def __init__(self):
        super().__init__(table_name="tw_fact_inventory_snapshot", model_class=dict)

    async def insert_staging_data(self, data_rows: list[dict[str, Any]], source_file: str) -> int:
        """批次插入暫存資料 - 增強版"""
        try:
            logger.info(f"開始插入 staging 資料: {len(data_rows)} 筆記錄，source_file: {source_file}")

            # ✅ 檢查資料格式
            if not data_rows:
                logger.warning("沒有資料需要插入")
                return 0

            # 準備 staging 資料
            staging_records = []
            for i, row in enumerate(data_rows, 1):
                try:
                    mapped_row = self._map_to_staging_columns(row)
                    staging_record = {
                        "source_file": source_file,
                        "row_num": i,
                        "status": "pending",
                        **mapped_row
                    }
                    staging_records.append(staging_record)
                except Exception as map_error:
                    logger.error(f"映射第 {i} 筆資料失敗: {map_error}")
                    logger.error(f"原始資料: {row}")
                    # 繼續處理其他資料
                    continue

            if not staging_records:
                logger.error("所有資料映射失敗，無法插入 staging 表")
                return 0

            logger.info(f"準備插入 {len(staging_records)} 筆映射後的資料")

            # ✅ 分批插入，避免單次插入過多資料
            batch_size = 1000
            total_inserted = 0

            client = await self.get_client()

            for i in range(0, len(staging_records), batch_size):
                batch = staging_records[i:i + batch_size]
                logger.info(f"插入第 {i//batch_size + 1} 批: {len(batch)} 筆記錄")

                result = await client.from_("tw_stg_inventory_sg").insert(batch).execute()
                inserted_data = self._handle_supabase_result(result)
                batch_count = len(inserted_data) if inserted_data else 0
                total_inserted += batch_count

                logger.info(f"第 {i//batch_size + 1} 批插入成功: {batch_count} 筆")

            logger.info(f"Staging 資料插入完成，總計: {total_inserted} 筆")
            return total_inserted

        except Exception as e:
            logger.error(f"插入 staging 資料失敗: {e}")
            logger.error(f"錯誤詳情: source_file={source_file}, data_rows_count={len(data_rows) if data_rows else 0}")
            raise Exception(f"Staging 資料插入失敗: {str(e)}") from e

    def _map_to_staging_columns(self, row: dict[str, Any]) -> dict[str, str]:
        """將資料列映射到 staging 表格欄位 (全部轉為字串)"""
        import pandas as pd

        def safe_str(value):
            """安全轉換為字串，處理 NaN 和 None"""
            if pd.isna(value) or value is None:
                return ""
            return str(value).strip()

        # ✅ 使用正確的 Excel 欄位名稱作為鍵值
        return {
            "Date": safe_str(row.get("Date", "")),
            "Sku": safe_str(row.get("Sku", "")),
            "Descr": safe_str(row.get("Descr", "")),
            "Brand": safe_str(row.get("Brand", "")),  # ✅ 允許為空
            "Skugroup": safe_str(row.get("Skugroup", "")),
            "Facility": safe_str(row.get("Facility", "")),
            "Loc": safe_str(row.get("Loc", "")),
            "SLOC": safe_str(row.get("SLOC", "")),
            "Qty": safe_str(row.get("Qty", "0")),
            "BQty": safe_str(row.get("BQty", "0")),
            "QtyAllocated": safe_str(row.get("QtyAllocated", "0")),
            "CaseCnt": safe_str(row.get("CaseCnt", "0")),
            "BUom": safe_str(row.get("BUom", "")),
            "WMS Lot": safe_str(row.get("WMS Lot", "")),
            "Manf_Date": safe_str(row.get("Manf_Date", "")),
            "Receipt Date": safe_str(row.get("Receipt Date", "")),
            "DC Stop Ship Date": safe_str(row.get("DC Stop Ship Date", "")),
            "Shelflife": safe_str(row.get("Shelflife", "")),
            "Stop Ship Lead time": safe_str(row.get("Stop Ship Lead time", "")),
            "EAN": safe_str(row.get("EAN", "")),
            "ITF-14": safe_str(row.get("ITF-14", "")),
            "REASON": safe_str(row.get("REASON", "")),  # ✅ 允許為空
            "Remark": safe_str(row.get("Remark", "")),
            "Id": safe_str(row.get("Id", "")),  # ✅ 使用實際的 Id 欄位
        }

    async def process_staging_to_dimensions(self, source_file: str) -> dict[str, int]:
        """處理 staging 資料到維度表"""
        try:
            result_counts = {
                "products": 0,
                "locations": 0,
                "lots": 0
            }

            # 1. 處理產品維度
            result_counts["products"] = await self._upsert_products(source_file)

            # 2. 處理地點維度
            result_counts["locations"] = await self._upsert_locations(source_file)

            # 3. 處理批號維度
            result_counts["lots"] = await self._upsert_lots(source_file)

            return result_counts

        except Exception as e:
            logger.error(f"處理維度資料失敗: {e}")
            raise

    async def _upsert_products(self, source_file: str) -> int:
        """更新產品維度"""
        try:
            # 使用 SQL 執行 upsert 邏輯
            sql = """
            INSERT INTO tw_dim_product (sku, descr, brand_name, skugroup_name, ean, itf14)
            SELECT DISTINCT
                "Sku"::text,
                NULLIF(TRIM("Descr"), '') as descr,
                NULLIF(TRIM("Brand"), '') as brand_name,
                NULLIF(TRIM("Skugroup"), '') as skugroup_name,
                NULLIF(TRIM("EAN"), '') as ean,
                NULLIF(TRIM("ITF-14"), '') as itf14
            FROM tw_stg_inventory_sg
            WHERE source_file = $1 AND "Sku" IS NOT NULL
            ON CONFLICT (sku) DO UPDATE SET
                descr = COALESCE(EXCLUDED.descr, tw_dim_product.descr),
                brand_name = COALESCE(EXCLUDED.brand_name, tw_dim_product.brand_name),
                skugroup_name = COALESCE(EXCLUDED.skugroup_name, tw_dim_product.skugroup_name),
                ean = COALESCE(EXCLUDED.ean, tw_dim_product.ean),
                itf14 = COALESCE(EXCLUDED.itf14, tw_dim_product.itf14)
            """

            # ✅ MUST use base class execute_sql method
            # 將 $1 替換為實際參數（因為新的 RPC 使用字串替換）
            final_sql = sql.replace('$1', f"'{source_file}'")
            result = await super().execute_sql(final_sql, [])
            count = len(result) if result else 0
            logger.info(f"產品維度 upsert 完成: {count} 筆記錄")
            return count

        except Exception as e:
            logger.error(f"更新產品維度失敗: {e}")
            raise  # 拋出異常，讓上層知道失敗

    async def _upsert_locations(self, source_file: str) -> int:
        """更新地點維度"""
        try:
            # ✅ 修正地點維度插入邏輯，匹配實際的唯一約束
            sql = """
            INSERT INTO tw_dim_location (facility_code, loc_code, sloc_code)
            SELECT DISTINCT
                NULLIF(TRIM("Facility"), ''),
                NULLIF(TRIM("Loc"), ''),
                NULLIF(TRIM("SLOC"), '')
            FROM tw_stg_inventory_sg
            WHERE source_file = $1
                AND "Facility" IS NOT NULL
                AND "Facility" != ''
                AND "Loc" IS NOT NULL
                AND "Loc" != ''
            ON CONFLICT (facility_code, loc_code, sloc_code) DO UPDATE SET
                updated_at = now()
            """

            # ✅ MUST use base class execute_sql method
            # 將 $1 替換為實際參數
            final_sql = sql.replace('$1', f"'{source_file}'")
            result = await super().execute_sql(final_sql, [])
            count = len(result) if result else 0
            logger.info(f"地點維度 upsert 完成: {count} 筆記錄")
            return count

        except Exception as e:
            logger.error(f"更新地點維度失敗: {e}")
            raise  # 拋出異常，讓上層知道失敗

    async def _upsert_lots(self, source_file: str) -> int:
        """更新批號維度"""
        try:
            sql = """
            INSERT INTO tw_dim_lot (
                lot_code, product_id, facility_code, manf_date, receipt_date,
                shelf_life_days, dc_stop_ship_date, stop_ship_lead_days, reason_code, remark
            )
            SELECT DISTINCT
                s."WMS Lot"::text as lot_code,
                p.product_id,
                NULLIF(TRIM(s."Facility"), ''),
                CASE
                    WHEN s."Manf_Date" ~ '^[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}$'
                    THEN s."Manf_Date"::date
                    ELSE NULL
                END,
                CASE
                    WHEN s."Receipt Date" ~ '^[0-9]{8}'
                    THEN to_date(SUBSTRING(s."Receipt Date" FROM 1 FOR 8), 'YYYYMMDD')
                    ELSE NULL
                END,
                CASE
                    WHEN s."Shelflife" ~ '^[0-9]+$'
                    THEN s."Shelflife"::integer
                    ELSE NULL
                END,
                CASE
                    WHEN s."DC Stop Ship Date" ~ '^[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}$'
                    THEN s."DC Stop Ship Date"::date
                    ELSE NULL
                END,
                CASE
                    WHEN s."Stop Ship Lead time" ~ '^[0-9]+$'
                    THEN s."Stop Ship Lead time"::integer
                    ELSE NULL
                END,
                NULLIF(TRIM(s."REASON"), ''),
                NULLIF(TRIM(s."Remark"), '')
            FROM tw_stg_inventory_sg s
            JOIN tw_dim_product p ON p.sku = s."Sku"::text
            WHERE s.source_file = $1 AND s."WMS Lot" IS NOT NULL
            ON CONFLICT (product_id, lot_code, facility_code) WHERE facility_code IS NOT NULL DO NOTHING
            """

            # ✅ MUST use base class execute_sql method
            # 將 $1 替換為實際參數
            final_sql = sql.replace('$1', f"'{source_file}'")

            # 分別處理有 facility_code 和沒有 facility_code 的情況
            try:
                await super().execute_sql(final_sql, [])

                # 再處理沒有 facility_code 的批號
                sql_no_facility = """
                INSERT INTO tw_dim_lot (
                    lot_code, product_id, manf_date, receipt_date,
                    shelf_life_days, dc_stop_ship_date, stop_ship_lead_days, reason_code, remark
                )
                SELECT DISTINCT
                    s."WMS Lot"::text as lot_code,
                    p.product_id,
                    CASE
                        WHEN s."Manf_Date" ~ '^[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}$'
                        THEN s."Manf_Date"::date
                        ELSE NULL
                    END,
                    CASE
                        WHEN s."Receipt Date" ~ '^[0-9]{8}'
                        THEN to_date(SUBSTRING(s."Receipt Date" FROM 1 FOR 8), 'YYYYMMDD')
                        ELSE NULL
                    END,
                    CASE
                        WHEN s."Shelflife" ~ '^[0-9]+$'
                        THEN s."Shelflife"::integer
                        ELSE NULL
                    END,
                    CASE
                        WHEN s."DC Stop Ship Date" ~ '^[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}$'
                        THEN s."DC Stop Ship Date"::date
                        ELSE NULL
                    END,
                    CASE
                        WHEN s."Stop Ship Lead time" ~ '^[0-9]+$'
                        THEN s."Stop Ship Lead time"::integer
                        ELSE NULL
                    END,
                    NULLIF(TRIM(s."REASON"), ''),
                    NULLIF(TRIM(s."Remark"), '')
                FROM tw_stg_inventory_sg s
                JOIN tw_dim_product p ON p.sku = s."Sku"::text
                WHERE s.source_file = '{source_file}' AND s."WMS Lot" IS NOT NULL
                    AND (s."Facility" IS NULL OR TRIM(s."Facility") = '')
                ON CONFLICT (product_id, lot_code) WHERE facility_code IS NULL DO NOTHING
                """

                await super().execute_sql(sql_no_facility, [])

                count = 1  # 假設至少有一些資料插入
                logger.info(f"批號維度 upsert 完成: {count} 筆記錄 (有/無 facility)")
                return count

            except Exception as lot_error:
                logger.error(f"批號維度插入錯誤: {lot_error}")
                # 嘗試簡化的插入，不使用 ON CONFLICT
                try:
                    simple_sql = """
                    INSERT INTO tw_dim_lot (lot_code, product_id, facility_code)
                    SELECT DISTINCT
                        s."WMS Lot"::text as lot_code,
                        p.product_id,
                        NULLIF(TRIM(s."Facility"), '')
                    FROM tw_stg_inventory_sg s
                    JOIN tw_dim_product p ON p.sku = s."Sku"::text
                    WHERE s.source_file = '{source_file}' AND s."WMS Lot" IS NOT NULL
                    """

                    await super().execute_sql(simple_sql, [])
                    count = 1
                    logger.info(f"批號維度簡化插入完成: {count} 筆記錄")
                    return count
                except Exception as simple_error:
                    logger.error(f"批號維度簡化插入也失敗: {simple_error}")
                    return 0

        except Exception as e:
            logger.error(f"更新批號維度失敗: {e}")
            raise  # 拋出異常，讓上層知道失敗

    async def process_staging_to_facts(self, source_file: str, target_date: date) -> int:
        """處理 staging 資料到事實表"""
        try:
            # 先處理有批號的資料
            with_lot_sql = """
            INSERT INTO tw_fact_inventory_snapshot
                (snapshot_date, product_id, location_id, lot_id, qty, bqty, qty_allocated, case_cnt, buom_code, source_system, source_row_key)
            SELECT
                $1::date as snapshot_date,
                p.product_id,
                l.location_id,
                lot.lot_id,
                COALESCE(s."Qty"::numeric, 0),
                COALESCE(s."BQty"::numeric, 0),
                COALESCE(s."QtyAllocated"::numeric, 0),
                COALESCE(s."CaseCnt"::numeric, 0),
                NULLIF(TRIM(s."BUom"), ''),
                'WMS',
                NULLIF(TRIM(s."Id"), '')
            FROM tw_stg_inventory_sg s
            JOIN tw_dim_product p ON p.sku = s."Sku"::text
            JOIN tw_dim_location l ON l.facility_code = s."Facility" AND l.loc_code = s."Loc"
                AND COALESCE(l.sloc_code, '') = COALESCE(s."SLOC", '')
            JOIN tw_dim_lot lot ON lot.product_id = p.product_id AND lot.lot_code = s."WMS Lot"::text
            WHERE s.source_file = $2 AND s."WMS Lot" IS NOT NULL
            """

            # 然後處理無批號的資料
            without_lot_sql = """
            INSERT INTO tw_fact_inventory_snapshot
                (snapshot_date, product_id, location_id, lot_id, qty, bqty, qty_allocated, case_cnt, buom_code, source_system, source_row_key)
            SELECT
                $1::date as snapshot_date,
                p.product_id,
                l.location_id,
                NULL,
                COALESCE(s."Qty"::numeric, 0),
                COALESCE(s."BQty"::numeric, 0),
                COALESCE(s."QtyAllocated"::numeric, 0),
                COALESCE(s."CaseCnt"::numeric, 0),
                NULLIF(TRIM(s."BUom"), ''),
                'WMS',
                NULLIF(TRIM(s."Id"), '')
            FROM tw_stg_inventory_sg s
            JOIN tw_dim_product p ON p.sku = s."Sku"::text
            JOIN tw_dim_location l ON l.facility_code = s."Facility" AND l.loc_code = s."Loc"
                AND COALESCE(l.sloc_code, '') = COALESCE(s."SLOC", '')
            WHERE s.source_file = $2 AND (s."WMS Lot" IS NULL OR s."WMS Lot" = '')
            """

            # 執行兩個 SQL - ✅ Use base class method
            target_date_str = target_date.isoformat()

            # 替換參數 $1=target_date, $2=source_file
            final_with_lot_sql = with_lot_sql.replace('$1', f"'{target_date_str}'").replace('$2', f"'{source_file}'")
            final_without_lot_sql = without_lot_sql.replace('$1', f"'{target_date_str}'").replace('$2', f"'{source_file}'")

            result1 = await super().execute_sql(final_with_lot_sql, [])
            result2 = await super().execute_sql(final_without_lot_sql, [])

            # 返回總插入數量
            count1 = len(result1) if result1 else 0
            count2 = len(result2) if result2 else 0
            total_count = count1 + count2

            logger.info(f"事實表載入完成: 有批號 {count1} 筆, 無批號 {count2} 筆, 總計 {total_count} 筆")
            return total_count

        except Exception as e:
            logger.error(f"處理事實表資料失敗: {e}")
            raise

    async def cleanup_staging_data(self, source_file: str) -> bool:
        """清理 staging 資料"""
        try:
            client = await self.get_client()
            query = client.from_("tw_stg_inventory_sg").delete().eq("source_file", source_file)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result for all queries
            self._handle_supabase_result(result, allow_empty=True)
            return True

        except Exception as e:
            logger.error(f"清理 staging 資料失敗: {e}")
            return False
