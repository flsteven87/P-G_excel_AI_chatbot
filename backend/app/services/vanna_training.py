"""
Vanna.AI 訓練資料初始化服務
基於現有庫存資料模型自動訓練 vanna.ai
"""
import logging

from .vanna_service import vanna_service

logger = logging.getLogger(__name__)


class VannaTrainingService:
    """處理 vanna.ai 模型的初始訓練和更新"""

    def __init__(self):
        self.business_vocabulary = self._get_business_vocabulary()
        self.sample_questions = self._get_sample_questions()

    async def initialize_training(self) -> bool:
        """初始化完整的 vanna.ai 訓練"""
        try:
            logger.info("開始初始化 vanna.ai 訓練資料...")

            # 1. 訓練資料庫結構 (DDL)
            await self._train_database_schema()

            # 2. 訓練商業詞彙
            await self._train_business_vocabulary()

            # 3. 訓練範例問答
            await self._train_sample_questions()

            logger.info("vanna.ai 訓練資料初始化完成")
            return True

        except Exception as e:
            logger.error(f"vanna.ai 訓練初始化失敗: {e}")
            return False

    async def _train_database_schema(self) -> None:
        """訓練資料庫結構"""
        # 庫存資料模型的完整 DDL
        schemas = [
            {
                "table": "tw_dim_product",
                "ddl": """CREATE TABLE tw_dim_product (
                    product_id BIGSERIAL PRIMARY KEY,
                    sku TEXT NOT NULL UNIQUE,
                    descr TEXT,
                    brand_name TEXT,
                    skugroup_name TEXT,
                    ean TEXT,
                    itf14 TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                );"""
            },
            {
                "table": "tw_dim_location",
                "ddl": """CREATE TABLE tw_dim_location (
                    location_id BIGSERIAL PRIMARY KEY,
                    facility_code TEXT NOT NULL,
                    loc_code TEXT NOT NULL,
                    sloc_code TEXT,
                    facility_name TEXT,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                );"""
            },
            {
                "table": "tw_dim_lot",
                "ddl": """CREATE TABLE tw_dim_lot (
                    lot_id BIGSERIAL PRIMARY KEY,
                    lot_code TEXT NOT NULL,
                    product_id BIGINT REFERENCES tw_dim_product(product_id),
                    facility_code TEXT,
                    manf_date DATE,
                    receipt_date DATE,
                    shelf_life_days INTEGER,
                    dc_stop_ship_date DATE,
                    stop_ship_lead_days INTEGER,
                    reason_code TEXT,
                    reason_desc TEXT,
                    remark TEXT,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                );"""
            },
            {
                "table": "tw_fact_inventory_snapshot",
                "ddl": """CREATE TABLE tw_fact_inventory_snapshot (
                    snapshot_id BIGSERIAL PRIMARY KEY,
                    snapshot_date DATE NOT NULL,
                    product_id BIGINT REFERENCES tw_dim_product(product_id),
                    location_id BIGINT REFERENCES tw_dim_location(location_id),
                    lot_id BIGINT REFERENCES tw_dim_lot(lot_id),
                    qty NUMERIC(18,3) DEFAULT 0,
                    bqty NUMERIC(18,3) DEFAULT 0,
                    qty_allocated NUMERIC(18,3) DEFAULT 0,
                    case_cnt NUMERIC(18,3) DEFAULT 0,
                    buom_code TEXT,
                    source_system TEXT DEFAULT 'WMS',
                    source_row_key TEXT,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now()
                );"""
            }
        ]

        for schema in schemas:
            await vanna_service.train_with_ddl(schema["ddl"], schema["table"])
            logger.info(f"已訓練資料表結構: {schema['table']}")

    async def _train_business_vocabulary(self) -> None:
        """訓練商業詞彙和同義詞"""
        for term, definition in self.business_vocabulary.items():
            doc = f"商業術語 '{term}': {definition}"
            await vanna_service.train_with_documentation(doc)
            logger.info(f"已訓練商業詞彙: {term}")

    async def _train_sample_questions(self) -> None:
        """訓練範例問答對"""
        for question, sql in self.sample_questions:
            await vanna_service.train_with_sql(question, sql)
            logger.info(f"已訓練問答對: {question[:30]}...")

    def _get_business_vocabulary(self) -> dict[str, str]:
        """庫存管理相關的商業詞彙定義"""
        return {
            "庫存": "inventory, stock, quantity on hand - 指產品在倉庫中的現有數量",
            "SKU": "Stock Keeping Unit, product code - 產品識別代碼，每個產品的唯一標識",
            "品牌": "brand, manufacturer - 產品品牌或製造商名稱",
            "批號": "lot, batch - 產品批次編號，用於追蹤產品生產批次",
            "倉庫": "facility, warehouse - 儲存產品的物理位置",
            "庫位": "location, bin - 倉庫內的具體儲存位置",
            "分配量": "allocated quantity - 已分配但尚未出貨的庫存量",
            "可用庫存": "available stock - 總庫存減去分配量後的可用數量",
            "保質期": "shelf life, expiry date - 產品的有效期限",
            "停出貨": "stop shipment - 因品質或過期等原因停止出貨",
            "EAN": "European Article Number - 歐洲商品編號，國際通用條碼",
            "ITF-14": "Interleaved Two of Five - 物流條碼，用於外包裝",
            "箱數": "case count - 產品的包裝箱數量",
            "單位": "unit of measure - 產品的計量單位",
            "入庫日": "receipt date - 產品入庫的日期",
            "製造日": "manufacturing date - 產品的生產日期"
        }

    def _get_sample_questions(self) -> list[tuple[str, str]]:
        """預設的問答範例，用於訓練模型"""
        return [
            (
                "顯示庫存量前10的產品",
                """SELECT 
                    dp.sku, 
                    dp.descr, 
                    dp.brand_name, 
                    SUM(f.qty) as total_qty
                FROM tw_fact_inventory_snapshot f
                JOIN tw_dim_product dp ON dp.product_id = f.product_id
                WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                GROUP BY dp.sku, dp.descr, dp.brand_name
                ORDER BY total_qty DESC
                LIMIT 10;"""
            ),
            (
                "按品牌統計總庫存量",
                """SELECT 
                    dp.brand_name,
                    COUNT(DISTINCT dp.sku) as product_count,
                    SUM(f.qty) as total_qty
                FROM tw_fact_inventory_snapshot f
                JOIN tw_dim_product dp ON dp.product_id = f.product_id
                WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                GROUP BY dp.brand_name
                ORDER BY total_qty DESC;"""
            ),
            (
                "哪些產品庫存不足100件",
                """SELECT 
                    dp.sku,
                    dp.descr,
                    dp.brand_name,
                    SUM(f.qty) as current_qty
                FROM tw_fact_inventory_snapshot f
                JOIN tw_dim_product dp ON dp.product_id = f.product_id
                WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                GROUP BY dp.sku, dp.descr, dp.brand_name
                HAVING SUM(f.qty) < 100
                ORDER BY current_qty ASC;"""
            ),
            (
                "各倉庫的總庫存量",
                """SELECT 
                    dl.facility_code,
                    dl.facility_name,
                    COUNT(DISTINCT f.product_id) as product_types,
                    SUM(f.qty) as total_qty
                FROM tw_fact_inventory_snapshot f
                JOIN tw_dim_location dl ON dl.location_id = f.location_id
                WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                GROUP BY dl.facility_code, dl.facility_name
                ORDER BY total_qty DESC;"""
            ),
            (
                "即將停出貨的產品(14天內)",
                """SELECT 
                    dp.sku,
                    dp.descr,
                    dp.brand_name,
                    lot.dc_stop_ship_date,
                    SUM(f.qty) as qty
                FROM tw_fact_inventory_snapshot f
                JOIN tw_dim_product dp ON dp.product_id = f.product_id
                JOIN tw_dim_lot lot ON lot.lot_id = f.lot_id
                WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                  AND lot.dc_stop_ship_date IS NOT NULL
                  AND lot.dc_stop_ship_date - CURRENT_DATE <= 14
                GROUP BY dp.sku, dp.descr, dp.brand_name, lot.dc_stop_ship_date
                ORDER BY lot.dc_stop_ship_date, qty DESC;"""
            ),
            (
                "顯示所有產品的平均庫存",
                """SELECT 
                    AVG(total_qty) as avg_inventory
                FROM (
                    SELECT 
                        SUM(f.qty) as total_qty
                    FROM tw_fact_inventory_snapshot f
                    WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                    GROUP BY f.product_id
                ) as product_totals;"""
            ),
            (
                "庫存價值最高的前5個品牌",
                """SELECT 
                    dp.brand_name,
                    COUNT(DISTINCT dp.sku) as sku_count,
                    SUM(f.qty) as total_qty,
                    SUM(f.case_cnt) as total_cases
                FROM tw_fact_inventory_snapshot f
                JOIN tw_dim_product dp ON dp.product_id = f.product_id
                WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                  AND dp.brand_name IS NOT NULL
                GROUP BY dp.brand_name
                ORDER BY total_qty DESC
                LIMIT 5;"""
            ),
            (
                "哪些產品有分配但未出貨",
                """SELECT 
                    dp.sku,
                    dp.descr,
                    SUM(f.qty_allocated) as allocated_qty,
                    SUM(f.qty) as total_qty
                FROM tw_fact_inventory_snapshot f
                JOIN tw_dim_product dp ON dp.product_id = f.product_id
                WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM tw_fact_inventory_snapshot)
                  AND f.qty_allocated > 0
                GROUP BY dp.sku, dp.descr
                ORDER BY allocated_qty DESC;"""
            )
        ]


# 全局服務實例
vanna_training_service = VannaTrainingService()
