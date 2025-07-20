"""
Script to test the optimized handler with different input sizes.
"""
import sys
import time
import json
import unittest.mock as mock
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

# Add parent directory to path to import handlers
sys.path.append('.')

# Import optimized handler
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


def create_mock_option_data(num_expirations=4, num_strikes=7):
    """
    Create mock option data with variable size.
    
    Args:
        num_expirations: Number of expiration dates
        num_strikes: Number of strike prices per expiration
        
    Returns:
        List of ExpirationData objects
    """
    # Create expiration dates
    base_date = datetime(2025, 7, 18, tzinfo=timezone.utc)
    expiration_dates = []
    
    for i in range(num_expirations):
        # Add 7 days for each expiration
        exp_date = base_date + timedelta(days=(i+1)*7)
        expiration_dates.append(exp_date.strftime("%Y-%m-%d"))
    
    # Current stock price
    current_price = 627.58
    
    # Create strikes around current price
    strikes = []
    strike_range = 0.3  # Range from 0.85 to 1.15
    for i in range(num_strikes):
        moneyness = 0.85 + (strike_range * i / (num_strikes - 1))
        strike = round(current_price * moneyness)
        strikes.append(strike)
    
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


def test_with_input_size(num_expirations, num_strikes, iterations=3):
    """
    Test the optimized handler with a specific input size.
    
    Args:
        num_expirations: Number of expiration dates
        num_strikes: Number of strike prices per expiration
        iterations: Number of iterations to run
        
    Returns:
        Tuple of (average_time, min_time, max_time)
    """
    event = create_mock_event()
    context = {}
    
    # Create mock data
    mock_market_data_value = create_mock_market_data()
    mock_options_data_value = create_mock_option_data(num_expirations, num_strikes)
    
    total_options = num_expirations * num_strikes * 2  # Both calls and puts
    
    print(f"Testing with {num_expirations} expirations, {num_strikes} strikes ({total_options} total options)")
    
    times = []
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...")
        
        # Mock the external service calls
        with mock.patch.object(MarketDataFetcher, 'fetch_enhanced_market_data') as mock_market_data:
            with mock.patch.object(OptionsDataFetcher, 'fetch_filtered_option_chains') as mock_options_data:
                # Set up mock return values
                mock_market_data.return_value = mock_market_data_value
                mock_options_data.return_value = mock_options_data_value
                
                # Measure execution time
                start_time = time.time()
                response = optimized_handler.get_options_analytics(event, context)
                end_time = time.time()
                execution_time = end_time - start_time
                times.append(execution_time)
                print(f"  Execution time: {execution_time:.4f} seconds")
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"  Average: {avg_time:.4f}s, Min: {min_time:.4f}s, Max: {max_time:.4f}s")
    print()
    
    return avg_time, min_time, max_time, total_options


def run_input_size_tests():
    """Run tests with different input sizes."""
    print("Testing optimized handler with different input sizes...")
    print("=" * 50)
    
    results = []
    
    # Test with different combinations of expirations and strikes
    test_configs = [
        (4, 7),    # Small: 4 expirations, 7 strikes (56 options)
        (8, 10),   # Medium: 8 expirations, 10 strikes (160 options)
        (12, 15),  # Large: 12 expirations, 15 strikes (360 options)
        (16, 20)   # Extra Large: 16 expirations, 20 strikes (640 options)
    ]
    
    for exps, strikes in test_configs:
        avg_time, min_time, max_time, total_options = test_with_input_size(exps, strikes)
        results.append((exps, strikes, total_options, avg_time))
    
    print("\nSummary:")
    print("=" * 50)
    print("Expirations | Strikes | Total Options | Avg Time (s)")
    print("-" * 50)
    
    for exps, strikes, total_options, avg_time in results:
        print(f"{exps:11d} | {strikes:7d} | {total_options:12d} | {avg_time:.4f}")


if __name__ == "__main__":
    run_input_size_tests()