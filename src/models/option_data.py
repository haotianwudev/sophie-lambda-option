"""
Data models for options analytics API.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class OptionData:
    """Data model for individual option contract."""
    strike: float
    last_price: float
    implied_volatility: Optional[float]  # This will be used as impliedVolatilityYF
    delta: Optional[float]
    option_type: str  # 'c' for call, 'p' for put
    contract_symbol: Optional[str] = None
    last_trade_date: Optional[str] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    mid_price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    moneyness: Optional[float] = None
    implied_volatility_bid: Optional[float] = None
    implied_volatility_mid: Optional[float] = None
    implied_volatility_ask: Optional[float] = None


@dataclass
class ExpirationData:
    """Data model for options grouped by expiration date."""
    expiration: str
    calls: List[OptionData]
    puts: List[OptionData]
    days_to_expiration: Optional[int] = None
    expiration_label: Optional[str] = None


@dataclass
class StockData:
    """Data model for stock price information."""
    price: float
    previous_close: float
    percent_change: float
    timestamp: datetime


@dataclass
class VixData:
    """Data model for VIX value information."""
    value: float
    previous_close: float
    percent_change: float
    timestamp: datetime


@dataclass
class MarketData:
    """Data model for complete market data response."""
    ticker: str
    stock: StockData
    vix: VixData
    expiration_dates: List[ExpirationData]