# MarketLens

## See what changed. Know what matters.

MarketLens is a personalized stock-monitoring platform designed to help users quickly understand what meaningfully changed in their tracked stocks since their last check. Instead of repeatedly checking raw price data, MarketLens establishes a user-specific reference point and highlights changes using deterministic, explainable scoring rules.

## Problem Statement

Users who actively track stocks face a fundamental problem: repeatedly checking price movements provides little insight into what has *meaningfully changed* since their previous check. Current financial tools overwhelm users with raw data—open, high, low, close, volume—without context about what actually matters relative to when they last looked.

MarketLens solves this by:

1. **Eliminating repetitive rechecking** — Users establish a personal reference point (baseline) for each stock.
2. **Providing meaning beyond raw prices** — The system detects meaningful changes using deterministic rules, not speculation.
3. **Personalizing the experience** — Each user has their own reference points and watchlists, ensuring their baseline is relevant to their investment timeline.
4. **Making attention explainable** — Changes are scored using transparent, rule-based logic, not opaque algorithms.

## Solution

MarketLens provides an integrated platform for stock tracking:

### User Workflow

1. **Sign up / Log in** — Create a personal account
2. **Browse or search stocks** — Explore the available stock catalogue (NSE stocks by default)
3. **Create watchlists** — Organize stocks into custom watchlists
4. **Add stocks to watchlists** — Build a portfolio to monitor
5. **Establish a baseline** — Click "Check stock" to set your reference price and timestamp
6. **Market snapshots collected** — The system continuously collects market data (every 5 minutes during NSE market hours)
7. **Compare with latest data** — When you revisit a stock, MarketLens compares the latest snapshot with your reference
8. **Detect meaningful changes** — Analyzes price, volume, important levels, and movement patterns
9. **Calculate attention score** — Assigns a deterministic score (0–100) based on change factors
10. **Display results** — Dashboard and stock details pages show changes and attention levels

### Key Design Principles

- **Backend-driven:** All business logic (change detection, attention scoring) runs on the backend. Frontend is a data display layer.
- **User-specific baseline:** Your reference point is independent of other users. Only your explicit stock checks update it.
- **Deterministic scoring:** Attention levels are calculated using transparent rules, not machine learning or hidden algorithms.
- **Attention is informational:** Attention scores are *NOT* buy/sell recommendations or financial predictions. They highlight what changed relative to your baseline.

## Key Features

- **User Authentication** — Secure signup/login with password hashing and JWT tokens
- **Stock Catalogue** — Browse 10 pre-seeded NSE stocks (RELIANCE, TCS, INFY, HDFC, ICICI, SBI, ITC, BHARTI, LT, AXIS)
- **Search Functionality** — Search stocks by symbol or company name
- **Watchlists** — Create and manage multiple custom watchlists
- **Add/Remove Stocks** — Manage stocks within watchlists
- **Personalized Baseline** — Establish and update reference prices and timestamps for each stock
- **Market Data Collection** — Automated 5-minute snapshot collection during NSE market hours (9:15 AM – 3:30 PM IST, weekdays)
- **Change Detection** — Deterministic comparison of latest data with user baseline
- **Attention Scoring** — Rule-based scoring considering price, volume, important levels, and sustained movement
- **Dashboard** — Overview of all tracked stocks with change summaries
- **Stock Details** — Detailed view of individual stock changes and attention metrics
- **Responsive UI** — Works on desktop and mobile browsers
- **Dark/Light Theme** — Toggle between dark and light display modes
- **Error Handling** — Clear, user-friendly error messages for edge cases

## How MarketLens Works

```
┌─────────────────────────────────────────────────────────────────┐
│ USER INTERACTION                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. Signup / Login                                               │
│ 2. Create Watchlist                                             │
│ 3. Add Stocks                                                   │
│ 4. Check Stock (Establish Baseline)                             │
│ 5. View Dashboard / Stock Details                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND PROCESSING                                               │
├─────────────────────────────────────────────────────────────────┤
│ • Collect market snapshots (every 5 min, 9:15–15:30 IST)       │
│ • Store in database (PostgreSQL)                               │
│ • Calculate change vs. user baseline                           │
│ • Detect important levels (prev day high/low)                 │
│ • Analyze volume change                                        │
│ • Detect sustained movement (3+ consecutive directions)       │
│ • Calculate attention score (0–100)                           │
│ • Assign attention level (HIGH/NOTABLE/MILD/NO_NOTABLE)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND DISPLAY                                                 │
├─────────────────────────────────────────────────────────────────┤
│ • Dashboard: Summary of all tracked stocks                      │
│ • Watchlist: Stocks organized by watchlist                      │
│ • Stock Details: Full change data and attention metrics        │
│ • No client-side calculations (backend is source of truth)     │
└─────────────────────────────────────────────────────────────────┘
```

