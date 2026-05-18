# TradeSphere

TradeSphere is a full-stack virtual trading simulator built with React, Vite, and FastAPI. It enables users to place buy/sell orders, track portfolio value, view live market events, and inspect real OHLC candle data generated from executed trades.

## What TradeSphere Does

- Provides account registration and JWT-based login.
- Shows a live stock feed with price updates and order-book snapshots.
- Executes market and limit orders through a backend matching engine.
- Aggregates executed trades into real candlestick bars per resolution.
- Tracks portfolio holdings, unrealized profit and loss, and transaction history.
- Includes a recovery bonus mechanic to give users additional virtual capital over time.

## High-Level Architecture

### System Overview

TradeSphere is a trading simulator built around a single truth: prices move only when a trade is executed. The system combines:
- React + Vite frontend for user interaction, dashboards, charts, and order entry
- FastAPI backend for auth, order routing, matching, trade execution, and market state
- SQL database for persistent stocks, orders, executed trades, candles, portfolios, and user state
- WebSocket event stream for real-time updates to all connected clients

### Use Case Model

```mermaid
flowchart LR
    Trader[Trader]
    System[TradeSphere System]
    Trader -->|Login / Register| Login(Login)
    Trader -->|View live market| Market(View Market Data)
    Trader -->|Place buy/sell| Order(Place Order)
    Trader -->|Inspect candles| Candles(View Candle Chart)
    Trader -->|Check portfolio| Portfolio(View Portfolio)
    Trader -->|Review history| History(View Transactions)
```

### Class Diagram

```mermaid
classDiagram
    class User {
      +int id
      +str email
      +str hashed_password
      +float balance
      +float buying_power
      +List[PortfolioItem] portfolio
      +List[Order] orders
    }
    class Stock {
      +int id
      +str symbol
      +str name
      +float last_price
      +float bid
      +float ask
      +OrderBook order_book
    }
    class Order {
      +int id
      +int user_id
      +int stock_id
      +str side
      +float price
      +int quantity
      +str status
      +datetime created_at
    }
    class Trade {
      +int id
      +int buy_order_id
      +int sell_order_id
      +int stock_id
      +float price
      +int quantity
      +datetime executed_at
    }
    class Candle {
      +int id
      +int stock_id
      +datetime start_time
      +float open
      +float high
      +float low
      +float close
      +int volume
    }
    class PortfolioItem {
      +int id
      +int user_id
      +int stock_id
      +int quantity
      +float avg_cost
    }
    class OrderBook {
      +List[Order] bids
      +List[Order] asks
      +fillOrder()
      +snapshot()
    }
    User "1" --o "*" Order
    User "1" --o "*" PortfolioItem
    Stock "1" --o "*" Order
    Stock "1" --o "*" Trade
    Stock "1" --o "*" Candle
    OrderBook "1" --o "*" Order
    Trade "1" -- "1" Candle : contributes
```

### Sequence Diagrams

#### Order Placement and Execution

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI
    participant M as MatchingEngine
    participant DB as Database
    participant WS as WebSocketHub

    U->>F: Submit buy/sell order
    F->>API: POST /orders
    API->>DB: create pending order
    API->>M: match order
    M->>DB: load opposite book
    alt match found
      M->>DB: create Trade records
      M->>DB: update Order statuses
      M->>DB: update Stock last_price
      API->>WS: broadcast trade_tick, price_update, book_snapshot
    else no match
      M->>DB: keep order on book
      API->>WS: broadcast book_snapshot
    end
    API->>F: return order response
```

#### Market Data Delivery

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant WS as WebSocketHub
    participant F as Frontend
    API->>WS: publish market_snapshot / book_snapshot
    WS->>F: send live market events
    F->>F: update order book, candles, price display
```

### Activity Diagrams

#### Order Lifecycle

```mermaid
flowchart TD
    A[Start] --> B[Receive order request]
    B --> C[Validate auth and balance]
    C --> D[Add order to order book]
    D --> E{Opposite order available?}
    E -- Yes --> F[Match orders]
    F --> G[Create trade execution]
    G --> H[Update stock price and order statuses]
    H --> I[Broadcast updates via WebSocket]
    I --> J[Update candles]
    J --> K[Persist all changes]
    E -- No --> L[Keep limit order open]
    L --> I
    K --> M[End]
```

#### Candle Aggregation

```mermaid
flowchart TD
    A[New executed trade] --> B[Fetch candle bucket]
    B --> C{Bucket exists?}
    C -- Yes --> D[Update high/low/close/volume]
    C -- No --> E[Create new candle bucket]
    D --> F[Save candle]
    E --> F
    F --> G[Broadcast candle_update]
```

