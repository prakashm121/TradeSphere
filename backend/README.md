# TradeSphereA Backend

A FastAPI-based backend application for a stock trading platform with JWT authentication, Argon2 password hashing, and SQLAlchemy ORM.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration settings
│   │   ├── database.py         # SQLAlchemy database setup
│   │   └── security.py         # JWT and password hashing utilities
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User SQLAlchemy model
│   │   ├── stock.py            # Stock SQLAlchemy model
│   │   ├── transaction.py     # Transaction SQLAlchemy model
│   │   └── portfolio.py       # Portfolio SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication Pydantic schemas
│   │   └── trade.py            # Trading Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── stocks.py            # Stock endpoints
│   │   ├── trades.py           # Trading endpoints (buy/sell)
│   │   ├── portfolio.py        # Portfolio endpoints
│   │   ├── transactions.py     # Transaction history endpoints
│   │   └── balance.py          # Balance management endpoints
│   └── utils/
│       ├── __init__.py
│       └── init_db.py          # Database initialization
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Features

- **JWT Authentication**: Secure token-based authentication
- **Argon2 Password Hashing**: Industry-standard password hashing
- **SQLAlchemy ORM**: Database abstraction layer
- **SQLite Database**: Lightweight, file-based database
- **Pydantic Schemas**: Request/response validation
- **RESTful API**: Well-structured API endpoints

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   Copy `.env.example` to `.env` and update with your values:
   ```env
   DATABASE_URL=sqlite:///./stock_market.db
   SECRET_KEY=your-secret-key-here-change-this-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   CORS_ORIGINS=*
   ```

3. **Run the application:**
   ```bash
   python -m app.main
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host localhost --port 5000
   ```

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login with JSON body (returns JWT token)
- `POST /auth/token` - Login with OAuth2 form data (returns JWT token)
- `GET /auth/me` - Get current user info (requires authentication)

### Stocks
- `GET /stocks` - Get all stocks with updated prices

### Trading
- `POST /trades/buy` - Buy stocks (requires authentication)
- `POST /trades/sell` - Sell stocks (requires authentication)

### Portfolio
- `GET /portfolio` - Get user's portfolio (requires authentication)

### Transactions
- `GET /transactions` - Get transaction history (requires authentication)

### Balance
- `GET /balance` - Get current balance (requires authentication)
- `POST /balance/recover` - Recover balance (once per 24 hours, requires authentication)
- `GET /balance/recovery-status` - Check recovery status (requires authentication)

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

## Database

The application uses SQLite by default. The database file (`stock_market.db`) will be created automatically on first run. The database is initialized with default stocks on startup.

## Security Notes

- Always change the `SECRET_KEY` in production
- Use strong, unique secret keys
- Consider using environment-specific configurations
- The default CORS setting allows all origins (`*`) - restrict this in production

