"""
Binance Futures Testnet REST API client.

Handles authentication (HMAC-SHA256), request signing, and HTTP communication.
All raw API interactions live here so the rest of the codebase stays clean.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures USDT-M REST API.

    Args:
        api_key: Binance Futures Testnet API key.
        api_secret: Binance Futures Testnet API secret.
        base_url: Base URL for the API (defaults to testnet).
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")

        self.api_key = api_key
        self._api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

        logger.info("BinanceClient initialised | base_url=%s", self.base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append HMAC-SHA256 signature to a parameters dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _timestamp(self) -> int:
        """Return current UTC timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request against the API.

        Args:
            method: HTTP verb ('GET' or 'POST').
            endpoint: API path, e.g. '/fapi/v1/order'.
            params: Query / body parameters.
            signed: Whether to add timestamp + signature.

        Returns:
            Parsed JSON response dict.

        Raises:
            BinanceAPIError: On non-2xx API error responses.
            requests.RequestException: On network-level failures.
        """
        params = params or {}

        if signed:
            params["timestamp"] = self._timestamp()
            params = self._sign(params)

        url = f"{self.base_url}{endpoint}"

        logger.debug(
            "HTTP %s %s | params=%s",
            method.upper(),
            endpoint,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=params, timeout=self.timeout)
            else:
                response = self._session.post(url, data=params, timeout=self.timeout)
        except requests.exceptions.Timeout:
            logger.error("Request timed out | url=%s", url)
            raise
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error | url=%s | error=%s", url, exc)
            raise

        logger.debug(
            "HTTP response | status=%s | body=%s",
            response.status_code,
            response.text[:500],
        )

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return {}

        # Binance returns errors as JSON with 'code' (negative int) and 'msg'
        if isinstance(data, dict) and "code" in data and int(data["code"]) < 0:
            if int(data["code"]) == -2015:
                logger.error(
                    "Authentication rejected (-2015). Verify API key/secret pair, "
                    "endpoint (testnet vs mainnet futures), and key permissions/IP whitelist."
                )
            logger.error(
                "API error | code=%s | msg=%s", data["code"], data.get("msg")
            )
            raise BinanceAPIError(int(data["code"]), data.get("msg", "Unknown error"))

        if not response.ok:
            response.raise_for_status()

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """Return Binance server time in milliseconds."""
        data = self._request("GET", "/fapi/v1/time")
        return data["serverTime"]

    def get_exchange_info(self) -> Dict[str, Any]:
        """Return exchange info including symbol filters."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> Dict[str, Any]:
        """Return account information (requires authentication)."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        stop_price: Optional[str] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a futures order.

        Args:
            symbol: Trading symbol, e.g. 'BTCUSDT'.
            side: 'BUY' or 'SELL'.
            order_type: 'MARKET', 'LIMIT', 'STOP_MARKET', or 'STOP'.
            quantity: Order quantity as a string.
            price: Limit price (required for LIMIT / STOP).
            stop_price: Stop trigger price (required for STOP_MARKET / STOP).
            time_in_force: 'GTC', 'IOC', or 'FOK' (LIMIT only).
            reduce_only: Whether this order only reduces an existing position.

        Returns:
            Raw order response dict from Binance.

        Raises:
            BinanceAPIError: On API-level order rejection.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP":
            params["price"] = price
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            params["stopPrice"] = stop_price

        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info(
            "Placing order | symbol=%s side=%s type=%s qty=%s price=%s",
            symbol,
            side,
            order_type,
            quantity,
            price or "N/A",
        )

        response = self._request("POST", "/fapi/v1/order", params=params, signed=True)

        logger.info(
            "Order placed | orderId=%s status=%s execQty=%s avgPrice=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
            response.get("avgPrice"),
        )

        return response

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order by ID."""
        params = {"symbol": symbol, "orderId": order_id}
        logger.info("Cancelling order | symbol=%s orderId=%s", symbol, order_id)
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Return all open orders, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)
