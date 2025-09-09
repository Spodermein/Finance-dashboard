# Finance-dashboard

# Finance Dashboard

A minimal full‑stack personal finance tracker with a FastAPI backend and a static (vanilla JS + Chart.js) frontend.

## Features
- **Auth & security**: Email + password, JWT‑based session.
- **Transactions**: Add single entries, import CSV (idempotent via per‑user hash), list & search, export CSV.
- **Analytics**: Income vs. expense totals, category breakdown, monthly trend (Chart.js).
- **Budgets**: Per‑category monthly limits with simple progress bars.
- **ML assist**: Optional category suggestion using a TF‑IDF + Logistic Regression model (scikit‑learn).
- **Zero build tooling** on the frontend; simple Python server for the backend.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, SQLite (default), Pydantic, JWT (PyJWT), passlib[bcrypt], pandas, scikit‑learn, joblib
- **Frontend**: Vanilla JS, HTML, CSS, Chart.js
- **Dev**: Python 3.11+ recommended

## Repo Structure
```
/backend
  app/
    routers/           # auth, transactions, analytics, budgets, ml
    ml/                # train.py, service.py, saved model (model.joblib)
    models.py          # SQLAlchemy models: User, Transaction, Budget
    schemas.py         # Pydantic request/response models
    main.py            # FastAPI app factory, router mounting, CORS
  requirements.txt
  .env.example         # copy to .env and edit
/frontend
  index.html           # one-file UI that talks to the API
```
> Note: Do **not** commit virtualenv or `app.db` to Git. Add them to `.gitignore`.

### Example `.gitignore`
```
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.env
app.db
*.sqlite
# Node/Front-end
node_modules/
dist/
# OS
.DS_Store
Thumbs.db
```

## Quick Start

### 1) Backend (FastAPI)
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt

# Configure env
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env

# Run the API (http://localhost:8000)
uvicorn app.main:app --reload
```

> If you change ports or deploy behind a different host, update `CORS_ORIGINS` in `.env` accordingly.

#### Train the (optional) ML model
```bash
# Saves a bundled model to backend/app/ml/model.joblib
python backend/app/ml/train.py
```

### 2) Frontend (Static)
```bash
cd frontend
# Serve on http://localhost:5173
python -m http.server 5173
# then open http://localhost:5173
```

In **Settings → API Settings** (in the UI), set **Backend API URL** to `http://localhost:8000` and click **Save**.

## Using the App
1. **Register** then **Login** (top section).  
   The JWT is stored in `localStorage` and used for subsequent API calls.
2. **Add transactions** (negative = expense, positive = income). Click **Predict (ML)** to get a category suggestion.
3. **Analytics** card shows totals and a **Category** chart.
4. **Transactions** table supports searching and sorting. Click **Export CSV** to download filtered data.
5. **Budgets** tab lets you add per‑category monthly limits and view progress.

## CSV Import / Export
- Import endpoint (backend): `POST /transactions/import` (multipart file). The CSV must contain at least `date,amount`. Optional: `merchant,description,category,account`.
- Export endpoint (backend): `GET /transactions/export?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&category=Food`

**CSV columns**
```
date,amount,merchant,description,category,account
2025-07-01,-12.99,Starbucks,Latte,Food & Drink,Main
```

## API (Selected Endpoints)

### Auth
```http
POST /auth/register
POST /auth/login
```
Payload:
```json
{ "email": "you@example.com", "password": "secret123" }
```
Response:
```json
{ "access_token": "…", "token_type": "bearer" }
```
Use header: `Authorization: Bearer <token>` for protected endpoints.

### Transactions
```http
GET  /transactions?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&category=Food
POST /transactions
POST /transactions/import        # multipart CSV upload
GET  /transactions/export        # CSV download
```
`POST /transactions` payload:
```json
{
  "date": "2025-07-01",
  "amount": -12.99,
  "merchant": "Starbucks",
  "description": "Latte",
  "category": "Food & Drink",
  "account": "Main",
  "source": "manual"
}
```

### Analytics
```http
GET /analytics/summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

### Budgets
```http
GET  /budgets
POST /budgets
GET  /budgets/progress?month=2025-07
```
`POST /budgets` payload:
```json
{ "category": "Food & Drink", "monthly_limit": 300.0 }
```

### ML (Category Suggestion)
```http
GET  /ml/status
POST /ml/threshold/{value}
POST /ml/predict    # UI calls this; ensure the route exists (see note below)
```
`POST /ml/predict` payload:
```json
{ "merchant": "Starbucks", "description": "Latte", "amount": -4.5, "date": "2025-07-01" }
```

> **Note:** If `/ml/predict` is missing, add a route that calls `ml.service.predict(...)` and returns `{label, confidence}`.

## Environment Variables (`backend/.env`)
```
DATABASE_URL=sqlite:///./app.db
JWT_SECRET=change_me_in_production
JWT_ALGORITHM=HS256
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000
```
- Change `JWT_SECRET` in production.
- Switch `DATABASE_URL` to Postgres/MySQL for a multi‑user deployment.

## Troubleshooting
- **CORS errors**: Ensure `CORS_ORIGINS` includes your frontend origin.
- **401 Unauthorized**: Login again and confirm `Authorization: Bearer <token>` is attached.
- **CSV import**: Verify headers and that `date` parses. The backend dedupes on `(user_id,date,amount,merchant)`.
- **Model not loaded**: Run the training step; the backend prints a message on startup about model load status.

## Roadmap / TODO
- Add missing `POST /ml/predict` router (if not yet present).
- Edit/update/delete transactions from the UI.
- Basic categories management and rules (auto‑categorization).
- Dockerfile(s) for backend & static frontend.
- CI/CD workflow.

## License
MIT
