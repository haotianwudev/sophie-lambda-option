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
    implied_volatility: Optional[float]
    delta: Optional[float]
    option_type: str  # 'c' for call, 'p' for put


@dataclass
class ExpirationData:
    """Data model for options grouped by expiration date."""
    expiration: str
    calls: List[OptionData]
    puts: List[OptionData]


@dataclass
class MarketData:
    """Data model for complete market data response."""
    ticker: str
    stock_price: float
    vix_value: float
    data_timestamp: datetime
    vix_timestamp: datetime
    expiration_dates: List[ExpirationData]