import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, stocks, trades, portfolio, transactions, balance, orders, websocket
from app.utils.init_db import init_database
from app.services.market_maker import market_maker
from app.services.candle_engine import candle_engine
from app.services import ws_hub

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("TradeSphere API starting up...")
    init_database()
    
    # Initialize WebSocket hub
    await ws_hub.init_hub()
    
    # Start background tasks
    tasks = []
    
    # Market maker bots (v2: real order placement, not random price moves)
    logger.info("Starting market maker bots...")
    tasks.append(asyncio.create_task(market_maker()))
    
    # Candle aggregation engine
    logger.info("Starting candle engine...")
    tasks.append(asyncio.create_task(candle_engine()))
    
    yield
    
    # Shutdown
    logger.info("TradeSphere API shutting down...")
    
    # Shutdown WebSocket hub
    await ws_hub.shutdown_hub()
    
    # Cancel background tasks
    for task in tasks:
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    logger.info("Shutdown complete")


app = FastAPI(title="TradeSphere API", version="2.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Authorization"],
)

# Include routers
app.include_router(auth.router)
app.include_router(stocks.router)
app.include_router(orders.router)
app.include_router(trades.router)
app.include_router(portfolio.router)
app.include_router(transactions.router)
app.include_router(balance.router)
app.include_router(websocket.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "TradeSphere API", "version": "2.0.0"}


@app.get("/healthz")
def health_check():
    """Health check endpoint for uptime and readiness."""
    return {"status": "ok", "service": "TradeSphere API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000)
