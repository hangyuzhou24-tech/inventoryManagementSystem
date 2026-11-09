"""单号发号器：基于数据库持久化计数器，重启/迁移后自动从存量单号续号。

用法：order_no = next_no(db, "SO", SalesOrder)
"""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import SeqCounter


def next_no(db: Session, prefix: str, model) -> str:
    today = datetime.now().strftime("%Y%m%d")
    counter = db.get(SeqCounter, (prefix, today))
    if counter is None:
        # 首次生成当日单号时，从已有数据中取最大序号（兼容迁移/重启场景）
        max_seq = 0
        like = f"{prefix}{today}-%"
        for (no,) in db.query(model.order_no).filter(model.order_no.like(like)).all():
            try:
                max_seq = max(max_seq, int(no.rsplit("-", 1)[1]))
            except (ValueError, IndexError):
                pass
        counter = SeqCounter(prefix=prefix, day=today, value=max_seq)
        db.add(counter)
        db.flush()
    counter.value += 1
    return f"{prefix}{today}-{counter.value:04d}"
