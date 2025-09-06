from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import date, datetime

# Auth
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

# Transactions
class TransactionBase(BaseModel):
    account: str = "Main"
    date: date
    amount: float
    merchant: str = ""
    description: str = ""
    category: str = "Uncategorized"
    source: str = "manual"
    unique_hash: str

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionsQuery(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    category: Optional[str] = None

# Analytics
class SummaryOut(BaseModel):
    total_income: float
    total_expense: float
    by_category: Dict[str, float]
    by_month: Dict[str, float]


# ML
class MLPredictIn(BaseModel):
    merchant: str = ""
    description: str = ""
    amount: float = 0.0
    date: Optional[date] = None

class MLPredictOut(BaseModel):
    category: str
    confidence: float

class BudgetCreate(BaseModel):
    category: str
    monthly_limit: float

class BudgetOut(BaseModel):
    id: int
    category: str
    monthly_limit: float
    created_at: datetime
    class Config:
        from_attributes = True

class BudgetProgressOut(BaseModel):
    category: str
    monthly_limit: float
    actual: float
    remaining: float
    month: str