### Database Model

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER ||--o{ PORTFOLIO_ITEM : owns
    STOCK ||--o{ ORDER : contains
    STOCK ||--o{ TRADE : records
    STOCK ||--o{ CANDLE : aggregates
    ORDER ||--o{ TRADE : fills
    TRADE ||--|| STOCK : for
    PORTFOLIO_ITEM }o--|| STOCK : references
```

### Component Architecture

```mermaid
flowchart LR
    Browser[Browser UI]
    subgraph Frontend
      Login(Login)
      Dashboard(Dashboard)
      Trading(Trading Page)
      Portfolios(Portfolio)
      Hist(Transactions)
    end
    subgraph Backend
      Auth[Auth Router]
      Stocks[Stocks Router]
      Orders[Orders Router]
      Market[Matching Engine]
      Candles[Candle Service]
      WS[WebSocket Hub]
    end
    Browser --> Auth
    Browser --> Stocks
    Browser --> Orders
    Browser --> WS
    Orders --> Market
    Market --> Candles
    Market --> WS
    Candles --> WS
```

### How Prices Change

TradeSphere only changes a stock’s displayed price when an actual trade is executed. The key rules are:
- Limit orders are placed into the buy or sell book and do not change price by themselves.
- The matching engine compares incoming orders against the opposite side of the book.
- When an incoming order matches one or more opposite orders, trade records are created at the agreed price.
- The executed trade updates `Stock.last_price` and the market quote.
- After execution, the system publishes a `trade_tick` event and a `price_update` event to all WebSocket clients.
- Candles are built from the same executed trades, so candlestick bars always reflect real volume and price movement.

### Price and Market Build Process

1. User submits an order through the trading UI.
2. Backend validates the request and saves the pending order.
3. Matching Engine loads current bids/asks and attempts a match.
4. If a match occurs, executed trade records are written.
5. Backend updates stock price and order statuses.
6. Candle Engine aggregates the trade into the correct OHLC bucket.
7. WebSocket Hub broadcasts:
   - `trade_tick`
   - `price_update`
   - `book_snapshot`
   - `candle_update`
8. Frontend receives events and redraws the order book, price badge, trade ticks, and charts.

### Frontend (React + Vite)

The frontend is a client-side SPA in the src folder:
- App.jsx for app structure, auth restore, navigation, and routes
- components/Login.jsx for login and registration flow
- components/Dashboard.jsx for summary cards and market overview
- components/Trading.jsx for live market feed, order entry, order book, and candle chart
- components/Portfolio.jsx for holdings and distribution
- components/Transactions.jsx for transaction history
- components/CandleChart.jsx for SVG candlestick rendering
- utils/axiosAuthSetup.js for auth interceptor
- utils/auth.js for local storage session helpers

### Backend (FastAPI)

The backend lives in backend/app:
- main.py for FastAPI startup, CORS, routers, and lifecycle tasks
- core/config.py for environment and settings loader
- core/database.py for SQLAlchemy engine and session setup
- core/security.py for hashing and JWT utilities
- models for users, stocks, portfolio, orders, transactions, trades, and candles
- schemas for request and response models
- routers for auth, stocks, portfolio, orders, trades, balance, and transaction endpoints
- services for matching engine, trade execution, candle aggregation, market maker, and WebSocket broadcast logic
- utils/init_db.py for database initialization and seeding

## Event Flow

1. User logs in and receives a JWT token.
2. Frontend requests stock, portfolio, balance, and transaction data.
3. Trading page opens a WebSocket to /ws/market for live events.
4. Orders are submitted to the backend and matched by the engine.
5. Executed trades publish trade ticks and update market prices.
6. The candle engine aggregates executed trades into OHLCV candles.
7. The WebSocket hub broadcasts updated market events and candles to clients.

## Project Structure

```text
TradeSphere/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── .env
│   ├── requirements.txt
│   └── README.md
├── public/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx
│   │   ├── Landing.jsx
│   │   ├── Login.jsx
│   │   ├── Portfolio.jsx
│   │   ├── Trading.jsx
│   │   ├── Transactions.jsx
│   │   └── CandleChart.jsx
│   ├── utils/
│   │   ├── auth.js
│   │   └── axiosAuthSetup.js
│   ├── App.jsx
│   ├── App.css
│   └── main.jsx
├── package.json
├── vite.config.js
└── README.md
```

### Notes on structure
- `backend/app` contains the FastAPI application and domain modules.
- `src/components` contains the main React UI screens and trading widgets.
- `src/utils` contains auth helpers and Axios configuration.
- `public` contains static frontend assets.

## Setup

Frontend:

npm install
npm run dev

Backend:

cd backend
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 5000

## Environment

Create or update backend/.env with required variables such as DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, CORS_ORIGINS, and VERIFICATION_BASE_URL.

## API Endpoints

Method | Path | Description
--- | --- | ---
POST | /auth/register | Register a new user
POST | /auth/login | Log in and receive a JWT
GET | /auth/me | Get current authenticated user
GET | /stocks | List stocks with current pricing
GET | /stocks/{stock_id}/book | Get order book data for a stock
GET | /stocks/{stock_id}/candles | Get OHLCV candles for a stock
GET | /portfolio | Get authenticated user portfolio
GET | /transactions | Get authenticated user transactions
GET | /balance | Get authenticated user balance
GET | /balance/recovery-status | Get recovery cooldown status
POST | /orders | Submit a buy or sell order
GET | /healthz | Health check
WS | /ws/market | Live market event feed

## Notes

- The frontend currently uses a hard-coded API_BASE_URL pointing at the backend.
- CORS is open for development. Restrict CORS_ORIGINS before production deployment.
- Candle data is generated from executed trades and broadcast live via WebSocket updates.

## Common Commands

- npm run build — Build the frontend
- npm run lint — Run ESLint
- uvicorn app.main:app --reload --host 127.0.0.1 --port 5000 — Start backend

## Troubleshooting

- If the frontend cannot connect, confirm backend is running and API_BASE_URL matches the backend URL.
- If login fails, verify the JWT token is stored and the auth interceptor is sending it.
- If WebSocket updates stop, verify /ws/market is reachable.

## License

See LICENSE for license details.
