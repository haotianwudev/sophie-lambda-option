"""
Utility functions for financial calculations in options analytics.
"""
from typing import Union, Dict, Any, Optional, List, Tuple
import math
import logging

logger = logging.getLogger(__name__)


def calculate_percentage_change(current_value: float, previous_value: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        current_value: Current value
        previous_value: Previous value
        
    Returns:
        Percentage change as float, rounded to 2 decimal places
    """
    if previous_value == 0:
        return 0.0
    
    percent_change = ((current_value - previous_value) / previous_value) * 100
    return round(percent_change, 2)


def calculate_mid_price(bid: float, ask: float) -> float:
    """
    Calculate mid price from bid and ask prices.
    
    Args:
        bid: Bid price
        ask: Ask price
        
    Returns:
        Mid price as float
    """
    # Handle cases where bid or ask might be None or 0
    if bid is None or ask is None:
        return 0.0
    
    if bid <= 0 and ask <= 0:
        return 0.0
    
    if bid <= 0:
        return ask
    
    if ask <= 0:
        return bid
    
    return (bid + ask) / 2


def calculate_moneyness(strike_price: float, current_price: float) -> float:
    """
    Calculate moneyness as the ratio of strike price to current stock price.
    
    Args:
        strike_price: Option strike price
        current_price: Current stock price
        
    Returns:
        Moneyness as float, rounded to 3 decimal places
    """
    if current_price == 0:
        return 0.0
    
    moneyness = strike_price / current_price
    return round(moneyness, 3)


def is_within_moneyness_range(
    moneyness: float, 
    min_moneyness: float = 0.85, 
    max_moneyness: float = 1.15
) -> bool:
    """
    Check if moneyness is within specified range.
    
    Args:
        moneyness: Calculated moneyness value
        min_moneyness: Minimum moneyness threshold (default: 0.85)
        max_moneyness: Maximum moneyness threshold (default: 1.15)
        
    Returns:
        Boolean indicating if moneyness is within range
    """
    return min_moneyness <= moneyness <= max_moneyness


def filter_options_by_moneyness(
    options: List[Dict[str, Any]], 
    current_price: float,
    min_moneyness: float = 0.85, 
    max_moneyness: float = 1.15
) -> List[Dict[str, Any]]:
    """
    Filter options by moneyness range and add moneyness field.
    
    Args:
        options: List of option data dictionaries
        current_price: Current stock price
        min_moneyness: Minimum moneyness threshold (default: 0.85)
        max_moneyness: Maximum moneyness threshold (default: 1.15)
        
    Returns:
        Filtered list of options with moneyness field added
    """
    filtered_options = []
    
    for option in options:
        if 'strike' not in option:
            continue
            
        moneyness = calculate_moneyness(option['strike'], current_price)
        option['moneyness'] = moneyness
        
        if is_within_moneyness_range(moneyness, min_moneyness, max_moneyness):
            filtered_options.append(option)
    
    return filtered_options


def safe_float_conversion(value: Any) -> float:
    """
    Safely convert a value to float.
    
    Args:
        value: Value to convert
        
    Returns:
        Float value or 0.0 if conversion fails
    """
    if value is None:
        return 0.0
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def calculate_implied_volatilities(
    option: Dict[str, Any],
    current_price: float,
    time_to_expiration: float,
    risk_free_rate: float,
    option_type: str
) -> Dict[str, Optional[float]]:
    """
    Calculate implied volatilities based on bid, mid, and ask prices.
    
    Uses py_vollib to calculate implied volatility for different price points.
    
    Args:
        option: Option data dictionary
        current_price: Current stock price
        time_to_expiration: Time to expiration in years
        risk_free_rate: Risk-free interest rate
        option_type: Option type ('c' for call, 'p' for put)
        
    Returns:
        Dictionary with implied volatility values
    """
    from py_vollib.black_scholes.implied_volatility import implied_volatility
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get bid and ask prices
    bid = safe_float_conversion(option.get('bid', 0))
    ask = safe_float_conversion(option.get('ask', 0))
    
    # Calculate mid price
    mid_price = calculate_mid_price(bid, ask)
    
    # Store the original implied volatility from yfinance
    iv_yf = safe_float_conversion(option.get('impliedVolatility', 0))
    
    # Initialize results dictionary
    iv_results = {
        'impliedVolatilityYF': iv_yf,
        'impliedVolatilityBid': None,
        'impliedVolatilityMid': None,
        'impliedVolatilityAsk': None
    }
    
    # Get strike price
    strike = safe_float_conversion(option.get('strike', 0))
    
    # Validate inputs
    if strike <= 0 or current_price <= 0 or time_to_expiration <= 0:
        logger.warning(f"Invalid inputs for IV calculation: strike={strike}, price={current_price}, time={time_to_expiration}")
        return iv_results
    
    # Calculate IV based on bid price
    if bid > 0:
        try:
            iv_bid = implied_volatility(
                price=bid,
                S=current_price,
                K=strike,
                t=time_to_expiration,
                r=risk_free_rate,
                flag=option_type
            )
            
            # Validate result
            if iv_bid is not None and 0 < iv_bid < 5.0:  # Cap at 500% volatility
                iv_results['impliedVolatilityBid'] = round(iv_bid, 4)
        except Exception as e:
            logger.warning(f"Failed to calculate bid IV: {e}")
    
    # Calculate IV based on mid price
    if mid_price > 0:
        try:
            iv_mid = implied_volatility(
                price=mid_price,
                S=current_price,
                K=strike,
                t=time_to_expiration,
                r=risk_free_rate,
                flag=option_type
            )
            
            # Validate result
            if iv_mid is not None and 0 < iv_mid < 5.0:
                iv_results['impliedVolatilityMid'] = round(iv_mid, 4)
        except Exception as e:
            logger.warning(f"Failed to calculate mid IV: {e}")
    
    # Calculate IV based on ask price
    if ask > 0:
        try:
            iv_ask = implied_volatility(
                price=ask,
                S=current_price,
                K=strike,
                t=time_to_expiration,
                r=risk_free_rate,
                flag=option_type
            )
            
            # Validate result
            if iv_ask is not None and 0 < iv_ask < 5.0:
                iv_results['impliedVolatilityAsk'] = round(iv_ask, 4)
        except Exception as e:
            logger.warning(f"Failed to calculate ask IV: {e}")
    
    return iv_results