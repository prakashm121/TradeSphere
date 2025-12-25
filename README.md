# TradeSphere

TradeSphere is a full-stack virtual stock market simulator that pairs a Vite + React SPA with a lightweight Flask API. Users start with ₹50,000 in virtual cash, trade from a curated basket of Indian and global equities, and review their holdings, transactions, and recovery bonuses.

## Features
- Email-free authentication flow with registration, login, and persistent sessions via `localStorage`
- Live-feeling price feed that refreshes every 30 seconds, with client caching to avoid redundant network calls
- Guided trading console supporting buy/sell orders, affordability checks, owned-share warnings, and contextual alerts
- Portfolio analytics including holding weights, distribution bars, and summary cards
- Transaction ledger with filtering, totals, and timestamp formatting for the most recent 50 orders
- Daily ₹5,000 recovery mechanic driven by backend cooldown tracking to keep balances replenished

## Tech Stack
- **Frontend:** React 19, Vite 7, Tailwind CSS v4 (@tailwindcss/vite), lucide-react for icons, axios for HTTP
- **Backend:** Flask + flask-cors with SQLite for persistence and deterministic seed data
- **Tooling:** ESLint 9, npm scripts for build/lint/preview, Python virtualenv recommended for backend isolation

## Project Structure
```
TradeSphere/
├── backend/
│   └── app.py              # Flask API + SQLite schema/seed
├── public/
│   └── Stock.png
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx   # Balance widgets + stock feed + recovery CTA
|   |   ├── Landing.jsx     # Welcome message + signup form
│   │   ├── Login.jsx       # Register/Login toggle
│   │   ├── Portfolio.jsx   # Holdings table + distribution bars
│   │   ├── Trading.jsx     # Order ticket + stock selector
│   │   └── Transactions.jsx# Filterable transaction history
│   ├── App.jsx             # Layout, tab navigation, session handling
│   ├── App.css             # Tailwind import + custom effects
│   └── main.jsx            # React root bootstrap
├── package.json
├── requirements.txt
└── README.md
```

## Prerequisites
- Node.js 18+ and npm
- Python 3.10+ with pip
- SQLite (bundled with Python, no manual setup required)

## Setup & Installation
1. **Install frontend dependencies**
   ```bash
   npm install
   ```
2. **Create a Python virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```
3. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize the SQLite database** – The first backend launch runs `init_database()` and seeds the `stock_market.db` file automatically.

## Running the Apps
### Backend (Flask API)
```bash
cd backend
python app.py
```
- Starts on `http://127.0.0.1:5000`
- Provides REST endpoints for auth, stocks, trades, portfolio, and recovery logic
- Keep this terminal running while the frontend is active

### Frontend (Vite Dev Server)
```bash
npm run dev
```
- Serves the React app on the port Vite chooses (usually `5173`)
- Proxies are not configured; the UI talks to `http://127.0.0.1:5000` directly via the hard-coded `API_BASE_URL` constant in each component. Update that constant if the backend runs elsewhere.

### Additional npm Scripts
- `npm run build` – Production build
- `npm run lint` – ESLint (JS/JSX)
- `npm run preview` – Preview the production build locally

## API Overview
| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/register` | Create a new user with hashed password + ₹50,000 starting balance |
| POST | `/login` | Authenticate and return user profile + balance |
| GET | `/balance/<user_id>` | Fetch liquid balance |
| GET | `/stocks` | Return all stocks with simulated prices (updated ≥30s cadence) |
| GET | `/portfolio/<user_id>` | Holdings with current market value |
| GET | `/transactions/<user_id>` | Latest 50 trades enriched with stock meta |
| POST | `/buy` | Execute a buy order with balance checks and transaction log |
| POST | `/sell` | Execute a sell order with position validation |
| POST | `/recover-balance/<user_id>` | Apply ₹5,000 bonus if cooldown elapsed |
| GET | `/recovery-status/<user_id>` | Cooldown state + countdown timer |

## Data & Persistence
- All data lives in `stock_market.db` in the project root; delete the file to reset the simulation.
- Stock seeds include Indian large caps plus major US tech names for broader variety.
- Price ticks are pseudo-random (±35%) but clamped to stay ≥₹1.

## Configuration Notes
- `API_BASE_URL` is defined separately inside `Login.jsx`, `Dashboard.jsx`, `Portfolio.jsx`, `Trading.jsx`, and `Transactions.jsx`. If deploying the backend elsewhere, update those constants or move them to a shared config.
- Ensure CORS remains enabled (handled via `flask-cors`) when hosting the frontend separately.

## License
Distributed under the terms described in `LICENSE`.