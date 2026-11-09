from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.deps import get_current_user
from ..models import User, Customer, FollowUp, SalesOrder, Receivable
from ..schemas import FollowUpIn, FollowUpOut

router = APIRouter(tags=["crm"])

PROTECT_DAYS = 15  # 私客保护期


@router.get("/customers/{cid}/overview")
def overview(cid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """客户 360° 视图：档案 + 订单 + 应收 + 跟进时间线。"""
    c = db.get(Customer, cid)
    if not c:
        raise HTTPException(404, "客户不存在")
    orders = (
        db.query(SalesOrder)
        .filter(SalesOrder.customer_id == cid)
        .order_by(SalesOrder.id.desc()).limit(20).all()
    )
    receivables = db.query(Receivable).filter(Receivable.customer_id == cid).all()
    outstanding = sum(r.amount - r.paid_amount for r in receivables if r.status != "SETTLED")
    follows = (
        db.query(FollowUp)
        .filter(FollowUp.customer_id == cid)
        .order_by(FollowUp.id.desc()).limit(50).all()
    )
    return {
        "customer": {
            "id": c.id, "code": c.code, "name": c.name, "level": c.level,
            "credit_limit": c.credit_limit, "total_sales": c.total_sales,
            "contact": c.contact, "phone": c.phone, "address": c.address,
            "in_public_pool": c.public_at is not None and c.public_at < datetime.now(),
        },
        "outstanding_receivable": outstanding,
        "orders": [
            {"order_no": o.order_no, "status": o.status,
             "total_amount": o.total_amount, "created_at": o.created_at}
            for o in orders
        ],
        "follow_ups": [
            {"id": f.id, "method": f.method, "content": f.content,
             "created_at": f.created_at, "next_follow_at": f.next_follow_at}
            for f in follows
        ],
    }


@router.post("/customers/{cid}/follow-ups", response_model=FollowUpOut)
def add_follow(cid: int, body: FollowUpIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """新增跟进记录，并顺延客户保护期。"""
    c = db.get(Customer, cid)
    if not c:
        raise HTTPException(404, "客户不存在")
    f = FollowUp(customer_id=cid, method=body.method, content=body.content,
                 next_follow_at=body.next_follow_at, created_by=user.id)
    c.public_at = datetime.now() + timedelta(days=PROTECT_DAYS)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.get("/public-pool")
def public_pool(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """公海客户：保护期已到期。"""
    rows = db.query(Customer).filter(Customer.public_at < datetime.now()).all()
    return [
        {"id": c.id, "code": c.code, "name": c.name, "level": c.level,
         "total_sales": c.total_sales, "expired_at": c.public_at}
        for c in rows
    ]


@router.post("/customers/{cid}/claim")
def claim(cid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """从公海领取客户，重置保护期。"""
    c = db.get(Customer, cid)
    if not c:
        raise HTTPException(404, "客户不存在")
    c.owner_id = user.id
    c.public_at = datetime.now() + timedelta(days=PROTECT_DAYS)
    db.commit()
    return {"message": f"客户 {c.name} 已领取", "protect_until": c.public_at}
