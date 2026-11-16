"""Read-only Order Flow market-data service.

The adapter joins gateway Type A ticks to the existing m.Stock instrument
master. It never changes the existing cash-market or order-execution paths.
"""
from app.services.order_flow_gateway_adapter import (
    OrderFlowFeedError,
    get_order_flow_snapshot,
)

__all__ = ["OrderFlowFeedError", "get_order_flow_snapshot"]
