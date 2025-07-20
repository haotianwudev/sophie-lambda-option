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
    response = {
        "strike": round(option.strike, 2),
        "lastPrice": round(option.last_price, 2) if option.last_price else None,
        "impliedVolatilityYF": round(option.implied_volatility, 4) if option.implied_volatility else None,
        "delta": round(option.delta, 4) if option.delta else None
    }
    
    # Add contract symbol if available
    if option.contract_symbol:
        response["contractSymbol"] = option.contract_symbol
    
    # Add last trade date if available
    if option.last_trade_date:
        response["lastTradeDate"] = option.last_trade_date
    
    # Add bid and ask if available
    if option.bid is not None:
        response["bid"] = round(option.bid, 2)
    
    if option.ask is not None:
        response["ask"] = round(option.ask, 2)
    
    # Add mid price if available
    if option.mid_price is not None:
        response["midPrice"] = round(option.mid_price, 2)
    
    # Add volume and open interest if available
    if option.volume is not None:
        response["volume"] = option.volume
    
    if option.open_interest is not None:
        response["openInterest"] = option.open_interest
    
    # Add moneyness if available
    if option.moneyness is not None:
        response["moneyness"] = round(option.moneyness, 3)
    
    # Add the new implied volatility fields
    if option.implied_volatility_bid is not None:
        response["impliedVolatilityBid"] = round(option.implied_volatility_bid, 4)
    
    if option.implied_volatility_mid is not None:
        response["impliedVolatilityMid"] = round(option.implied_volatility_mid, 4)
    
    if option.implied_volatility_ask is not None:
        response["impliedVolatilityAsk"] = round(option.implied_volatility_ask, 4)
    
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