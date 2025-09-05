"""
Inventory Repository Layer
處理庫存相關的資料庫操作，包含維度表和事實表
嚴格遵循 CLAUDE.md Repository Layer 規範
"""
import logging
from datetime import date

from app.repositories.supabase_base import SupabaseRepository

logger = logging.getLogger(__name__)


class ProductRepository(SupabaseRepository):
    """產品維度 Repository"""

    def __init__(self):
        # ✅ MUST inherit from SupabaseRepository base class
        super().__init__(table_name="tw_dim_product", model_class=dict)

    async def get_by_sku(self, sku: str) -> dict | None:
        """根據 SKU 取得產品"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("sku", sku)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result() for ALL query results
            data = self._handle_supabase_result(result, allow_empty=True)

            if not data:
                return None

            return data[0] if isinstance(data, list) else data

        except Exception as e:
            logger.error(f"根據 SKU 取得產品失敗 ({sku}): {e}")
            raise

    async def get_by_brand(self, brand_name: str, limit: int = 100) -> list[dict]:
        """根據品牌取得產品列表"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("brand_name", brand_name).limit(limit)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result() for ALL query results
            data = self._handle_supabase_result(result, allow_empty=True)

            return self._build_models(data)

        except Exception as e:
            logger.error(f"根據品牌取得產品失敗 ({brand_name}): {e}")
            raise

    async def search_products(self, search_term: str, limit: int = 50) -> list[dict]:
        """搜尋產品"""
        try:
            # 使用 RPC 函數進行全文搜尋
            sql = """
            SELECT * FROM tw_dim_product
            WHERE sku ILIKE $1
               OR descr ILIKE $1
               OR brand_name ILIKE $1
            ORDER BY
                CASE
                    WHEN sku ILIKE $1 THEN 1
                    WHEN descr ILIKE $1 THEN 2
                    ELSE 3
                END
            LIMIT $2
            """

            search_pattern = f"%{search_term}%"
            # ✅ MUST use base class execute_sql method
            result = await super().execute_sql(sql, [search_pattern, limit])

            return result or []

        except Exception as e:
            logger.error(f"搜尋產品失敗 ({search_term}): {e}")
            raise


class LocationRepository(SupabaseRepository):
    """地點維度 Repository"""

    def __init__(self):
        # ✅ MUST inherit from SupabaseRepository base class
        super().__init__(table_name="tw_dim_location", model_class=dict)

    async def get_by_facility(self, facility_code: str) -> list[dict]:
        """根據倉庫代碼取得所有地點"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("facility_code", facility_code)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result() for ALL query results
            data = self._handle_supabase_result(result, allow_empty=True)

            return self._build_models(data)

        except Exception as e:
            logger.error(f"根據倉庫代碼取得地點失敗 ({facility_code}): {e}")
            raise

    async def get_by_facility_and_location(
        self,
        facility_code: str,
        loc_code: str,
        sloc_code: str | None = None
    ) -> dict | None:
        """根據倉庫、地點和子地點取得地點記錄"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*")\
                .eq("facility_code", facility_code)\
                .eq("loc_code", loc_code)

            if sloc_code:
                query = query.eq("sloc_code", sloc_code)
            else:
                query = query.is_("sloc_code", "null")

            result = await query.execute()

            # ✅ MUST use _handle_supabase_result() for ALL query results
            data = self._handle_supabase_result(result, allow_empty=True)

            if not data:
                return None

            return data[0] if isinstance(data, list) else data

        except Exception as e:
            logger.error(f"根據地點資訊取得記錄失敗: {e}")
            raise


