"""
Utility functions for data formatting in options analytics.
"""
from typing import Dict, Any, List, Optional
from src.models.option_data import MarketData, ExpirationData, OptionData, StockData, VixData
from src.utils.time_utils import format_timestamp_for_api


def format_option_for_response(option: OptionData) -> Dict[str, Any]:
    """
    Format OptionData object for API response.
    
    Args:
        option: OptionData object to format
        
    Returns:
        Dictionary formatted for JSON response
    """
    def safe_round(value, decimals):
        return round(value, decimals) if value is not None else None
    
    def safe_get(attr_name):
        return getattr(option, attr_name, None)
    
    # Field mapping: response_key -> (attribute_name, decimal_places)
    numeric_fields = {
        "strike": ("strike", 2),
        "lastPrice": ("last_price", 2),
        "impliedVolatilityYF": ("implied_volatility", 4),
        "delta": ("delta", 4),
        "bid": ("bid", 2),
        "ask": ("ask", 2),
        "midPrice": ("mid_price", 2),
        "moneyness": ("moneyness", 3),
        "impliedVolatilityBid": ("implied_volatility_bid", 4),
        "impliedVolatilityMid": ("implied_volatility_mid", 4),
        "impliedVolatilityAsk": ("implied_volatility_ask", 4),
    }
    
    # Direct fields (no rounding needed)
    direct_fields = {
        "contractSymbol": "contract_symbol",
        "lastTradeDate": "last_trade_date",
        "volume": "volume",
        "openInterest": "open_interest",
    }
    
    # Build response
    response = {
        key: safe_round(safe_get(attr), decimals) 
        for key, (attr, decimals) in numeric_fields.items()
    }
    
    response.update({
        key: safe_get(attr) 
        for key, attr in direct_fields.items()
    })
    
    return response


def format_expiration_for_response(expiration: ExpirationData) -> Dict[str, Any]:
    """
    Format ExpirationData object for API response.
    
    Args:
        expiration: ExpirationData object to format
        
    Returns:
        Dictionary formatted for JSON response
    """
    response = {
        "expiration": expiration.expiration,
        "calls": [format_option_for_response(call) for call in expiration.calls],
        "puts": [format_option_for_response(put) for put in expiration.puts]
    }
    
    # Add days to expiration if available
    if expiration.days_to_expiration is not None:
        response["daysToExpiration"] = expiration.days_to_expiration
    
    # Add expiration label if available
    if expiration.expiration_label is not None:
        response["expirationLabel"] = expiration.expiration_label
    
    return response


def format_stock_data_for_response(stock_data: StockData) -> Dict[str, Any]:
    """
    Format StockData object for API response.
    
    Args:
        stock_data: StockData object to format
        
    Returns:
        Dictionary formatted for JSON response
    """
    return {
        "price": round(stock_data.price, 2),
        "previousClose": round(stock_data.previous_close, 2),
        "percentChange": round(stock_data.percent_change, 2),
        "timestamp": format_timestamp_for_api(stock_data.timestamp)
    }


def format_vix_data_for_response(vix_data: VixData) -> Dict[str, Any]:
    """
    Format VixData object for API response.
    
    Args:
        vix_data: VixData object to format
        
    Returns:
        Dictionary formatted for JSON response
    """
    return {
        "value": round(vix_data.value, 2),
        "previousClose": round(vix_data.previous_close, 2),
        "percentChange": round(vix_data.percent_change, 2),
        "timestamp": format_timestamp_for_api(vix_data.timestamp)
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
        "stock": format_stock_data_for_response(market_data.stock),
        "vix": format_vix_data_for_response(market_data.vix),
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
    
    # Basic validation: allow alphanumeric characters, dots, hyphens, and carets (for indices like ^SPX, ^VIX)
    if not all(c.isalnum() or c in '.-^' for c in cleaned_ticker):
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