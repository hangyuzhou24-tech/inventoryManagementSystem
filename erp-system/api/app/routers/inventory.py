from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.deps import get_current_user
from ..models import User, Inventory, Product, Warehouse, StockMove
from ..schemas import InventoryOut, StockMoveOut

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/summary", response_model=list[InventoryOut])
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(Inventory, Product, Warehouse)
        .join(Product, Inventory.product_id == Product.id)
        .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        .order_by(Inventory.id)
        .all()
    )
    return [
        InventoryOut(
            product_id=inv.product_id, sku=p.sku, product_name=p.name,
            warehouse_id=inv.warehouse_id, warehouse_name=w.name,
            qty_available=inv.qty_available, qty_locked=inv.qty_locked,
            safety_stock=p.safety_stock,
        )
        for inv, p, w in rows
    ]


@router.get("/moves", response_model=list[StockMoveOut])
def moves(limit: int = 100, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(StockMove)
        .order_by(StockMove.id.desc())
        .limit(limit)
        .all()
    )


@router.get("/alerts")
def alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """安全库存预警：可用量低于安全库存的商品。"""
    rows = (
        db.query(Inventory, Product)
        .join(Product, Inventory.product_id == Product.id)
        .filter(Product.safety_stock > 0)
        .all()
    )
    return [
        {
            "product_id": p.id, "sku": p.sku, "product_name": p.name,
            "qty_available": inv.qty_available, "safety_stock": p.safety_stock,
            "shortage": p.safety_stock - inv.qty_available,
        }
        for inv, p in rows
        if inv.qty_available < p.safety_stock
    ]