class LotRepository(SupabaseRepository):
    """批號維度 Repository"""

    def __init__(self):
        # ✅ MUST inherit from SupabaseRepository base class
        super().__init__(table_name="tw_dim_lot", model_class=dict)

    async def get_by_product_and_lot(self, product_id: int, lot_code: str) -> dict | None:
        """根據產品ID和批號取得批號記錄"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*")\
                .eq("product_id", product_id)\
                .eq("lot_code", lot_code)
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result() for ALL query results
            data = self._handle_supabase_result(result, allow_empty=True)

            if not data:
                return None

            return data[0] if isinstance(data, list) else data

        except Exception as e:
            logger.error(f"根據產品和批號取得記錄失敗: {e}")
            raise

    async def get_expiring_lots(self, days_ahead: int = 30) -> list[dict]:
        """取得即將過期的批號"""
        try:
            sql = """
            SELECT l.*, p.sku, p.descr as product_name
            FROM tw_dim_lot l
            JOIN tw_dim_product p ON l.product_id = p.product_id
            WHERE l.dc_stop_ship_date IS NOT NULL
              AND l.dc_stop_ship_date <= CURRENT_DATE + INTERVAL '%s days'
              AND l.dc_stop_ship_date >= CURRENT_DATE
            ORDER BY l.dc_stop_ship_date ASC
            """

            # ✅ MUST use base class execute_sql method
            result = await super().execute_sql(sql, [days_ahead])

            return result or []

        except Exception as e:
            logger.error(f"取得即將過期批號失敗: {e}")
            raise


class InventorySnapshotRepository(SupabaseRepository):
    """庫存快照事實表 Repository"""

    def __init__(self):
        # ✅ MUST inherit from SupabaseRepository base class
        super().__init__(table_name="tw_fact_inventory_snapshot", model_class=dict)

    async def get_snapshot_by_date(self, snapshot_date: date) -> list[dict]:
        """根據日期取得庫存快照"""
        try:
            client = await self.get_client()
            query = client.from_(self.table_name).select("*").eq("snapshot_date", snapshot_date.isoformat())
            result = await query.execute()

            # ✅ MUST use _handle_supabase_result() for ALL query results
            data = self._handle_supabase_result(result, allow_empty=True)

            return self._build_models(data)

        except Exception as e:
            logger.error(f"根據日期取得庫存快照失敗 ({snapshot_date}): {e}")
            raise

    async def get_inventory_summary(self, snapshot_date: date | None = None) -> list[dict]:
        """取得庫存摘要報表"""
        try:
            sql = """
            SELECT
                p.sku,
                p.descr as product_name,
                p.brand_name,
                l.facility_code,
                SUM(f.qty) as total_qty,
                SUM(f.bqty) as total_bqty,
                SUM(f.qty_allocated) as total_allocated,
                COUNT(*) as location_count
            FROM tw_fact_inventory_snapshot f
            JOIN tw_dim_product p ON f.product_id = p.product_id
            JOIN tw_dim_location l ON f.location_id = l.location_id
            WHERE ($1::date IS NULL OR f.snapshot_date = $1::date)
            GROUP BY p.product_id, p.sku, p.descr, p.brand_name, l.facility_code
            ORDER BY total_qty DESC
            """

            date_param = snapshot_date.isoformat() if snapshot_date else None
            # ✅ MUST use base class execute_sql method
            result = await super().execute_sql(sql, [date_param])

            return result or []

        except Exception as e:
            logger.error(f"取得庫存摘要失敗: {e}")
            raise

    async def get_low_stock_items(self, threshold: float = 100.0) -> list[dict]:
        """取得低庫存商品"""
        try:
            sql = """
            SELECT
                p.sku,
                p.descr as product_name,
                l.facility_code,
                l.loc_code,
                f.qty,
                f.qty_allocated,
                f.snapshot_date
            FROM tw_fact_inventory_snapshot f
            JOIN tw_dim_product p ON f.product_id = p.product_id
            JOIN tw_dim_location l ON f.location_id = l.location_id
            WHERE f.qty < $1
              AND f.snapshot_date = (
                  SELECT MAX(snapshot_date)
                  FROM tw_fact_inventory_snapshot
              )
            ORDER BY f.qty ASC
            """

            # ✅ MUST use base class execute_sql method
            result = await super().execute_sql(sql, [threshold])

            return result or []

        except Exception as e:
            logger.error(f"取得低庫存商品失敗: {e}")
            raise

    async def get_inventory_by_product(
        self,
        sku: str,
        snapshot_date: date | None = None
    ) -> list[dict]:
        """根據產品 SKU 取得庫存明細"""
        try:
            sql = """
            SELECT
                f.*,
                p.sku,
                p.descr as product_name,
                l.facility_code,
                l.loc_code,
                l.sloc_code,
                lot.lot_code,
                lot.manf_date,
                lot.dc_stop_ship_date
            FROM tw_fact_inventory_snapshot f
            JOIN tw_dim_product p ON f.product_id = p.product_id
            JOIN tw_dim_location l ON f.location_id = l.location_id
            LEFT JOIN tw_dim_lot lot ON f.lot_id = lot.lot_id
            WHERE p.sku = $1
              AND ($2::date IS NULL OR f.snapshot_date = $2::date)
            ORDER BY f.snapshot_date DESC, l.facility_code, l.loc_code
            """

            date_param = snapshot_date.isoformat() if snapshot_date else None
            # ✅ MUST use base class execute_sql method
            result = await super().execute_sql(sql, [sku, date_param])

            return result or []

        except Exception as e:
            logger.error(f"根據產品取得庫存明細失敗 ({sku}): {e}")
            raise
