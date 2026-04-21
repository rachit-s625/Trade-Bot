#!/usr/bin/env python3
"""
Trading Bot CLI – Binance Futures Testnet (USDT-M)

Usage examples:
  # Market BUY
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit SELL
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

  # Stop-Market BUY
  python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 95000

  # Stop-Limit SELL (bonus order type)
  python cli.py place --symbol BTCUSDT --side SELL --type STOP --quantity 0.001 --price 90000 --stop-price 91000

  # Account info
  python cli.py account

  # Open orders
  python cli.py open-orders --symbol BTCUSDT
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logging
from bot.orders import place_order

# ---------------------------------------------------------------------------
# Load credentials from environment variables (preferred) or prompt the user
# ---------------------------------------------------------------------------

def _get_credentials() -> tuple[str, str]:
    api_key = os.environ.get("BINANCE_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_API_SECRET", "").strip()

    if not api_key:
        api_key = input("Enter your Binance Futures Testnet API key   : ").strip()
    if not api_secret:
        api_secret = input("Enter your Binance Futures Testnet API secret: ").strip()

    if not api_key or not api_secret:
        print("❌  API credentials are required. Exiting.")
        sys.exit(1)

    return api_key, api_secret


def _get_base_url(cli_base_url: str | None) -> str:
    """
    Resolve the Binance base URL from CLI flag or environment.

    Precedence:
      1) --base-url
      2) BINANCE_BASE_URL
      3) Binance Futures Testnet default
    """
    if cli_base_url and cli_base_url.strip():
        return cli_base_url.strip().rstrip("/")

    env_base_url = os.environ.get("BINANCE_BASE_URL", "").strip()
    if env_base_url:
        return env_base_url.rstrip("/")

    return "https://testnet.binancefuture.com"


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_place(args: argparse.Namespace, client: BinanceClient) -> int:
    """Handle the 'place' sub-command."""
    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
        time_in_force=args.time_in_force,
        reduce_only=args.reduce_only,
    )
    result.print_summary()
    return 0 if result.success else 1


def cmd_account(args: argparse.Namespace, client: BinanceClient) -> int:
    """Handle the 'account' sub-command."""
    try:
        data = client.get_account()
        print("\n📊  Account Information")
        print("─" * 55)
        print(f"  Total Wallet Balance : {data.get('totalWalletBalance', 'N/A')} USDT")
        print(f"  Available Balance    : {data.get('availableBalance', 'N/A')} USDT")
        print(f"  Total Unrealised PnL : {data.get('totalUnrealizedProfit', 'N/A')} USDT")
        print("─" * 55 + "\n")
        return 0
    except BinanceAPIError as exc:
        print(f"\n❌  API error [{exc.code}]: {exc.message}\n")
        return 1
    except Exception as exc:
        print(f"\n❌  Error: {exc}\n")
        return 1


def cmd_open_orders(args: argparse.Namespace, client: BinanceClient) -> int:
    """Handle the 'open-orders' sub-command."""
    try:
        orders = client.get_open_orders(symbol=args.symbol)
        if not orders:
            print("\n  No open orders found.\n")
            return 0
        print(f"\n📋  Open Orders ({len(orders)} found)")
        print("─" * 55)
        for o in orders:
            print(
                f"  [{o.get('orderId')}] {o.get('symbol')} "
                f"{o.get('side')} {o.get('type')} "
                f"qty={o.get('origQty')} price={o.get('price')} "
                f"status={o.get('status')}"
            )
        print("─" * 55 + "\n")
        return 0
    except BinanceAPIError as exc:
        print(f"\n❌  API error [{exc.code}]: {exc.message}\n")
        return 1
    except Exception as exc:
        print(f"\n❌  Error: {exc}\n")
        return 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description=textwrap.dedent(
            """\
            Binance Futures Testnet Trading Bot
            -----------------------------------
            Place MARKET, LIMIT, STOP_MARKET, and STOP orders
            on Binance Futures Testnet (USDT-M).
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Binance Futures API base URL. "
            "Examples: https://testnet.binancefuture.com or https://fapi.binance.com"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- place ---
    place_parser = subparsers.add_parser(
        "place",
        help="Place a new futures order",
        description="Place a MARKET, LIMIT, STOP_MARKET, or STOP order.",
    )
    place_parser.add_argument(
        "--symbol", "-s",
        required=True,
        metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT",
    )
    place_parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        type=str.upper,
        help="Order side: BUY or SELL",
    )
    place_parser.add_argument(
        "--type", "-t",
        required=True,
        dest="type",
        choices=["MARKET", "LIMIT", "STOP_MARKET", "STOP"],
        type=str.upper,
        help="Order type",
    )
    place_parser.add_argument(
        "--quantity", "-q",
        required=True,
        help="Order quantity (e.g. 0.001)",
    )
    place_parser.add_argument(
        "--price", "-p",
        default=None,
        help="Limit price – required for LIMIT and STOP orders",
    )
    place_parser.add_argument(
        "--stop-price",
        default=None,
        dest="stop_price",
        help="Stop trigger price – required for STOP_MARKET and STOP orders",
    )
    place_parser.add_argument(
        "--time-in-force",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        dest="time_in_force",
        help="Time-in-force for LIMIT orders (default: GTC)",
    )
    place_parser.add_argument(
        "--reduce-only",
        action="store_true",
        dest="reduce_only",
        help="Mark order as reduce-only (closes an existing position)",
    )

    # --- account ---
    subparsers.add_parser("account", help="Show account balances")

    # --- open-orders ---
    oo_parser = subparsers.add_parser("open-orders", help="List open orders")
    oo_parser.add_argument(
        "--symbol", "-s",
        default=None,
        help="Filter by symbol (optional)",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(args.log_level)

    api_key, api_secret = _get_credentials()
    base_url = _get_base_url(args.base_url)

    try:
        client = BinanceClient(api_key=api_key, api_secret=api_secret, base_url=base_url)
    except ValueError as exc:
        print(f"❌  Configuration error: {exc}")
        sys.exit(1)

    handlers = {
        "place": cmd_place,
        "account": cmd_account,
        "open-orders": cmd_open_orders,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    exit_code = handler(args, client)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
