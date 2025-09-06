import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from .routers import auth, transactions, analytics, ml
from .ml import service as ml_service
from .routers import auth as auth_router, transactions as tx_router, analytics as an_router, ml as ml_router, budgets as bu_router

def create_app():
    app = FastAPI(title="Finance Dashboard API")

    # CORS
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # DB init
    Base.metadata.create_all(bind=engine)

    # Routers (note: import modules, then use .router)
    app.include_router(auth.router)
    app.include_router(transactions.router)
    app.include_router(analytics.router)
    app.include_router(ml.router)
    app.include_router(bu_router.router)

    @app.on_event("startup")
    def _load_model():
        ok = ml_service.load_model()
        print("ML model loaded." if ok else "No ML model found yet. Train with backend/app/ml/train.py")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_app()