## Attention Scoring

Attention is a deterministic score (0–100) that quantifies meaningful change. It combines four independent factors:

| Factor | Maximum Score | Calculation |
|---|---:|---|
| **Price Movement** | 40 | Based on percentage change magnitude |
| **Volume Change** | 25 | Based on percentage change from previous snapshot |
| **Important Level Crossed** | 20 | Previous trading day high/low crossing |
| **Sustained Movement** | 15 | 3+ consecutive snapshots moving same direction |
| **Total** | **100** | Sum of all factors (capped at 100) |


### Attention Levels

| Level | Score Range | Interpretation |
|---|---:|---|
| **HIGH** | 75–100 | Significant meaningful change |
| **NOTABLE** | 50–74 | Meaningful change observed |
| **MILD** | 25–49 | Some change, not substantial |
| **NO_NOTABLE_CHANGE** | 0–24 | Minimal meaningful change |

### Important Notes on Attention

- **Attention is informational** — It indicates *what changed relative to your baseline*, not whether you should buy or sell.
- **Not a prediction** — Attention does not predict future price movement.
- **Not a recommendation** — Attention is not financial advice.
- **Deterministic** — The same data always produces the same attention score using transparent rules.

## Architecture

### System Design

MarketLens follows a client-server architecture:

- **Frontend:** React SPA (Single Page Application) running in the browser
- **Backend:** FastAPI REST API processing all business logic
- **Database:** PostgreSQL storing users, stocks, watchlists, market snapshots, and user baselines
- **Market Data:** yfinance library fetching NSE stock data
- **Authentication:** JWT tokens for stateless session management

### Data Flow

1. **User Action** → Frontend HTTP request
2. **API Endpoint** → FastAPI validates and routes to handler
3. **Business Logic** → Python backend calculates changes, scores, etc.
4. **Database Query** → PostgreSQL returns historical data
5. **Response** → JSON response sent to frontend
6. **Display** → React renders data without recalculating

### Key Principle: Backend is Source of Truth

All meaningful calculations happen on the backend:
- Change detection
- Attention scoring
- Baseline management
- Watchlist aggregation

The frontend is a **presentation layer** that displays backend-computed data. No business logic is duplicated in React.

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend UI** | React 19 | Interactive user interface |
| **Build Tool** | Vite 8 | Development and production bundling |
| **Backend Framework** | FastAPI | REST API and request handling |
| **Backend Runtime** | Python 3.10+ | Server-side logic execution |
| **Database** | PostgreSQL | Persistent data storage |
| **ORM** | SQLAlchemy 2 | Database interaction layer |
| **Authentication** | JWT (PyJWT) | Secure session tokens |
| **Password Hashing** | bcrypt | Secure password storage |
| **Market Data** | yfinance | Fetch NSE stock prices |
| **API Validation** | Pydantic | Request/response schema validation |
| **Task Scheduling** | APScheduler | 5-minute snapshot collection |
| **Linting** | ESLint | Code quality (frontend) |

## Project Structure

