from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import hashlib
from datetime import datetime, timedelta
import random
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = os.path.join(os.path.dirname(__file__), "stock_market.db")


class AuthRequest(BaseModel):
    username: str
    password: str


class TradeRequest(BaseModel):
    user_id: int
    stock_id: int
    quantity: int


def get_db_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 50000,
                last_recovery_date TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stocks (
                stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                symbol TEXT UNIQUE NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stock_id INTEGER,
                type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_at_transaction REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio (
                user_id INTEGER,
                stock_id INTEGER,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, stock_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
            )
            """
        )
        stocks = [
            ("Apple Inc.", "AAPL", 150.00),
            ("Google", "GOOGL", 2800.00),
            ("Microsoft", "MSFT", 300.00),
            ("Amazon", "AMZN", 3200.00),
            ("Tesla", "TSLA", 800.00),
            ("Meta Platforms", "META", 250.00),
            ("Netflix", "NFLX", 400.00),
            ("NVIDIA", "NVDA", 900.00),
            ("Reliance Industries", "RELIANCE", 2500.00),
            ("Tata Consultancy Services", "TCS", 3500.00),
            ("Infosys Ltd.", "INFY", 1533.40),
            ("Wipro Ltd.", "WIPRO", 254.15),
            ("HDFC Bank Ltd.", "HDFCBANK", 1700.00),
            ("ICICI Bank Ltd.", "ICICIBANK", 1050.00),
            ("Hindustan Unilever Ltd.", "HUL", 2700.00),
            ("Bharti Airtel Ltd.", "BHARTIARTL", 1050.00),
            ("ITC Ltd.", "ITC", 460.00),
            ("State Bank of India", "SBIN", 700.00),
            ("Larsen & Toubro", "LT", 3500.00),
            ("Maruti Suzuki India", "MARUTI", 900.00),
            ("HCL Technologies", "HCLTECH", 1500.00),
            ("Kotak Mahindra Bank", "KOTAKBANK", 1800.00),
        ]
        for name, symbol, price in stocks:
            conn.execute(
                "INSERT OR IGNORE INTO stocks (name, symbol, price) VALUES (?, ?, ?)",
                (name, symbol, price),
            )
        conn.commit()
    finally:
        conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


last_price_update = datetime.now()


def update_stock_prices():
    global last_price_update
    current_time = datetime.now()
    time_since_last_update = (current_time - last_price_update).total_seconds()
    if time_since_last_update < 30:
        return
    conn = get_db_connection()
    try:
        stocks = conn.execute("SELECT * FROM stocks").fetchall()
        for stock in stocks:
            change_percent = random.uniform(-0.35, 0.35)
            new_price = stock["price"] * (1 + change_percent)
            new_price = round(max(new_price, 1.0), 2)
            conn.execute(
                "UPDATE stocks SET price = ? WHERE stock_id = ?",
                (new_price, stock["stock_id"]),
            )
        conn.commit()
        last_price_update = current_time
    finally:
        conn.close()


@app.post("/register")
def register(payload: AuthRequest):
    username = payload.username.strip()
    password = payload.password.strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    conn = get_db_connection()
    try:
        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        hashed_password = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password),
        )
        conn.commit()
        user = conn.execute(
            "SELECT user_id, username, balance FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "balance": user["balance"],
        }
    finally:
        conn.close()


@app.post("/login")
def login(payload: AuthRequest):
    username = payload.username.strip()
    password = payload.password.strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    conn = get_db_connection()
    try:
        hashed_password = hash_password(password)
        user = conn.execute(
            "SELECT user_id, username, balance FROM users WHERE username = ? AND password = ?",
            (username, hashed_password),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "balance": user["balance"],
        }
    finally:
        conn.close()


@app.get("/balance/{user_id}")
def get_balance(user_id: int):
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT balance FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"balance": user["balance"]}
    finally:
        conn.close()


@app.get("/stocks")
def get_stocks():
    update_stock_prices()
    conn = get_db_connection()
    try:
        stocks = conn.execute("SELECT * FROM stocks").fetchall()
        return [dict(stock) for stock in stocks]
    finally:
        conn.close()


@app.get("/portfolio/{user_id}")
def get_portfolio(user_id: int):
    conn = get_db_connection()
    try:
        portfolio = conn.execute(
            """
            SELECT p.quantity, s.name, s.symbol, s.price, s.stock_id,
                   (p.quantity * s.price) as current_value
            FROM portfolio p
            JOIN stocks s ON p.stock_id = s.stock_id
            WHERE p.user_id = ? AND p.quantity > 0
            """,
            (user_id,),
        ).fetchall()
        return [dict(item) for item in portfolio]
    finally:
        conn.close()


@app.get("/transactions/{user_id}")
def get_transactions(user_id: int):
    conn = get_db_connection()
    try:
        transactions = conn.execute(
            """
            SELECT t.*, s.name, s.symbol
            FROM transactions t
            JOIN stocks s ON t.stock_id = s.stock_id
            WHERE t.user_id = ?
            ORDER BY t.timestamp DESC
            LIMIT 50
            """,
            (user_id,),
        ).fetchall()
        return [dict(transaction) for transaction in transactions]
    finally:
        conn.close()


@app.post("/buy")
def buy_stock(payload: TradeRequest):
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT balance FROM users WHERE user_id = ?",
            (payload.user_id,),
        ).fetchone()
        stock = conn.execute(
            "SELECT price FROM stocks WHERE stock_id = ?",
            (payload.stock_id,),
        ).fetchone()
        if not user or not stock:
            raise HTTPException(status_code=404, detail="User or stock not found")
        total_cost = stock["price"] * payload.quantity
        if user["balance"] < total_cost:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        new_balance = user["balance"] - total_cost
        conn.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (new_balance, payload.user_id),
        )
        conn.execute(
            """
            INSERT INTO transactions (user_id, stock_id, type, quantity, price_at_transaction, timestamp)
            VALUES (?, ?, 'BUY', ?, ?, ?)
            """,
            (
                payload.user_id,
                payload.stock_id,
                payload.quantity,
                stock["price"],
                datetime.now().isoformat(),
            ),
        )
        existing_holding = conn.execute(
            "SELECT quantity FROM portfolio WHERE user_id = ? AND stock_id = ?",
            (payload.user_id, payload.stock_id),
        ).fetchone()
        if existing_holding:
            new_quantity = existing_holding["quantity"] + payload.quantity
            conn.execute(
                "UPDATE portfolio SET quantity = ? WHERE user_id = ? AND stock_id = ?",
                (new_quantity, payload.user_id, payload.stock_id),
            )
        else:
            conn.execute(
                "INSERT INTO portfolio (user_id, stock_id, quantity) VALUES (?, ?, ?)",
                (payload.user_id, payload.stock_id, payload.quantity),
            )
        conn.commit()
        return {"success": True, "new_balance": new_balance}
    finally:
        conn.close()


@app.post("/sell")
def sell_stock(payload: TradeRequest):
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    conn = get_db_connection()
    try:
        holding = conn.execute(
            "SELECT quantity FROM portfolio WHERE user_id = ? AND stock_id = ?",
            (payload.user_id, payload.stock_id),
        ).fetchone()
        if not holding or holding["quantity"] < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient shares")
        stock = conn.execute(
            "SELECT price FROM stocks WHERE stock_id = ?",
            (payload.stock_id,),
        ).fetchone()
        user = conn.execute(
            "SELECT balance FROM users WHERE user_id = ?",
            (payload.user_id,),
        ).fetchone()
        total_value = stock["price"] * payload.quantity
        new_balance = user["balance"] + total_value
        conn.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (new_balance, payload.user_id),
        )
        conn.execute(
            """
            INSERT INTO transactions (user_id, stock_id, type, quantity, price_at_transaction, timestamp)
            VALUES (?, ?, 'SELL', ?, ?, ?)
            """,
            (
                payload.user_id,
                payload.stock_id,
                payload.quantity,
                stock["price"],
                datetime.now().isoformat(),
            ),
        )
        new_quantity = holding["quantity"] - payload.quantity
        if new_quantity == 0:
            conn.execute(
                "DELETE FROM portfolio WHERE user_id = ? AND stock_id = ?",
                (payload.user_id, payload.stock_id),
            )
        else:
            conn.execute(
                "UPDATE portfolio SET quantity = ? WHERE user_id = ? AND stock_id = ?",
                (new_quantity, payload.user_id, payload.stock_id),
            )
        conn.commit()
        return {"success": True, "new_balance": new_balance}
    finally:
        conn.close()


@app.post("/recover-balance/{user_id}")
def recover_balance(user_id: int):
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT balance, last_recovery_date FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        last_recovery = user["last_recovery_date"]
        now = datetime.now()
        if last_recovery:
            last_recovery_date = datetime.fromisoformat(last_recovery)
            if now - last_recovery_date < timedelta(hours=24):
                time_left = timedelta(hours=24) - (now - last_recovery_date)
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                raise HTTPException(
                    status_code=400,
                    detail=f"Recovery available in {hours_left}h {minutes_left}m",
                )
        recovery_amount = 5000
        new_balance = user["balance"] + recovery_amount
        conn.execute(
            "UPDATE users SET balance = ?, last_recovery_date = ? WHERE user_id = ?",
            (new_balance, now.isoformat(), user_id),
        )
        conn.commit()
        return {
            "success": True,
            "recovery_amount": recovery_amount,
            "new_balance": new_balance,
        }
    finally:
        conn.close()


@app.get("/recovery-status/{user_id}")
def recovery_status(user_id: int):
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT last_recovery_date FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        last_recovery = user["last_recovery_date"]
        if not last_recovery:
            return {"can_recover": True}
        last_recovery_date = datetime.fromisoformat(last_recovery)
        now = datetime.now()
        time_diff = now - last_recovery_date
        if time_diff >= timedelta(hours=24):
            return {"can_recover": True}
        time_left = timedelta(hours=24) - time_diff
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        return {
            "can_recover": False,
            "hours_left": hours_left,
            "minutes_left": minutes_left,
        }
    finally:
        conn.close()


@app.on_event("startup")
def startup_event():
    init_database()


if __name__ == "__main__":
    import uvicorn

    init_database()
    uvicorn.run(app, host="localhost", port=5000)
