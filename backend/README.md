# Finance Dashboard Backend (FastAPI)

## Quick start
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
# (optional) copy env example
cp .env.example .env  # Windows: copy .env.example .env

# Train a sample ML model
python app/ml/train.py

# Run API
uvicorn app.main:app --reload --port 8000
```
API will be at http://localhost:8000 (docs at /docs).

## Auth
- POST `/auth/register` {email, password}
- POST `/auth/login` {email, password} → returns JWT
  - Use JWT as `Authorization: Bearer <token>` for all other endpoints.

## Transactions
- GET `/transactions` (filters: `start_date`, `end_date`, `category`)
- POST `/transactions` JSON body:
```json
{
  "account": "Main",
  "date": "2025-01-03",
  "amount": -4.5,
  "merchant": "Starbucks",
  "description": "Latte",
  "category": "Food & Drink",
  "source": "manual",
  "unique_hash": "ignored-by-server"
}
```
- POST `/transactions/import` (multipart upload CSV) — columns: date,amount,merchant,description,category,account

## Analytics
- GET `/analytics/summary`

## ML
- POST `/ml/predict` {merchant, description, amount, date?}
