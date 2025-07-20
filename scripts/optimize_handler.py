"""
Script to optimize the handler function for Lambda environment.
"""
import cProfile
import pstats
import io
import json
import time
import sys
from datetime import datetime, timezone
from contextlib import contextmanager
import unittest.mock as mock

# Add parent directory to path to import handler
sys.path.append('.')

from handler import get_options_analytics
from src.services.market_data_fetcher import MarketDataFetcher
from src.services.options_data_fetcher import OptionsDataFetcher
from src.models.option_data import ExpirationData, OptionData

@contextmanager
def profile_code(sort_by='cumulative', lines=20):
    """Context manager for profiling code blocks."""
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
    ps.print_stats(lines)
    print(s.getvalue())

def create_mock_event():
    """Create a mock API Gateway event."""
    return {
        'httpMethod': 'GET',
        'path': '/options-analytics',
        'queryStringParameters': {
            'ticker': 'SPY'
        },
        'headers': {},
        'requestContext': {
            'requestId': 'test-request-id'
        }
    }

def create_mock_market_data():
    """Create mock market data."""
    return {
        'stock': {
            'price': 627.58,
            'previousClose': 625.12,
            'percentChange': 0.39,
            'timestamp': datetime.now(timezone.utc).isoformat()
        },
        'vix': {
            'value': 16.41,
            'previousClose': 16.85,
            'percentChange': -2.61,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    }

def create_mock_option_data():
    """Create mock option data."""
    # Create expiration dates
    expiration_dates = [
        "2025-07-25",  # 1 week
        "2025-08-01",  # 2 weeks
        "2025-08-15",  # ~4 weeks
        "2025-09-05"   # ~7 weeks
    ]
    
    # Current stock price
    current_price = 627.58
    
    # Create strikes around current price
    strikes = [
        round(current_price * 0.85),  # 533
        round(current_price * 0.90),  # 565
        round(current_price * 0.95),  # 596
        round(current_price * 1.00),  # 628
        round(current_price * 1.05),  # 659
        round(current_price * 1.10),  # 690
        round(current_price * 1.15)   # 722
    ]
    
    expiration_data_list = []
    
    for exp_date in expiration_dates:
        calls = []
        puts = []
        
        for strike in strikes:
            # Create call option
            call = OptionData(
                strike=strike,
                last_price=max(0.01, current_price - strike + 5),
                implied_volatility=0.2,
                delta=0.5,
                option_type='c',
                contract_symbol=f"SPY{exp_date.replace('-', '')}C{strike:08d}",
                last_trade_date=datetime.now(timezone.utc).isoformat(),
                bid=max(0.01, current_price - strike),
                ask=max(0.01, current_price - strike + 10),
                volume=1000,
                open_interest=5000
            )
            calls.append(call)
            
            # Create put option
            put = OptionData(
                strike=strike,
                last_price=max(0.01, strike - current_price + 5),
                implied_volatility=0.2,
                delta=-0.5,
                option_type='p',
                contract_symbol=f"SPY{exp_date.replace('-', '')}P{strike:08d}",
                last_trade_date=datetime.now(timezone.utc).isoformat(),
                bid=max(0.01, strike - current_price),
                ask=max(0.01, strike - current_price + 10),
                volume=1000,
                open_interest=5000
            )
            puts.append(put)
        
        expiration_data = ExpirationData(
            expiration=exp_date,
            calls=calls,
            puts=puts
        )
        expiration_data_list.append(expiration_data)
    
    return expiration_data_list

def profile_handler():
    """Profile the handler function with mock data."""
    # Create mock event
    event = create_mock_event()
    
    # Mock context
    context = {}
    
    # Mock the external service calls
    with mock.patch.object(MarketDataFetcher, 'fetch_enhanced_market_data') as mock_market_data:
        with mock.patch.object(OptionsDataFetcher, 'fetch_filtered_option_chains') as mock_options_data:
            # Set up mock return values
            mock_market_data.return_value = create_mock_market_data()
            mock_options_data.return_value = create_mock_option_data()
            
            # Profile the handler function
            print("Profiling handler function...")
            with profile_code(sort_by='cumulative', lines=30):
                response = get_options_analytics(event, context)
    
    # Print response status code
    response_body = json.loads(response['body'])
    print(f"Response status code: {response['statusCode']}")
    print(f"Response size: {len(response['body'])} bytes")
    
    # Print some statistics about the response
    expiration_dates = response_body.get('expirationDates', [])
    print(f"Number of expiration dates: {len(expiration_dates)}")
    
    total_options = 0
    for exp in expiration_dates:
        calls = len(exp.get('calls', []))
        puts = len(exp.get('puts', []))
        total_options += calls + puts
        print(f"Expiration {exp.get('expiration')}: {calls} calls, {puts} puts")
    
    print(f"Total options: {total_options}")

def measure_execution_time(iterations=5):
    """Measure execution time over multiple iterations."""
    event = create_mock_event()
    context = {}
    
    # Create mock data
    mock_market_data_value = create_mock_market_data()
    mock_options_data_value = create_mock_option_data()
    
    times = []
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}...")
        
        # Mock the external service calls
        with mock.patch.object(MarketDataFetcher, 'fetch_enhanced_market_data') as mock_market_data:
            with mock.patch.object(OptionsDataFetcher, 'fetch_filtered_option_chains') as mock_options_data:
                # Set up mock return values
                mock_market_data.return_value = mock_market_data_value
                mock_options_data.return_value = mock_options_data_value
                
                # Measure execution time
                start_time = time.time()
                response = get_options_analytics(event, context)
                end_time = time.time()
                execution_time = end_time - start_time
                times.append(execution_time)
                print(f"Execution time: {execution_time:.4f} seconds")
    
    avg_time = sum(times) / len(times)
    print(f"\nAverage execution time over {iterations} iterations: {avg_time:.4f} seconds")
    print(f"Min time: {min(times):.4f} seconds")
    print(f"Max time: {max(times):.4f} seconds")

if __name__ == "__main__":
    # Profile the handler function
    profile_handler()
    
    # Measure execution time
    print("\n" + "="*50)
    print("Measuring execution time...")
    measure_execution_time(iterations=3)