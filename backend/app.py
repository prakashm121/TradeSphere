from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)
CORS(app)

DATABASE = 'stock_market.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 50000,
            last_recovery_date TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            symbol TEXT UNIQUE NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    conn.execute('''
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
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            user_id INTEGER,
            stock_id INTEGER,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, stock_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (stock_id) REFERENCES stocks (stock_id)
        )
    ''')
    
    # Insert sample stocks
    stocks = [
        ('Apple Inc.', 'AAPL', 150.00),
        ('Google', 'GOOGL', 2800.00),
        ('Microsoft', 'MSFT', 300.00),
        ('Amazon', 'AMZN', 3200.00),
        ('Tesla', 'TSLA', 800.00),
        ('Meta Platforms', 'META', 250.00),
        ('Netflix', 'NFLX', 400.00),
        ('NVIDIA', 'NVDA', 900.00),
        ('Reliance Industries', 'RELIANCE', 2500.00),
        ('Tata Consultancy Services', 'TCS', 3500.00),
        ('Infosys Ltd.', 'INFY', 1533.40),
        ('Wipro Ltd.', 'WIPRO', 254.15),
        ('HDFC Bank Ltd.', 'HDFCBANK', 1700.00),
        ('ICICI Bank Ltd.', 'ICICIBANK', 1050.00),
        ('Hindustan Unilever Ltd.', 'HUL', 2700.00),
        ('Bharti Airtel Ltd.', 'BHARTIARTL', 1050.00),
        ('ITC Ltd.', 'ITC', 460.00),
        ('State Bank of India', 'SBIN', 700.00),
        ('Larsen & Toubro', 'LT', 3500.00),
        ('Maruti Suzuki India', 'MARUTI', 900.00),
        ('HCL Technologies', 'HCLTECH', 1500.00),
        ('Kotak Mahindra Bank', 'KOTAKBANK', 1800.00)
    ]
    
    for name, symbol, price in stocks:
        conn.execute(
            'INSERT OR IGNORE INTO stocks (name, symbol, price) VALUES (?, ?, ?)',
            (name, symbol, price)
        )
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Global variable to track last price update time
last_price_update = datetime.now()

def update_stock_prices():
    """Simulate stock price fluctuations with 30-second cooldown"""
    global last_price_update
    
    current_time = datetime.now()
    time_since_last_update = (current_time - last_price_update).total_seconds()
    
    # Only update prices if more than 30 seconds have passed
    if time_since_last_update < 30:
        return  # Skip price update
    
    conn = get_db_connection()
    stocks = conn.execute('SELECT * FROM stocks').fetchall()
    
    for stock in stocks:
        # Random price change between -5% to +5%
        change_percent = random.uniform(-0.35, 0.35)
        new_price = stock['price'] * (1 + change_percent)
        new_price = round(max(new_price, 1.0), 2)  # Minimum price of ₹1
        
        conn.execute(
            'UPDATE stocks SET price = ? WHERE stock_id = ?',
            (new_price, stock['stock_id'])
        )
    
    conn.commit()
    conn.close()
    last_price_update = current_time  # Update the last update time

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db_connection()
    
    # Check if user exists
    existing_user = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create user
    hashed_password = hash_password(password)
    conn.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        (username, hashed_password)
    )
    conn.commit()
    
    user = conn.execute(
        'SELECT user_id, username, balance FROM users WHERE username = ?',
        (username,)
    ).fetchone()
    
    conn.close()
    
    return jsonify({
        'user_id': user['user_id'],
        'username': user['username'],
        'balance': user['balance']
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db_connection()
    hashed_password = hash_password(password)
    
    user = conn.execute(
        'SELECT user_id, username, balance FROM users WHERE username = ? AND password = ?',
        (username, hashed_password)
    ).fetchone()
    
    conn.close()
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return jsonify({
        'user_id': user['user_id'],
        'username': user['username'],
        'balance': user['balance']
    })

@app.route('/balance/<int:user_id>')
def get_balance(user_id):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT balance FROM users WHERE user_id = ?', (user_id,)
    ).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'balance': user['balance']})

@app.route('/stocks')
def get_stocks():
    update_stock_prices()  # Update prices with 30-second cooldown
    conn = get_db_connection()
    stocks = conn.execute('SELECT * FROM stocks').fetchall()
    conn.close()
    
    return jsonify([dict(stock) for stock in stocks])

@app.route('/portfolio/<int:user_id>')
def get_portfolio(user_id):
    conn = get_db_connection()
    
    portfolio = conn.execute('''
        SELECT p.quantity, s.name, s.symbol, s.price, s.stock_id,
               (p.quantity * s.price) as current_value
        FROM portfolio p
        JOIN stocks s ON p.stock_id = s.stock_id
        WHERE p.user_id = ? AND p.quantity > 0
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(item) for item in portfolio])

@app.route('/transactions/<int:user_id>')
def get_transactions(user_id):
    conn = get_db_connection()
    
    transactions = conn.execute('''
        SELECT t.*, s.name, s.symbol
        FROM transactions t
        JOIN stocks s ON t.stock_id = s.stock_id
        WHERE t.user_id = ?
        ORDER BY t.timestamp DESC
        LIMIT 50
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(transaction) for transaction in transactions])

