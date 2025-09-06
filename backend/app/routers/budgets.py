from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from collections import defaultdict
from ..db import get_db
from .. import models
from ..schemas import BudgetCreate, BudgetOut, BudgetProgressOut
from ..deps import get_current_user

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.get("/", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Budget).filter(models.Budget.user_id == user.id).all()

@router.post("/", response_model=BudgetOut, status_code=201)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    exists = db.query(models.Budget).filter(
        models.Budget.user_id == user.id,
        models.Budget.category == payload.category
    ).first()
    if exists:
        raise HTTPException(400, "Budget for category already exists")
    b = models.Budget(user_id=user.id, category=payload.category, monthly_limit=payload.monthly_limit)
    db.add(b); db.commit(); db.refresh(b)
    return b

@router.get("/progress", response_model=list[BudgetProgressOut])
def budget_progress(month: str | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not month:
        month = date.today().strftime("%Y-%m")
    budgets = db.query(models.Budget).filter(models.Budget.user_id == user.id).all()
    txs = db.query(models.Transaction).filter(models.Transaction.user_id == user.id).all()
    by_cat = defaultdict(float)
    for t in txs:
        if t.date.strftime("%Y-%m") == month:
            by_cat[t.category] += float(t.amount)
    out = []
    for b in budgets:
        actual = by_cat.get(b.category, 0.0)
        spent = -actual if actual < 0 else 0.0  # expenses only
        remaining = float(b.monthly_limit) - spent
        out.append(BudgetProgressOut(
            category=b.category,
            monthly_limit=float(b.monthly_limit),
            actual=spent,
            remaining=remaining,
            month=month
        ))
    return out
