"""
Put instantiated logger object here.
"""

from collections import namedtuple

Tick = namedtuple("Tick", ["timestamp", "open", "high", "low", "close", "volume"])
Balance = namedtuple("Balance", ["balance", "pendingFunds"])
TradeData = namedtuple("ChainTrade", ["id", "currency", "instrument", "orderSide", "price", "volume", "fee", "completionTime"])