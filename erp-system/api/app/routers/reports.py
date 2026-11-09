from datetime import datetime, date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.deps import get_current_user
from ..models import (User, SalesOrder, PurchaseOrder, Receivable, Payable,
                      Customer, Product, Inventory)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    month_start = today.replace(day=1)

    orders = db.query(SalesOrder).filter(
        SalesOrder.status.in_(("SHIPPED", "CLOSED"))).all()
    today_sales = sum(o.total_amount for o in orders if o.shipped_at and o.shipped_at.date() == today)
    month_sales = sum(o.total_amount for o in orders if o.shipped_at and o.shipped_at.date() >= month_start)

    rec = db.query(Receivable).filter(Receivable.status != "SETTLED").all()
    pay = db.query(Payable).filter(Payable.status != "SETTLED").all()

    lows = (
        db.query(Inventory, Product)
        .join(Product, Inventory.product_id == Product.id)
        .filter(Product.safety_stock > 0).all()
    )
    low_stock_count = sum(1 for inv, p in lows if inv.qty_available < p.safety_stock)

    recent = db.query(SalesOrder).order_by(SalesOrder.id.desc()).limit(8).all()
    cust_names = {c.id: c.name for c in db.query(Customer).all()}

    return {
        "today_sales": today_sales,
        "month_sales": month_sales,
        "receivable_open": sum(r.amount - r.paid_amount for r in rec),
        "payable_open": sum(p.amount - p.paid_amount for p in pay),
        "customer_count": db.query(Customer).count(),
        "product_count": db.query(Product).count(),
        "low_stock_count": low_stock_count,
        "recent_orders": [
            {"order_no": o.order_no, "customer": cust_names.get(o.customer_id, ""),
             "status": o.status, "total_amount": o.total_amount, "created_at": o.created_at}
            for o in recent
        ],
    }


@router.get("/customer-ranking")
def customer_ranking(top: int = 10, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(Customer)
        .filter(Customer.total_sales > 0)
        .order_by(Customer.total_sales.desc())
        .limit(top).all()
    )
    return [{"name": c.name, "level": c.level, "total_sales": c.total_sales} for c in rows]
