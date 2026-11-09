"""库存服务：所有库存变更必须经由本模块，保证「更新库存 + 写流水」在同一事务内。"""
from sqlalchemy.orm import Session

from ..models import Inventory, StockMove


def get_or_create(db: Session, product_id: int, warehouse_id: int) -> Inventory:
    inv = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id, Inventory.warehouse_id == warehouse_id)
        .first()
    )
    if inv is None:
        inv = Inventory(product_id=product_id, warehouse_id=warehouse_id,
                        qty_available=0, qty_locked=0)
        db.add(inv)
        db.flush()
    return inv


def adjust(db: Session, product_id: int, warehouse_id: int, qty: float,
           move_type: str, ref_no: str, remark: str = "", user_id: int | None = None) -> Inventory:
    """qty 正数=入库，负数=出库。只增不改流水。"""
    inv = get_or_create(db, product_id, warehouse_id)
    inv.qty_available += qty
    move = StockMove(
        move_type=move_type, product_id=product_id, warehouse_id=warehouse_id,
        qty=qty, ref_no=ref_no, remark=remark, created_by=user_id,
    )
    db.add(move)
    return inv


def lock(db: Session, product_id: int, warehouse_id: int, qty: float) -> None:
    """预占库存（下单审核时）。"""
    inv = get_or_create(db, product_id, warehouse_id)
    if inv.qty_available < qty:
        raise ValueError(
            f"库存不足：可用 {inv.qty_available}，需预占 {qty}"
        )
    inv.qty_available -= qty
    inv.qty_locked += qty


def unlock(db: Session, product_id: int, warehouse_id: int, qty: float) -> None:
    """释放预占（取消订单）。"""
    inv = get_or_create(db, product_id, warehouse_id)
    inv.qty_locked -= qty
    inv.qty_available += qty


def ship(db: Session, product_id: int, warehouse_id: int, qty: float,
         ref_no: str, user_id: int | None = None) -> None:
    """出库：从预占扣减并写 SALES_OUT 流水。"""
    inv = get_or_create(db, product_id, warehouse_id)
    if inv.qty_locked < qty:
        raise ValueError(f"预占数量不足：预占 {inv.qty_locked}，出库 {qty}")
    inv.qty_locked -= qty
    db.add(StockMove(move_type="SALES_OUT", product_id=product_id,
                     warehouse_id=warehouse_id, qty=-qty, ref_no=ref_no, created_by=user_id))
