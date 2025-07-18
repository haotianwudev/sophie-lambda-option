"""
Utility functions for data formatting in options analytics.
"""
from typing import Dict, Any, List, Optional
from src.models.option_data import MarketData, ExpirationData, OptionData
from src.utils.time_utils import format_timestamp_for_api


def format_option_for_response(option: OptionData) -> Dict[str, Any]:
    """
    Format OptionData object for API response.
    
    Args:
        option: OptionData object to format
        
    Returns:
        Dictionary formatted for JSON response
    """
    return {
        "strike": round(option.strike, 2),
        "lastPrice": round(option.last_price, 2) if option.last_price else None,
        "impliedVolatility": round(option.implied_volatility, 4) if option.implied_volatility else None,
        "delta": round(option.delta, 4) if option.delta else None
    }


def format_expiration_for_response(expiration: ExpirationData) -> Dict[str, Any]:
    """
    Format ExpirationData object for API response.
    
    Args:
        expiration: ExpirationData object to format
        
    Returns:
        Dictionary formatted for JSON response
    """
    return {
        "expiration": expiration.expiration,
        "calls": [format_option_for_response(call) for call in expiration.calls],
        "puts": [format_option_for_response(put) for put in expiration.puts]
    }


def format_market_data_for_response(market_data: MarketData) -> Dict[str, Any]:
    """
    Format MarketData object for complete API response.
    
    Args:
        market_data: MarketData object to format
        
    Returns:
        Dictionary formatted for JSON response
    """
    return {
        "ticker": market_data.ticker.upper(),
        "stockPrice": round(market_data.stock_price, 2),
        "vixValue": round(market_data.vix_value, 2),
        "dataTimestamp": format_timestamp_for_api(market_data.data_timestamp),
        "vixTimestamp": format_timestamp_for_api(market_data.vix_timestamp),
        "expirationDates": [
            format_expiration_for_response(exp) 
            for exp in market_data.expiration_dates
        ]
    }


def validate_ticker_symbol(ticker: str) -> str:
    """
    Validate and format ticker symbol.
    
    Args:
        ticker: Raw ticker symbol
        
    Returns:
        Cleaned and validated ticker symbol
        
    Raises:
        ValueError: If ticker is invalid
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string")
    
    # Clean ticker: remove whitespace and convert to uppercase
    cleaned_ticker = ticker.strip().upper()
    
    # Basic validation: alphanumeric characters only
    if not cleaned_ticker.replace('.', '').replace('-', '').isalnum():
        raise ValueError(f"Invalid ticker symbol: {ticker}")
    
    return cleaned_ticker


def filter_valid_options(options: List[OptionData]) -> List[OptionData]:
    """
    Filter out options with invalid data.
    
    Args:
        options: List of OptionData objects
        
    Returns:
        List of valid OptionData objects
    """
    valid_options = []
    
    for option in options:
        # Skip options with invalid strike or last price
        if option.strike <= 0 or option.last_price is None or option.last_price <= 0:
            continue
            
        # Skip options where both IV and delta calculations failed
        if option.implied_volatility is None and option.delta is None:
            continue
            
        valid_options.append(option)
    
    return valid_options