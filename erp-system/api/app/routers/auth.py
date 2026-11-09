from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..core.deps import get_current_user
from ..core.security import authenticate_user, create_access_token, hash_password
from ..models import User, Warehouse, Customer
from ..schemas import LoginIn, TokenOut, UserOut, Msg

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id, user.role)
    return TokenOut(access_token=token, role=user.role, real_name=user.real_name)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/register", response_model=Msg)
def register(body: LoginIn, db: Session = Depends(get_db)):
    """开放注册仅限开发调试；生产环境应由管理员创建用户。"""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    db.add(User(username=body.username, hashed_password=hash_password(body.password)))
    db.commit()
    return Msg(message="注册成功")


@router.post("/seed-demo", response_model=Msg)
def seed_demo(db: Session = Depends(get_db)):
    """初始化演示数据：默认仓库与客户。"""
    if not db.query(Warehouse).first():
        db.add(Warehouse(name="总仓", is_default=True))
    if not db.query(Customer).first():
        db.add(Customer(code="C001", name="示例客户", credit_limit=50000, level="A"))
    db.commit()
    return Msg(message="演示数据已就绪")
