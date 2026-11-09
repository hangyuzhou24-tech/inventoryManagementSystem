from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.deps import get_current_user
from ..models import User, Receivable, Payable, Customer, SalesOrder
from ..schemas import PaymentIn

router = APIRouter(tags=["finance"])


@router.get("/receivables")
def receivables(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Receivable, Customer).join(
        Customer, Receivable.customer_id == Customer.id
    ).order_by(Receivable.id.desc()).all()
    return [
        {
            "id": r.id, "order_no": r.order_no, "customer_name": c.name,
            "amount": r.amount, "paid_amount": r.paid_amount,
            "remaining": r.amount - r.paid_amount, "status": r.status,
            "due_date": r.due_date, "overdue": bool(r.due_date and r.due_date < date.today() and r.status != "SETTLED"),
        }
        for r, c in rows
    ]


@router.get("/payables")
def payables(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Payable).order_by(Payable.id.desc()).all()
    return [
        {"id": p.id, "order_no": p.order_no, "supplier_id": p.supplier_id,
         "amount": p.amount, "paid_amount": p.paid_amount,
         "remaining": p.amount - p.paid_amount, "status": p.status}
        for p in rows
    ]


@router.post("/receivables/{rid}/payment")
def receive_payment(rid: int, body: PaymentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """收款核销：更新应收余额。一笔收款只核销当前应收单（一单多核后续扩展）。"""
    r = db.get(Receivable, rid)
    if not r:
        raise HTTPException(404, "应收单不存在")
    if r.status == "SETTLED":
        raise HTTPException(400, "该应收单已结清")
    r.paid_amount += body.amount
    if r.paid_amount >= r.amount:
        r.paid_amount = r.amount
        r.status = "SETTLED"
        # 全部结清后检查是否还有未核销应收（信用占用）
        still_open = (
            db.query(Receivable)
            .filter(Receivable.customer_id == r.customer_id,
                    Receivable.status != "SETTLED")
            .count()
        )
        if still_open == 0:
            so = db.query(SalesOrder).filter(
                SalesOrder.order_no == r.order_no).first()
            if so:
                so.status = "CLOSED"
    else:
        r.status = "PARTIAL"
    db.commit()
    return {"message": "核销成功", "paid_amount": r.paid_amount, "status": r.status}
