"""
Order placement and result formatting logic.

This module sits between the CLI layer and the raw API client.
It handles validation, builds the order payload, delegates to
BinanceClient, and formats human-readable output.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from bot.client import BinanceClient, BinanceAPIError
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = logging.getLogger(__name__)


class OrderResult:
    """Structured representation of a placed order."""

    def __init__(self, success: bool, data: Dict[str, Any], message: str) -> None:
        self.success = success
        self.data = data
        self.message = message

    def print_summary(self) -> None:
        """Pretty-print the order result to stdout."""
        separator = "─" * 55

        if self.success:
            print(f"\n{'✅ ORDER PLACED SUCCESSFULLY':^55}")
        else:
            print(f"\n{'❌ ORDER FAILED':^55}")

        print(separator)
        print(self.message)

        if self.success and self.data:
            d = self.data
            print(separator)
            print(f"  Order ID     : {d.get('orderId', 'N/A')}")
            print(f"  Symbol       : {d.get('symbol', 'N/A')}")
            print(f"  Side         : {d.get('side', 'N/A')}")
            print(f"  Type         : {d.get('type', 'N/A')}")
            print(f"  Orig Qty     : {d.get('origQty', 'N/A')}")
            print(f"  Executed Qty : {d.get('executedQty', 'N/A')}")
            print(f"  Avg Price    : {d.get('avgPrice', 'N/A')}")
            print(f"  Status       : {d.get('status', 'N/A')}")
            if d.get("price") and float(d.get("price", 0)) > 0:
                print(f"  Limit Price  : {d.get('price')}")
            if d.get("stopPrice") and float(d.get("stopPrice", 0)) > 0:
                print(f"  Stop Price   : {d.get('stopPrice')}")
            print(f"  Time In Force: {d.get('timeInForce', 'N/A')}")
            print(f"  Update Time  : {d.get('updateTime', 'N/A')}")

        print(separator + "\n")


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
    time_in_force: str = "GTC",
    reduce_only: bool = False,
) -> OrderResult:
    """
    Validate inputs, place an order via the client, and return an OrderResult.

    Args:
        client: Authenticated BinanceClient instance.
        symbol: Trading symbol.
        side: 'BUY' or 'SELL'.
        order_type: 'MARKET', 'LIMIT', 'STOP_MARKET', or 'STOP'.
        quantity: Order quantity.
        price: Limit/stop-limit price.
        stop_price: Trigger price for STOP / STOP_MARKET orders.
        time_in_force: GTC | IOC | FOK (for LIMIT orders).
        reduce_only: If True, order only reduces an existing position.

    Returns:
        OrderResult with success flag, raw data, and a human-readable message.
    """
    # --- Validate all inputs first ---
    try:
        symbol = validate_symbol(symbol)
        side = validate_side(side)
        order_type = validate_order_type(order_type)
        quantity = validate_quantity(quantity)
        price = validate_price(price, order_type)
        stop_price = validate_stop_price(stop_price, order_type)
    except ValueError as exc:
        logger.warning("Validation failed | %s", exc)
        return OrderResult(success=False, data={}, message=f"Validation error: {exc}")

    # --- Print request summary before sending ---
    _print_request_summary(symbol, side, order_type, quantity, price, stop_price)

    # --- Send to exchange ---
    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            reduce_only=reduce_only,
        )
        return OrderResult(
            success=True,
            data=response,
            message=(
                f"Order #{response.get('orderId')} accepted by exchange. "
                f"Status: {response.get('status')}."
            ),
        )

    except BinanceAPIError as exc:
        logger.error("Order placement failed | code=%s msg=%s", exc.code, exc.message)
        return OrderResult(
            success=False,
            data={},
            message=f"API error [{exc.code}]: {exc.message}",
        )
    except Exception as exc:
        logger.exception("Unexpected error during order placement")
        return OrderResult(
            success=False,
            data={},
            message=f"Unexpected error: {exc}",
        )


def _print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str],
    stop_price: Optional[str],
) -> None:
    """Print a clean summary of what is about to be sent."""
    separator = "─" * 55
    print(f"\n{'📤 ORDER REQUEST SUMMARY':^55}")
    print(separator)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price:
        print(f"  Price      : {price}")
    if stop_price:
        print(f"  Stop Price : {stop_price}")
    print(separator)
    logger.info(
        "Order request | symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, quantity, price or "N/A", stop_price or "N/A",
    )