```
MarketLens/
├── backend/
│   ├── app/
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── schemas.py             # Pydantic request/response schemas
│   │   ├── database.py            # Database connection and session management
│   │   ├── auth.py                # Authentication (JWT, hashing, user routes)
│   │   ├── stocks.py              # Stock endpoints and search
│   │   ├── watchlists.py          # Watchlist CRUD operations
│   │   ├── market_data.py         # yfinance market data fetching
│   │   ├── snapshot_collector.py  # 5-minute background task for data collection
│   │   ├── change_detection.py    # Deterministic change calculation
│   │   ├── attention_engine.py    # Attention scoring logic
│   │   ├── dashboard.py           # Dashboard aggregation endpoints
│   │   └── __init__.py
│   ├── main.py                    # FastAPI app initialization and startup
│   ├── .env                       # Environment variables (not committed)
│   ├── .env.example               # Environment template
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # Main dashboard view
│   │   │   ├── Watchlists.jsx     # Watchlist list page
│   │   │   ├── WatchlistDetails.jsx # Watchlist detail with stocks
│   │   │   ├── Stocks.jsx         # All stocks with pagination
│   │   │   ├── Search.jsx         # Stock discovery/search
│   │   │   └── Signup.jsx         # User registration
│   │   ├── components/
│   │   │   ├── LoginScreen.jsx    # Login form
│   │   │   ├── StockDetailsPage.jsx # Individual stock detail
│   │   │   ├── AddStockModal.jsx  # Modal to add stock to watchlist
│   │   │   ├── Navbar.jsx         # Top navigation
│   │   │   ├── ProtectedRoute.jsx # Auth wrapper
│   │   │   ├── ErrorBoundary.jsx  # Error handling
│   │   │   └── ... (other components)
│   │   ├── context/
│   │   │   └── AuthContext.jsx    # Global auth state
│   │   ├── services/
│   │   │   ├── api.js             # Centralized HTTP client
│   │   │   ├── auth.js            # Auth service
│   │   │   ├── stocks.js          # Stock API calls
│   │   │   ├── watchlists.js      # Watchlist API calls
│   │   │   └── dashboard.js       # Dashboard API calls
│   │   ├── layouts/
│   │   │   └── AppLayout.jsx      # Common layout wrapper
│   │   ├── App.jsx                # Main app routing
│   │   ├── App.css                # Global styles
│   │   ├── index.css              # Base styles
│   │   └── main.jsx               # React entry point
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js             # Vite build configuration
│   ├── eslint.config.js           # ESLint configuration
│   ├── index.html                 # HTML template
│   ├── .env.local                 # Frontend env (not committed)
│   └── .gitignore
│
└── README.md
```

## Market Data Handling

### Data Collection

- **Frequency:** Every 5 minutes during NSE market hours
- **Timing:** 9:15 AM – 3:30 PM IST, weekdays (Monday–Friday)
- **Source:** yfinance library fetching NSE stock quotes
- **Storage:** PostgreSQL `market_snapshots` table
- **Scheduler:** APScheduler background task

### Data Validation

- Timestamps must be timezone-aware
- Data must fall within NSE market hours
- Timestamps must be from today's trading session
- Duplicate snapshots (same stock, same timestamp) prevented by unique constraint

### NSE-Specific Handling

- **Market Hours:** 9:15 AM – 3:30 PM IST (weekdays only)
- **Timezone:** All data stored in UTC, converted to IST (UTC+5:30) for comparison
- **Weekend/Holiday:** Collection skipped; no snapshots collected
- **Previous Day High/Low:** Calculated from all previous day's snapshots for important level detection

## Setup and Installation

### Prerequisites

- **Python:** 3.10 or later
- **Node.js:** 18 or later
- **npm:** 9 or later (bundled with Node.js)
- **PostgreSQL:** 12 or later
- **Git:** For version control

### Clone Repository

```bash
git clone https://github.com/nehasree25/MarketLens.git
cd MarketLens
```

### Backend Setup

#### 1. Create Virtual Environment

```bash
cd backend
python -m venv env

# Activate (Windows)
env\Scripts\activate

# Activate (macOS/Linux)
source env/bin/activate
```

#### 2. Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic[email] pyjwt bcrypt yfinance apscheduler python-dotenv
```

#### 3. Configure Database

Create a PostgreSQL database:

```bash
createdb marketlens
```

#### 4. Environment Variables

Create `.env` in the `backend` directory:

```bash
DATABASE_URL=postgresql+psycopg2://marketlens:your_password@localhost:5432/marketlens
ADMIN_NAME=Admin
ADMIN_EMAIL=admin@marketlens.local
ADMIN_PASSWORD=AdminPassword123!
```

#### 5. Run Backend

```bash
python main.py
```

Backend runs at `http://127.0.0.1:8000`

API documentation available at `http://127.0.0.1:8000/docs`

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Environment Variables

Create `.env.local` in the `frontend` directory:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

#### 3. Run Development Server

```bash
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`

#### 4. Build for Production

```bash
npm run build
```

Output in `frontend/dist/` directory

## Running the Application

### Development

**Terminal 1 (Backend):**
```bash
cd backend
source env/bin/activate  # or env\Scripts\activate on Windows
uvicorn main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173` in your browser.


**MarketLens: See what changed. Know what matters.**