@app.route('/buy', methods=['POST'])
def buy_stock():
    data = request.json
    user_id = data.get('user_id')
    stock_id = data.get('stock_id')
    quantity = data.get('quantity')
    
    if not all([user_id, stock_id, quantity]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    conn = get_db_connection()
    
    # Get user balance and stock price
    user = conn.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()
    stock = conn.execute('SELECT price FROM stocks WHERE stock_id = ?', (stock_id,)).fetchone()
    
    if not user or not stock:
        conn.close()
        return jsonify({'error': 'User or stock not found'}), 404
    
    total_cost = stock['price'] * quantity
    
    if user['balance'] < total_cost:
        conn.close()
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # Update user balance
    new_balance = user['balance'] - total_cost
    conn.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    
    # Add transaction
    conn.execute('''
        INSERT INTO transactions (user_id, stock_id, type, quantity, price_at_transaction, timestamp)
        VALUES (?, ?, 'BUY', ?, ?, ?)
    ''', (user_id, stock_id, quantity, stock['price'], datetime.now().isoformat()))
    
    # Update portfolio
    existing_holding = conn.execute(
        'SELECT quantity FROM portfolio WHERE user_id = ? AND stock_id = ?',
        (user_id, stock_id)
    ).fetchone()
    
    if existing_holding:
        new_quantity = existing_holding['quantity'] + quantity
        conn.execute(
            'UPDATE portfolio SET quantity = ? WHERE user_id = ? AND stock_id = ?',
            (new_quantity, user_id, stock_id)
        )
    else:
        conn.execute(
            'INSERT INTO portfolio (user_id, stock_id, quantity) VALUES (?, ?, ?)',
            (user_id, stock_id, quantity)
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'new_balance': new_balance})

@app.route('/sell', methods=['POST'])
def sell_stock():
    data = request.json
    user_id = data.get('user_id')
    stock_id = data.get('stock_id')
    quantity = data.get('quantity')
    
    if not all([user_id, stock_id, quantity]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    conn = get_db_connection()
    
    # Check if user has enough shares
    holding = conn.execute(
        'SELECT quantity FROM portfolio WHERE user_id = ? AND stock_id = ?',
        (user_id, stock_id)
    ).fetchone()
    
    if not holding or holding['quantity'] < quantity:
        conn.close()
        return jsonify({'error': 'Insufficient shares'}), 400
    
    # Get current stock price and user balance
    stock = conn.execute('SELECT price FROM stocks WHERE stock_id = ?', (stock_id,)).fetchone()
    user = conn.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    total_value = stock['price'] * quantity
    new_balance = user['balance'] + total_value
    
    # Update user balance
    conn.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    
    # Add transaction
    conn.execute('''
        INSERT INTO transactions (user_id, stock_id, type, quantity, price_at_transaction, timestamp)
        VALUES (?, ?, 'SELL', ?, ?, ?)
    ''', (user_id, stock_id, quantity, stock['price'], datetime.now().isoformat()))
    
    # Update portfolio
    new_quantity = holding['quantity'] - quantity
    if new_quantity == 0:
        conn.execute(
            'DELETE FROM portfolio WHERE user_id = ? AND stock_id = ?',
            (user_id, stock_id)
        )
    else:
        conn.execute(
            'UPDATE portfolio SET quantity = ? WHERE user_id = ? AND stock_id = ?',
            (new_quantity, user_id, stock_id)
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'new_balance': new_balance})

@app.route('/recover-balance/<int:user_id>', methods=['POST'])
def recover_balance(user_id):
    conn = get_db_connection()
    
    user = conn.execute(
        'SELECT balance, last_recovery_date FROM users WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Check if 24 hours have passed
    last_recovery = user['last_recovery_date']
    now = datetime.now()
    
    if last_recovery:
        last_recovery_date = datetime.fromisoformat(last_recovery)
        if now - last_recovery_date < timedelta(hours=24):
            time_left = timedelta(hours=24) - (now - last_recovery_date)
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            conn.close()
            return jsonify({
                'error': f'Recovery available in {hours_left}h {minutes_left}m'
            }), 400
    
    # Give recovery bonus
    recovery_amount = 5000
    new_balance = user['balance'] + recovery_amount
    
    conn.execute(
        'UPDATE users SET balance = ?, last_recovery_date = ? WHERE user_id = ?',
        (new_balance, now.isoformat(), user_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'recovery_amount': recovery_amount,
        'new_balance': new_balance
    })

@app.route('/recovery-status/<int:user_id>')
def recovery_status(user_id):
    conn = get_db_connection()
    
    user = conn.execute(
        'SELECT last_recovery_date FROM users WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    last_recovery = user['last_recovery_date']
    
    if not last_recovery:
        conn.close()
        return jsonify({'can_recover': True})
    
    last_recovery_date = datetime.fromisoformat(last_recovery)
    now = datetime.now()
    time_diff = now - last_recovery_date
    
    if time_diff >= timedelta(hours=24):
        conn.close()
        return jsonify({'can_recover': True})
    
    time_left = timedelta(hours=24) - time_diff
    hours_left = int(time_left.total_seconds() // 3600)
    minutes_left = int((time_left.total_seconds() % 3600) // 60)
    
    conn.close()
    return jsonify({
        'can_recover': False,
        'hours_left': hours_left,
        'minutes_left': minutes_left
    })

if __name__ == '__main__':
    init_database()
    app.run(debug=True, port=5000)