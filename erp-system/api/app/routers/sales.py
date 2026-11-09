from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.config import settings
from ..core.deps import get_current_user
from ..models import (User, SalesOrder, SalesOrderItem, Customer,
                      Product, Receivable, Warehouse)
from ..schemas import SalesOrderIn, OrderOut
from ..services import inventory as inv_service
from ..services.sequences import next_no

router = APIRouter(prefix="/sales-orders", tags=["sales"])


def _so_dict(so: SalesOrder) -> dict:
    return {
        "id": so.id, "order_no": so.order_no, "status": so.status,
        "total_amount": so.total_amount, "remark": so.remark,
        "customer_id": so.customer_id, "pending_reason": so.pending_reason,
        "created_at": so.created_at, "shipped_at": so.shipped_at,
        "items": [
            {"id": i.id, "product_id": i.product_id, "qty": i.qty,
             "shipped_qty": i.shipped_qty, "price": i.price}
            for i in so.items
        ],
    }


def _outstanding_receivables(db: Session, customer_id: int) -> float:
    rows = db.query(Receivable).filter(
        Receivable.customer_id == customer_id,
        Receivable.status != "SETTLED",
    ).all()
    return sum(r.amount - r.paid_amount for r in rows)


@router.get("", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sos = db.query(SalesOrder).order_by(SalesOrder.id.desc()).all()
    return [_so_dict(so) for so in sos]


@router.post("", response_model=dict)
def create_order(body: SalesOrderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    customer = db.get(Customer, body.customer_id)
    if not customer:
        raise HTTPException(404, "客户不存在")
    total = sum(i.qty * i.price for i in body.items)
    so = SalesOrder(order_no=next_no(db, "SO", SalesOrder), customer_id=body.customer_id,
                    total_amount=total, remark=body.remark, created_by=user.id)
    for i in body.items:
        p = db.get(Product, i.product_id)
        if not p:
            raise HTTPException(404, f"商品 {i.product_id} 不存在")
        so.items.append(SalesOrderItem(product_id=i.product_id, qty=i.qty, price=i.price))

    # 信用额度校验：未核销应收 + 本单金额 > 信用额度 → 转审批
    outstanding = _outstanding_receivables(db, customer.id)
    if customer.credit_limit > 0 and outstanding + total > customer.credit_limit:
        so.status = "PENDING_APPROVAL"
        so.pending_reason = (
            f"超信用额度：已占用 {outstanding:.2f} + 本单 {total:.2f} > 额度 {customer.credit_limit:.2f}"
        )
    db.add(so)
    db.commit()
    result = _so_dict(so)
    result["credit_warning"] = so.status == "PENDING_APPROVAL"
    return result


@router.post("/{oid}/approve", response_model=OrderOut)
def approve(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """审核通过 → 预占库存；PENDING_APPROVAL 的单据由管理员审批放行。"""
    so = db.get(SalesOrder, oid)
    if not so:
        raise HTTPException(404, "销售单不存在")
    if so.status not in ("DRAFT", "PENDING_APPROVAL"):
        raise HTTPException(400, f"当前状态 {so.status} 不允许审核")
    wh = db.query(Warehouse).filter(Warehouse.is_default).first()
    if not wh:
        raise HTTPException(400, "未配置默认仓库")
    try:
        for i in so.items:
            inv_service.lock(db, i.product_id, wh.id, i.qty)
    except ValueError as e:
        db.rollback()
        raise HTTPException(400, str(e))
    so.status = "APPROVED"
    so.pending_reason = ""
    db.commit()
    return _so_dict(so)


@router.post("/{oid}/ship", response_model=OrderOut)
def ship(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """出库：释放预占 → 扣库存写流水 → 生成应收 → 更新客户累计销售。"""
    so = db.get(SalesOrder, oid)
    if not so:
        raise HTTPException(404, "销售单不存在")
    if so.status != "APPROVED":
        raise HTTPException(400, f"当前状态 {so.status} 不允许出库，请先审核")
    wh = db.query(Warehouse).filter(Warehouse.is_default).first()
    try:
        for i in so.items:
            inv_service.ship(db, i.product_id, wh.id, i.qty, so.order_no, user_id=user.id)
            i.shipped_qty = i.qty
    except ValueError as e:
        db.rollback()
        raise HTTPException(400, str(e))

    so.status = "SHIPPED"
    so.shipped_at = datetime.now()
    db.add(Receivable(order_no=so.order_no, customer_id=so.customer_id,
                      amount=so.total_amount,
                      due_date=datetime.now() + timedelta(days=30)))
    customer = db.get(Customer, so.customer_id)
    customer.total_sales += so.total_amount
    db.commit()
    return _so_dict(so)


@router.post("/{oid}/cancel", response_model=OrderOut)
def cancel(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    so = db.get(SalesOrder, oid)
    if not so:
        raise HTTPException(404, "销售单不存在")
    if so.status == "APPROVED":
        wh = db.query(Warehouse).filter(Warehouse.is_default).first()
        for i in so.items:
            inv_service.unlock(db, i.product_id, wh.id, i.qty)
    elif so.status in ("SHIPPED", "CLOSED"):
        raise HTTPException(400, "已出库订单不可取消，请走销售退货流程")
    so.status = "CANCELLED"
    db.commit()
    return _so_dict(so)
