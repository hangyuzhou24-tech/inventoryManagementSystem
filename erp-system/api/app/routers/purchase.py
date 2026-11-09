from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.deps import get_current_user
from ..models import User, PurchaseOrder, PurchaseOrderItem, Payable
from ..schemas import PurchaseOrderIn, PurchaseReceiveIn, OrderOut
from ..services import inventory as inv_service
from ..services.sequences import next_no

router = APIRouter(prefix="/purchase-orders", tags=["purchase"])


def _po_dict(po: PurchaseOrder) -> dict:
    return {
        "id": po.id, "order_no": po.order_no, "status": po.status,
        "total_amount": po.total_amount, "remark": po.remark,
        "supplier_id": po.supplier_id, "created_at": po.created_at,
        "items": [
            {"id": i.id, "product_id": i.product_id, "qty": i.qty,
             "received_qty": i.received_qty, "price": i.price}
            for i in po.items
        ],
    }


@router.get("", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pos = db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all()
    return [_po_dict(po) for po in pos]


@router.post("", response_model=dict)
def create_order(body: PurchaseOrderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    po = PurchaseOrder(
        order_no=next_no(db, "PO", PurchaseOrder), supplier_id=body.supplier_id,
        total_amount=sum(i.qty * i.price for i in body.items),
        remark=body.remark, created_by=user.id,
    )
    for i in body.items:
        po.items.append(PurchaseOrderItem(
            product_id=i.product_id, qty=i.qty, price=i.price))
    db.add(po)
    db.commit()
    return _po_dict(po)


@router.post("/{oid}/receive", response_model=dict)
def receive(oid: int, body: PurchaseReceiveIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """采购入库：支持部分到货。首次入库自动生成应付。"""
    po = db.get(PurchaseOrder, oid)
    if not po:
        raise HTTPException(404, "采购单不存在")
    if po.status in ("CLOSED", "CANCELLED"):
        raise HTTPException(400, "采购单已关闭或已取消")

    # 本次入库明细：缺省则未入库部分全部入库
    plan = {i.product_id: i for i in po.items}
    to_receive: dict[int, float] = {}
    if body.items:
        for i in body.items:
            if i.product_id not in plan:
                raise HTTPException(400, f"商品 {i.product_id} 不在该采购单中")
            if i.qty <= 0:
                raise HTTPException(400, "入库数量必须大于 0")
            to_receive[i.product_id] = i.qty
    else:
        for i in po.items:
            remain = i.qty - i.received_qty
            if remain > 0:
                to_receive[i.product_id] = remain

    for pid, qty in to_receive.items():
        item = plan[pid]
        if item.received_qty + qty > item.qty:
            raise HTTPException(400, f"入库数量超过采购数量（已收 {item.received_qty}）")
        item.received_qty += qty
        inv_service.adjust(db, pid, 1, qty, "PURCHASE_IN", po.order_no,
                           remark="采购入库", user_id=user.id)

    created_payable = False
    if po.status == "DRAFT":
        po.status = "RECEIVING"
        db.add(Payable(order_no=po.order_no, supplier_id=po.supplier_id,
                       amount=po.total_amount,
                       due_date=datetime.now() + timedelta(days=30)))
        created_payable = True

    # 全部到货则关闭
    if all(i.received_qty >= i.qty for i in po.items):
        po.status = "CLOSED"

    db.commit()
    result = _po_dict(po)
    result["created_payable"] = created_payable
    return result


@router.post("/{oid}/cancel", response_model=OrderOut)
def cancel(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    po = db.get(PurchaseOrder, oid)
    if not po:
        raise HTTPException(404, "采购单不存在")
    if po.status == "RECEIVING":
        raise HTTPException(400, "已有入库记录，不可取消，请走采购退货流程")
    po.status = "CANCELLED"
    db.commit()
    return _po_dict(po)
