from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from .core.config import settings
from .core.security import hash_password
from . import models  # noqa: F401 确保模型注册
from .models import User, Warehouse
from .routers import auth, master, purchase, sales, inventory, crm, finance, reports

app = FastAPI(title=settings.APP_NAME, version="1.0.0",
              description="进销存 + 客户管理系统 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, master, purchase, sales, inventory, crm, finance, reports):
    app.include_router(r.router, prefix="/api/v1")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 初始化：管理员账号 + 默认仓库
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", real_name="管理员",
                        hashed_password=hash_password("admin123"), role="admin"))
        if not db.query(Warehouse).filter(Warehouse.is_default).first():
            db.add(Warehouse(name="总仓", is_default=True))
        db.commit()
    finally:
        db.close()


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
