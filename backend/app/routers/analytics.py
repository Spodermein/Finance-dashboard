from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, select
from collections import defaultdict
from datetime import date
from ..db import get_db
from .. import models
from ..deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
def summary(start_date: date | None = None, end_date: date | None = None,
            db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    q = db.query(models.Transaction).filter(models.Transaction.user_id == user.id)
    if start_date:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date:
        q = q.filter(models.Transaction.date <= end_date)
    rows = q.all()

    total_income = 0.0
    total_expense = 0.0
    by_category = defaultdict(float)
    by_month = defaultdict(float)

    for tx in rows:
        amt = float(tx.amount)
        if amt >= 0:
            total_income += amt
        else:
            total_expense += amt
        by_category[tx.category] += amt
        month_key = tx.date.strftime("%Y-%m")
        by_month[month_key] += amt

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "by_month": {k: round(v, 2) for k, v in by_month.items()},
    }
