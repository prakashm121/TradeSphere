import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, stocks, trades, portfolio, transactions, balance
from app.routers import orders
from app.utils.init_db import init_database
from app.services.market_maker import market_maker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    init_database()
    task = None
    if settings.ENABLE_LEGACY_MARKET_MAKER:
        task = asyncio.create_task(market_maker())
    yield
    # Shutdown
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="TradeSphere API", version="2.0.0", lifespan=lifespan)

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
app.include_router(orders.router)
app.include_router(trades.router)
app.include_router(portfolio.router)
app.include_router(transactions.router)
app.include_router(balance.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "TradeSphere API", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000)


