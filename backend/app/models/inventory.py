"""
Inventory 相關的資料模型
定義庫存維度和事實表的 Pydantic 模型
"""
from datetime import date, datetime

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """產品基礎模型"""
    sku: str = Field(..., description="產品代碼")
    descr: str | None = Field(None, description="產品描述")
    brand_name: str | None = Field(None, description="品牌名稱")
    skugroup_name: str | None = Field(None, description="產品群組名稱")
    ean: str | None = Field(None, description="EAN 條碼")
    itf14: str | None = Field(None, description="ITF14 條碼")
    is_active: bool = Field(True, description="是否啟用")


class Product(ProductBase):
    """產品完整模型"""
    product_id: int = Field(..., description="產品 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    class Config:
        from_attributes = True


class ProductCreate(ProductBase):
    """建立產品模型"""
    pass


class ProductUpdate(BaseModel):
    """更新產品模型"""
    descr: str | None = None
    brand_name: str | None = None
    skugroup_name: str | None = None
    ean: str | None = None
    itf14: str | None = None
    is_active: bool | None = None


class LocationBase(BaseModel):
    """地點基礎模型"""
    facility_code: str = Field(..., description="倉庫代碼")
    loc_code: str = Field(..., description="地點代碼")
    sloc_code: str | None = Field(None, description="子地點代碼")
    facility_name: str | None = Field(None, description="倉庫名稱")


class Location(LocationBase):
    """地點完整模型"""
    location_id: int = Field(..., description="地點 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    class Config:
        from_attributes = True


class LocationCreate(LocationBase):
    """建立地點模型"""
    pass


class LotBase(BaseModel):
    """批號基礎模型"""
    lot_code: str = Field(..., description="批號代碼")
    product_id: int = Field(..., description="產品 ID")
    facility_code: str | None = Field(None, description="倉庫代碼")
    manf_date: date | None = Field(None, description="製造日期")
    receipt_date: date | None = Field(None, description="入庫日期")
    shelf_life_days: int | None = Field(None, description="保存期限天數")
    dc_stop_ship_date: date | None = Field(None, description="停止出貨日期")
    stop_ship_lead_days: int | None = Field(None, description="停止出貨提前天數")
    reason_code: str | None = Field(None, description="原因代碼")
    reason_desc: str | None = Field(None, description="原因描述")
    remark: str | None = Field(None, description="備註")


class Lot(LotBase):
    """批號完整模型"""
    lot_id: int = Field(..., description="批號 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    class Config:
        from_attributes = True


class LotCreate(LotBase):
    """建立批號模型"""
    pass


class InventorySnapshotBase(BaseModel):
    """庫存快照基礎模型"""
    snapshot_date: date = Field(..., description="快照日期")
    product_id: int = Field(..., description="產品 ID")
    location_id: int = Field(..., description="地點 ID")
    lot_id: int | None = Field(None, description="批號 ID")
    qty: float = Field(0, description="數量")
    bqty: float | None = Field(0, description="B數量")
    qty_allocated: float | None = Field(0, description="已分配數量")
    case_cnt: float | None = Field(0, description="箱數")
    buom_code: str | None = Field(None, description="基本單位代碼")
    source_system: str = Field("WMS", description="來源系統")
    source_row_key: str | None = Field(None, description="來源行鍵")


class InventorySnapshot(InventorySnapshotBase):
    """庫存快照完整模型"""
    snapshot_id: int = Field(..., description="快照 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    class Config:
        from_attributes = True


class InventorySnapshotCreate(InventorySnapshotBase):
    """建立庫存快照模型"""
    pass


class InventorySummary(BaseModel):
    """庫存摘要模型"""
    sku: str = Field(..., description="產品代碼")
    product_name: str | None = Field(None, description="產品名稱")
    brand_name: str | None = Field(None, description="品牌名稱")
    facility_code: str = Field(..., description="倉庫代碼")
    total_qty: float = Field(0, description="總數量")
    total_bqty: float = Field(0, description="總B數量")
    total_allocated: float = Field(0, description="總已分配數量")
    location_count: int = Field(0, description="地點數量")

    class Config:
        from_attributes = True


class LowStockItem(BaseModel):
    """低庫存商品模型"""
    sku: str = Field(..., description="產品代碼")
    product_name: str | None = Field(None, description="產品名稱")
    facility_code: str = Field(..., description="倉庫代碼")
    loc_code: str = Field(..., description="地點代碼")
    qty: float = Field(..., description="數量")
    qty_allocated: float = Field(..., description="已分配數量")
    snapshot_date: date = Field(..., description="快照日期")

    class Config:
        from_attributes = True


class InventoryDetail(BaseModel):
    """庫存明細模型"""
    snapshot_id: int = Field(..., description="快照 ID")
    snapshot_date: date = Field(..., description="快照日期")
    product_id: int = Field(..., description="產品 ID")
    location_id: int = Field(..., description="地點 ID")
    lot_id: int | None = Field(None, description="批號 ID")
    qty: float = Field(..., description="數量")
    bqty: float | None = Field(None, description="B數量")
    qty_allocated: float | None = Field(None, description="已分配數量")
    case_cnt: float | None = Field(None, description="箱數")
    buom_code: str | None = Field(None, description="基本單位代碼")
    source_system: str = Field(..., description="來源系統")
    source_row_key: str | None = Field(None, description="來源行鍵")

    # 關聯資料
    sku: str = Field(..., description="產品代碼")
    product_name: str | None = Field(None, description="產品名稱")
    facility_code: str = Field(..., description="倉庫代碼")
    loc_code: str = Field(..., description="地點代碼")
    sloc_code: str | None = Field(None, description="子地點代碼")
    lot_code: str | None = Field(None, description="批號代碼")
    manf_date: date | None = Field(None, description="製造日期")
    dc_stop_ship_date: date | None = Field(None, description="停止出貨日期")

    class Config:
        from_attributes = True


class ExpiringLot(BaseModel):
    """即將過期批號模型"""
    lot_id: int = Field(..., description="批號 ID")
    lot_code: str = Field(..., description="批號代碼")
    product_id: int = Field(..., description="產品 ID")
    facility_code: str | None = Field(None, description="倉庫代碼")
    manf_date: date | None = Field(None, description="製造日期")
    receipt_date: date | None = Field(None, description="入庫日期")
    shelf_life_days: int | None = Field(None, description="保存期限天數")
    dc_stop_ship_date: date | None = Field(None, description="停止出貨日期")
    stop_ship_lead_days: int | None = Field(None, description="停止出貨提前天數")

    # 關聯產品資料
    sku: str = Field(..., description="產品代碼")
    product_name: str | None = Field(None, description="產品名稱")

    class Config:
        from_attributes = True
