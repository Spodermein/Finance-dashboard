from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import hashlib
import pandas as pd

from fastapi import Response
from ..db import get_db
from .. import models
from ..schemas import TransactionCreate, TransactionOut
from ..deps import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

def compute_unique_hash(user_id: int, date_: date, amount: float, merchant: str) -> str:
    s = f"{user_id}|{date_.isoformat()}|{amount:.2f}|{merchant.lower()}"
    return hashlib.sha256(s.encode()).hexdigest()

@router.get("/", response_model=List[TransactionOut])
def list_transactions(start_date: Optional[date] = None,
                      end_date: Optional[date] = None,
                      category: Optional[str] = None,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(get_current_user)):
    q = db.query(models.Transaction).filter(models.Transaction.user_id == user.id)
    if start_date:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date:
        q = q.filter(models.Transaction.date <= end_date)
    if category:
        q = q.filter(models.Transaction.category == category)
    q = q.order_by(models.Transaction.date.desc(), models.Transaction.id.desc())
    return q.all()

@router.post("/", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(get_current_user)):
    # override unique hash to enforce user-scoped dedupe
    uh = compute_unique_hash(user.id, payload.date, payload.amount, payload.merchant or "")
    tx = models.Transaction(
        user_id=user.id, account=payload.account, date=payload.date, amount=payload.amount,
        merchant=payload.merchant, description=payload.description, category=payload.category,
        source=payload.source, unique_hash=uh
    )
    # dedupe
    exists = db.query(models.Transaction).filter(
        models.Transaction.user_id == user.id,
        models.Transaction.unique_hash == uh
    ).first()
    if exists:
        return exists
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.post("/import", response_model=List[TransactionOut])
async def import_csv(file: UploadFile = File(...),
                     db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    # Expect columns: date,amount,merchant,description,category(optional),account(optional)
    df = pd.read_csv(file.file)
    required = {"date","amount"}
    if not required.issubset(df.columns):
        raise HTTPException(status_code=400, detail="CSV must include at least date,amount columns")
    out = []
    for _, row in df.iterrows():
        date_val = pd.to_datetime(row.get("date")).date()
        amt = float(row.get("amount"))
        merchant = str(row.get("merchant") or "")
        desc = str(row.get("description") or "")
        cat = str(row.get("category") or "Uncategorized")
        acct = str(row.get("account") or "Main")
        uh = compute_unique_hash(user.id, date_val, amt, merchant)
        exists = db.query(models.Transaction).filter(
            models.Transaction.user_id == user.id,
            models.Transaction.unique_hash == uh
        ).first()
        if exists:
            out.append(exists)
            continue
        tx = models.Transaction(
            user_id=user.id, account=acct, date=date_val, amount=amt,
            merchant=merchant, description=desc, category=cat, source="csv", unique_hash=uh
        )
        db.add(tx)
        out.append(tx)
    db.commit()
    # refresh all
    for tx in out:
        db.refresh(tx)
    return out



@router.get("/export")
def export_csv(start_date: date | None = None,
               end_date: date | None = None,
               category: str | None = None,
               db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):

    q = db.query(models.Transaction).filter(models.Transaction.user_id == user.id)
    if start_date:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date:
        q = q.filter(models.Transaction.date <= end_date)
    if category:
        q = q.filter(models.Transaction.category == category)
    rows = q.order_by(models.Transaction.date.desc(), models.Transaction.id.desc()).all()

    import io, csv
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id","date","amount","merchant","description","category","account","source"])
    for t in rows:
        writer.writerow([t.id, t.date.isoformat(), float(t.amount), t.merchant,
                         t.description, t.category, t.account, t.source])
    return Response(content=buf.getvalue(), media_type="text/csv")
