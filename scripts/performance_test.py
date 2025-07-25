"""
Script to compare the performance of the original and optimized handlers.
"""
import sys
import time
import json
import unittest.mock as mock
from datetime import datetime, timezone
from contextlib import contextmanager

# Add parent directory to path to import handlers
sys.path.append('.')

# Import both handlers
import handler
import optimized_handler
from src.services.market_data_fetcher import MarketDataFetcher
from src.services.options_data_fetcher import OptionsDataFetcher
from src.models.option_data import ExpirationData, OptionData


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


def test_handler_performance(handler_module, iterations=5):
    """
    Test the performance of a handler function.
    
    Args:
        handler_module: The handler module to test
        iterations: Number of iterations to run
        
    Returns:
        Tuple of (average_time, min_time, max_time)
    """
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
                response = handler_module.get_options_analytics(event, context)
                end_time = time.time()
                execution_time = end_time - start_time
                times.append(execution_time)
                print(f"Execution time: {execution_time:.4f} seconds")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return avg_time, min_time, max_time


def compare_handlers():
    """Compare the performance of the original and optimized handlers."""
    print("Testing original handler performance...")
    print("-" * 50)
    orig_avg, orig_min, orig_max = test_handler_performance(handler, iterations=3)
    
    print("\nTesting optimized handler performance...")
    print("-" * 50)
    opt_avg, opt_min, opt_max = test_handler_performance(optimized_handler, iterations=3)
    
    print("\nPerformance Comparison:")
    print("=" * 50)
    print(f"Original Handler: Avg: {orig_avg:.4f}s, Min: {orig_min:.4f}s, Max: {orig_max:.4f}s")
    print(f"Optimized Handler: Avg: {opt_avg:.4f}s, Min: {opt_min:.4f}s, Max: {opt_max:.4f}s")
    
    improvement = ((orig_avg - opt_avg) / orig_avg) * 100
    print(f"Performance Improvement: {improvement:.2f}%")


if __name__ == "__main__":
    compare_handlers()