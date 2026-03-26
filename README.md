# AI Trading Analytics (Flask + AI Predictions)

AI Trading Analytics is a Flask web application that provides **AI-powered price predictions**. It includes user registration/login, a dashboard, prediction pages, prediction history/performance, and exchange account/portfolio views.

The app uses:
- A pre-trained scikit-learn model (stored under `FProject/AI trading analytics/services/models/`)
- Live market data from exchanges via `ccxt` (for OHLCV candles and derived inputs)
- A SQLite database (by default) to store users, exchange accounts, and prediction history

## Features

- User system: register, login/logout, and protected pages
- Dashboard and portfolio pages
- Prediction pages/endpoints (latest + on-demand predictions, including “advanced” prediction)
- Prediction history/performance tracking (advanced prediction page uses prediction history endpoints)
- Market widgets (example: Fear & Greed index on the dashboard)
- Exchange account management and exchange connectivity (add/delete/test + exchange portfolio view)
- App policy pages: FAQ, Privacy Policy, Terms
- Profile management (update personal info via the app)

## Requirements (dependencies)

Recommended:
- Python 3.9+

Install dependencies with pip:

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Notes:
- `flask` pulls in its standard web dependencies (Werkzeug/Jinja2/etc.).
- The AI model uses `scikit-learn` and `joblib` for training and inference.
- Market data comes from `ccxt`.

## Setup

1. (Optional but recommended) Create a virtual environment:

```bash
cd "/Users/farrukh/Downloads/AI Final Project"
python3 -m venv .venv
source .venv/bin/activate
```

2. Go to the app directory:

```bash
cd "/Users/farrukh/Downloads/AI Final Project/FProject/AI trading analytics"
```

3. Database:
   - By default, the app uses SQLite via `models/db.py` and expects `ai_trading.db` in the same project directory.
   - If you want to recreate the SQLite DB from scratch, run:

```bash
python3 scripts/setup_sqlite.py
```

   - (Optional) If you want to use MySQL instead, run:

```bash
python3 setup_database.py
```

   This requires MySQL credentials in `config.py`.

## Run the project (use pre-trained model)

From inside `FProject/AI trading analytics`:

```bash
./run.sh
```

Then open:
- http://127.0.0.1:5002/

## Project location / important files

- Flask app entry point: `FProject/AI trading analytics/app.py`
- Run scripts:
  - `FProject/AI trading analytics/run.sh`
  - `FProject/AI trading analytics/train.sh`
- SQLite DB file (default): `FProject/AI trading analytics/ai_trading.db`
- Tests runner: `FProject/AI trading analytics/run_tests.py`

