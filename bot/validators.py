"""
Input validation for trading parameters.
All validation raises ValueError with descriptive messages on failure.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{3,20}$")


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a trading symbol.

    Args:
        symbol: Raw symbol string from user input.

    Returns:
        Upper-cased, stripped symbol.

    Raises:
        ValueError: If symbol is empty or contains invalid characters.
    """
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ValueError("Symbol must not be empty.")
    if not SYMBOL_PATTERN.match(cleaned):
        raise ValueError(
            f"Invalid symbol '{cleaned}'. "
            "Use only uppercase letters and digits (3–20 chars), e.g. BTCUSDT."
        )
    return cleaned


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive).

    Returns:
        Upper-cased side string.

    Raises:
        ValueError: If side is not BUY or SELL.
    """
    cleaned = side.strip().upper()
    if cleaned not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{cleaned}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return cleaned


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: Order type string (case-insensitive).

    Returns:
        Upper-cased order type string.

    Raises:
        ValueError: If order type is not supported.
    """
    cleaned = order_type.strip().upper()
    if cleaned not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{cleaned}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return cleaned


def validate_quantity(quantity: str | float) -> str:
    """
    Validate order quantity.

    Args:
        quantity: Quantity as string or float.

    Returns:
        String representation of the validated quantity.

    Raises:
        ValueError: If quantity is not a positive number.
    """
    try:
        value = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")

    if value <= 0:
        raise ValueError(f"Quantity must be positive, got {value}.")

    return str(value)


def validate_price(price: Optional[str | float], order_type: str) -> Optional[str]:
    """
    Validate order price.

    LIMIT orders require a price; MARKET orders must not supply one.

    Args:
        price: Price value (may be None for MARKET orders).
        order_type: Validated order type string.

    Returns:
        String representation of the validated price, or None.

    Raises:
        ValueError: If price rules are violated.
    """
    if order_type == "MARKET":
        if price is not None:
            raise ValueError("Price must not be specified for MARKET orders.")
        return None

    if order_type in ("LIMIT", "STOP"):
        if price is None:
            raise ValueError(f"Price is required for {order_type} orders.")
        try:
            value = Decimal(str(price))
        except InvalidOperation:
            raise ValueError(f"Price '{price}' is not a valid number.")
        if value <= 0:
            raise ValueError(f"Price must be positive, got {value}.")
        return str(value)

    # STOP_MARKET does not need a price
    return None


def validate_stop_price(stop_price: Optional[str | float], order_type: str) -> Optional[str]:
    """
    Validate stop price for STOP_MARKET / STOP orders.

    Args:
        stop_price: Stop trigger price (may be None for non-stop orders).
        order_type: Validated order type string.

    Returns:
        String representation of the validated stop price, or None.

    Raises:
        ValueError: If stop price rules are violated.
    """
    if order_type not in ("STOP_MARKET", "STOP"):
        return None

    if stop_price is None:
        raise ValueError(f"--stop-price is required for {order_type} orders.")

    try:
        value = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")

    if value <= 0:
        raise ValueError(f"Stop price must be positive, got {value}.")

    return str(value)
