"""
Mock data for testing options data API.
"""
from datetime import datetime, timezone, timedelta


def get_mock_stock_data():
    """
    Get mock stock data for testing.
    
    Returns:
        Dictionary with mock stock data
    """
    return {
        "price": 627.58,
        "previousClose": 625.12,
        "percentChange": 0.39,
        "timestamp": "2025-07-18T20:17:06.058378Z"
    }


def get_mock_vix_data():
    """
    Get mock VIX data for testing.
    
    Returns:
        Dictionary with mock VIX data
    """
    return {
        "value": 16.41,
        "previousClose": 16.85,
        "percentChange": -2.61,
        "timestamp": "2025-07-18T20:17:06.224920Z"
    }


def get_mock_expiration_dates():
    """
    Get mock expiration dates for testing.
    
    Returns:
        List of expiration dates as strings
    """
    return [
        "2025-07-25",  # 1 week
        "2025-08-01",  # 2 weeks
        "2025-08-15",  # ~4 weeks
        "2025-09-05",  # ~7 weeks
        "2025-09-19"   # ~9 weeks
    ]


def get_mock_option_chain(current_price=627.58):
    """
    Get mock option chain data for testing.
    
    Args:
        current_price: Current stock price to use for moneyness calculation
        
    Returns:
        Dictionary with calls and puts for each expiration date
    """
    # Base strike prices around current price
    base_strikes = [
        current_price * 0.80,  # Deep ITM for calls, Deep OTM for puts
        current_price * 0.85,  # ITM for calls, OTM for puts
        current_price * 0.90,  # ITM for calls, OTM for puts
        current_price * 0.95,  # ITM for calls, OTM for puts
        current_price * 1.00,  # ATM
        current_price * 1.05,  # OTM for calls, ITM for puts
        current_price * 1.10,  # OTM for calls, ITM for puts
        current_price * 1.15,  # OTM for calls, ITM for puts
        current_price * 1.20   # Deep OTM for calls, Deep ITM for puts
    ]
    
    # Round strikes to nearest 5
    strikes = [round(strike / 5) * 5 for strike in base_strikes]
    
    # Get expiration dates
    expirations = get_mock_expiration_dates()
    
    # Current date for calculations
    current_date = datetime.now(timezone.utc)
    
    option_chain = {}
    
    for exp_date_str in expirations:
        exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_to_exp = (exp_date - current_date).days
        time_to_exp_years = days_to_exp / 365.25
        
        # Base IV that increases with time to expiration
        base_iv = 0.15 + (time_to_exp_years * 0.05)
        
        calls = []
        puts = []
        
        for strike in strikes:
            # Calculate moneyness
            moneyness = strike / current_price
            
            # IV smile effect - higher IV for OTM options
            iv_adjustment = abs(moneyness - 1.0) * 0.2
            iv = base_iv + iv_adjustment
            
            # Last trade date (random time on current day)
            last_trade_hour = 9 + (strike % 7)  # Between 9 and 15
            last_trade_date = current_date.replace(
                hour=last_trade_hour, 
                minute=30, 
                second=0, 
                microsecond=0
            )
            last_trade_date_str = last_trade_date.isoformat().replace('+00:00', 'Z')
            
            # Contract symbols
            call_symbol = f"SPY{exp_date_str.replace('-', '')}C{int(strike):08d}"
            put_symbol = f"SPY{exp_date_str.replace('-', '')}P{int(strike):08d}"
            
            # Call option pricing
            call_intrinsic = max(0, current_price - strike)
            call_time_value = current_price * iv * time_to_exp_years
            call_theo = call_intrinsic + call_time_value
            
            call_bid = round(call_theo * 0.95, 2)
            call_ask = round(call_theo * 1.05, 2)
            call_last = round((call_bid + call_ask) / 2, 2)
            
            # Put option pricing
            put_intrinsic = max(0, strike - current_price)
            put_time_value = current_price * iv * time_to_exp_years
            put_theo = put_intrinsic + put_time_value
            
            put_bid = round(put_theo * 0.95, 2)
            put_ask = round(put_theo * 1.05, 2)
            put_last = round((put_bid + put_ask) / 2, 2)
            
            # Volume and open interest - higher for strikes closer to ATM
            volume_factor = max(0.1, 1 - abs(moneyness - 1.0) * 2)
            base_volume = int(1000 * volume_factor)
            base_oi = int(5000 * volume_factor)
            
            # Call option
            call = {
                "contractSymbol": call_symbol,
                "strike": strike,
                "lastPrice": call_last,
                "bid": call_bid,
                "ask": call_ask,
                "lastTradeDate": last_trade_date_str,
                "volume": base_volume + (strike % 100),
                "openInterest": base_oi + (strike % 500),
                "impliedVolatility": round(iv, 3),
                "inTheMoney": strike < current_price,
                "delta": round(max(0, min(1, 0.5 + (current_price - strike) / (current_price * 0.2))), 2)
            }
            calls.append(call)
            
            # Put option
            put = {
                "contractSymbol": put_symbol,
                "strike": strike,
                "lastPrice": put_last,
                "bid": put_bid,
                "ask": put_ask,
                "lastTradeDate": last_trade_date_str,
                "volume": base_volume - (strike % 50),
                "openInterest": base_oi - (strike % 250),
                "impliedVolatility": round(iv, 3),
                "inTheMoney": strike > current_price,
                "delta": round(max(-1, min(0, -0.5 + (current_price - strike) / (current_price * 0.2))), 2)
            }
            puts.append(put)
        
        option_chain[exp_date_str] = {
            "calls": calls,
            "puts": puts
        }
    
    return option_chain


