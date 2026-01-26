from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, stocks, trades, portfolio, transactions, balance
from app.utils.init_db import init_database

app = FastAPI(title="TradeSphereA API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(trades.router)
app.include_router(portfolio.router)
app.include_router(transactions.router)
app.include_router(balance.router)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_database()


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "TradeSphereA API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000)

