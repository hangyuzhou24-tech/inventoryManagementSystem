from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.deps import get_current_user
from ..models import User, Product, Supplier, Customer, Warehouse
from ..schemas import ProductIn, ProductOut, SupplierIn, SupplierOut, CustomerIn, CustomerOut

router = APIRouter(tags=["master-data"])


# ---------- 商品 ----------
@router.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Product).order_by(Product.id.desc()).all()


@router.post("/products", response_model=ProductOut)
def create_product(body: ProductIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Product).filter(Product.sku == body.sku).first():
        raise HTTPException(400, "SKU 已存在")
    p = Product(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/products/{pid}", response_model=ProductOut)
def update_product(pid: int, body: ProductIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "商品不存在")
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


# ---------- 供应商 ----------
@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Supplier).order_by(Supplier.id.desc()).all()


@router.post("/suppliers", response_model=SupplierOut)
def create_supplier(body: SupplierIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Supplier).filter(Supplier.code == body.code).first():
        raise HTTPException(400, "供应商编码已存在")
    s = Supplier(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ---------- 客户 ----------
@router.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Customer).order_by(Customer.id.desc()).all()


@router.post("/customers", response_model=CustomerOut)
def create_customer(body: CustomerIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Customer).filter(Customer.code == body.code).first():
        raise HTTPException(400, "客户编码已存在")
    c = Customer(**body.model_dump(), owner_id=user.id,
                 public_at=__import__("datetime").datetime.now() + __import__("datetime").timedelta(days=15))
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/warehouses")
def list_warehouses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [{"id": w.id, "name": w.name, "is_default": w.is_default}
            for w in db.query(Warehouse).all()]