def get_mock_api_response():
    """
    Get complete mock API response for testing.
    
    Returns:
        Dictionary with complete mock API response
    """
    stock_data = get_mock_stock_data()
    vix_data = get_mock_vix_data()
    option_chain = get_mock_option_chain(stock_data["price"])
    
    # Get expiration dates with labels
    current_date = datetime.now(timezone.utc)
    target_periods = {
        "2w": 14,  # 2 weeks in days
        "1m": 30,  # 1 month in days
        "6w": 42,  # 6 weeks in days
        "2m": 60   # 2 months in days
    }
    
    expirations = get_mock_expiration_dates()
    labeled_expirations = []
    
    for label, days in target_periods.items():
        target_date = current_date + timedelta(days=days)
        closest_exp = min(expirations, key=lambda x: 
            abs((datetime.strptime(x, "%Y-%m-%d").replace(tzinfo=timezone.utc) - target_date).days))
        
        exp_date = datetime.strptime(closest_exp, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_to_exp = (exp_date - current_date).days
        
        labeled_expirations.append({
            "expiration": closest_exp,
            "daysToExpiration": days_to_exp,
            "expirationLabel": label,
            "calls": option_chain[closest_exp]["calls"],
            "puts": option_chain[closest_exp]["puts"]
        })
    
    return {
        "ticker": "SPY",
        "stock": stock_data,
        "vix": vix_data,
        "expirationDates": labeled_expirations
    }


def get_mock_raw_yfinance_option_data():
    """
    Get mock raw yfinance option data for testing.
    
    Returns:
        Dictionary with raw yfinance option data
    """
    # This simulates the raw data structure from yfinance
    current_price = 627.58
    option_chain = get_mock_option_chain(current_price)
    
    # Convert to yfinance format
    yf_data = {}
    
    for exp_date, data in option_chain.items():
        yf_data[exp_date] = {
            "calls": data["calls"],
            "puts": data["puts"]
        }
    
    return {
        "underlyingSymbol": "SPY",
        "expirationDates": list(yf_data.keys()),
        "strikes": sorted(set([opt["strike"] for opts in yf_data.values() for opt in opts["calls"]])),
        "options": yf_data
    }


def get_mock_raw_market_data():
    """
    Get mock raw market data for testing.
    
    Returns:
        Dictionary with raw market data
    """
    stock_data = get_mock_stock_data()
    vix_data = get_mock_vix_data()
    
    return {
        "SPY": {
            "info": {
                "regularMarketPrice": stock_data["price"],
                "previousClose": stock_data["previousClose"]
            },
            "history": {
                "Close": [stock_data["previousClose"], stock_data["price"]]
            }
        },
        "^VIX": {
            "info": {
                "regularMarketPrice": vix_data["value"],
                "previousClose": vix_data["previousClose"]
            },
            "history": {
                "Close": [vix_data["previousClose"], vix_data["value"]]
            }
        }
    }