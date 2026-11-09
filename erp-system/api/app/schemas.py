from datetime import datetime, date
from pydantic import BaseModel, Field


# ---------- Auth ----------
class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    real_name: str


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    role: str

    class Config:
        from_attributes = True


# ---------- Product ----------
class ProductIn(BaseModel):
    sku: str
    name: str
    unit: str = "件"
    barcode: str = ""
    purchase_price: float = 0
    sale_price: float = 0
    safety_stock: int = 0


class ProductOut(ProductIn):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


# ---------- Supplier ----------
class SupplierIn(BaseModel):
    code: str
    name: str
    contact: str = ""
    phone: str = ""
    payment_terms_days: int = 30


class SupplierOut(SupplierIn):
    id: int

    class Config:
        from_attributes = True


# ---------- Customer ----------
class CustomerIn(BaseModel):
    code: str
    name: str
    contact: str = ""
    phone: str = ""
    address: str = ""
    credit_limit: float = 0


class CustomerOut(CustomerIn):
    id: int
    level: str
    owner_id: int | None = None
    public_at: datetime | None = None
    total_sales: float

    class Config:
        from_attributes = True


# ---------- Purchase ----------
class PurchaseItemIn(BaseModel):
    product_id: int
    qty: float = Field(gt=0)
    price: float = Field(ge=0)


class PurchaseOrderIn(BaseModel):
    supplier_id: int
    remark: str = ""
    items: list[PurchaseItemIn]


class PurchaseReceiveIn(BaseModel):
    """部分到货：只传本次入库的商品与数量；不传则全部入库。"""
    items: list[PurchaseItemIn] | None = None


class OrderOut(BaseModel):
    id: int
    order_no: str
    status: str
    total_amount: float
    remark: str
    created_at: datetime
    items: list[dict] = []

    class Config:
        from_attributes = True


# ---------- Sales ----------
class SalesItemIn(BaseModel):
    product_id: int
    qty: float = Field(gt=0)
    price: float = Field(ge=0)


class SalesOrderIn(BaseModel):
    customer_id: int
    remark: str = ""
    items: list[SalesItemIn]


# ---------- Inventory ----------
class InventoryOut(BaseModel):
    product_id: int
    sku: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    qty_available: float
    qty_locked: float
    safety_stock: int


class StockMoveOut(BaseModel):
    id: int
    move_type: str
    product_id: int
    qty: float
    ref_no: str
    remark: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- CRM ----------
class FollowUpIn(BaseModel):
    method: str = "phone"
    content: str
    next_follow_at: datetime | None = None


class FollowUpOut(FollowUpIn):
    id: int
    customer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Finance ----------
class PaymentIn(BaseModel):
    amount: float = Field(gt=0)


# ---------- Common ----------
class Msg(BaseModel):
    message: str


class DashboardOut(BaseModel):
    today_sales: float
    month_sales: float
    receivable_open: float
    payable_open: float
    customer_count: int
    product_count: int
    low_stock_count: int
    recent_orders: list[dict] = []
