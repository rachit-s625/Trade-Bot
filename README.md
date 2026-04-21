# Trade-Bot

A clean, structured Python CLI application for placing orders on the **Binance Futures Testnet (USDT-M)**. Built with layered separation of concerns, structured logging, and comprehensive input validation.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API client (auth, signing, HTTP)
│   ├── orders.py          # Order placement logic & result formatting
│   ├── validators.py      # Input validation (all raises ValueError on failure)
│   └── logging_config.py  # Rotating file + console log setup
├── cli.py                 # CLI entry point (argparse sub-commands)
├── logs/
│   └── trading_bot.log    # Auto-created; rotates at 5 MB, keeps 3 backups
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Python version

Python **3.10+** recommended (uses `str | float` union type hints).

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Futures Testnet credentials

1. Go to <https://testnet.binancefuture.com>
2. Sign in (or create an account).
3. Navigate to **API Management** → generate an API key pair.
4. Keep your **API Key** and **Secret Key** handy.

### 5. Set environment variables (recommended)

```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

On Windows (PowerShell):

```powershell
$env:BINANCE_API_KEY    = "your_api_key_here"
$env:BINANCE_API_SECRET = "your_api_secret_here"
```

If environment variables are not set, the CLI will prompt you at runtime.

---

## How to Run

All commands follow the pattern:

```
python cli.py [--log-level LEVEL] <sub-command> [options]
```

### Place a MARKET order

```bash
# BUY 0.001 BTC at market price
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# SELL 0.01 ETH at market price
python cli.py place --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
# BUY 0.001 BTC with a limit at 80,000 USDT
python cli.py place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 80000

# SELL 0.001 BTC with a limit at 100,000 USDT (GTC by default)
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

# IOC limit order
python cli.py place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 80000 --time-in-force IOC
```

### Place a STOP_MARKET order *(bonus)*

Triggers a market order when the stop price is reached.

```bash
# BUY stop-market when BTCUSDT hits 95,000
python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 95000
```

### Place a STOP (Stop-Limit) order *(bonus)*

Triggers a limit order at `--price` when `--stop-price` is reached.

```bash
# SELL stop-limit: trigger @ 91,000, limit @ 90,000
python cli.py place --symbol BTCUSDT --side SELL --type STOP --quantity 0.001 \
  --price 90000 --stop-price 91000
```

### View account balances

```bash
python cli.py account
```

### List open orders

```bash
# All open orders
python cli.py open-orders

# Filtered by symbol
python cli.py open-orders --symbol BTCUSDT
```

### Verbose debug logging

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

## Sample Output

```
📤 ORDER REQUEST SUMMARY
───────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
───────────────────────────────────────────────────────

          ✅ ORDER PLACED SUCCESSFULLY
───────────────────────────────────────────────────────
  Order #4095652841 accepted by exchange. Status: FILLED.
───────────────────────────────────────────────────────
  Order ID     : 4095652841
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Orig Qty     : 0.001
  Executed Qty : 0.001
  Avg Price    : 84231.50
  Status       : FILLED
  Time In Force: GTC
  Update Time  : 1752307443231
───────────────────────────────────────────────────────
```

---

## Logging

Logs are written to `logs/trading_bot.log`. The file rotates at **5 MB** and keeps **3 backups**.

| Level | Written to       | Content                                      |
|-------|------------------|----------------------------------------------|
| DEBUG | File only        | Full HTTP params, raw response bodies        |
| INFO  | File + console   | Order summaries, lifecycle events            |
| WARN  | File + console   | Validation failures                          |
| ERROR | File + console   | API errors, network failures                 |

---

## Assumptions

- **Testnet only** – `BASE_URL` is hard-coded to `https://testnet.binancefuture.com`. Change `bot/client.py` for production use.
- **USDT-M futures** – only `/fapi/v1/` endpoints are used.
- **No position mode check** – assumes the account is in **One-way** (BOTH) position mode.
- **Quantity precision** – the user is responsible for supplying a quantity that meets the symbol's `LOT_SIZE` filter; the bot does not auto-round.
- **Dependencies** – only `requests` is required; no third-party Binance SDK is used to keep the dependency footprint minimal and the client fully transparent.

---

## Requirements

```
requests>=2.31.0
```

---

## License

MIT
