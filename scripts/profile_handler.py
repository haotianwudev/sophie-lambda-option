"""
Script to profile the handler function and identify performance bottlenecks.
"""
import cProfile
import pstats
import io
import json
import time
import sys
from contextlib import contextmanager
import unittest.mock as mock

# Add parent directory to path to import handler
sys.path.append('.')

from handler import get_options_analytics
from tests.mock_data import get_mock_api_response, get_mock_raw_market_data, get_mock_raw_yfinance_option_data
from src.services.market_data_fetcher import MarketDataFetcher
from src.services.options_data_fetcher import OptionsDataFetcher

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
            'ticker': '^SPX'
        },
        'headers': {},
        'requestContext': {
            'requestId': 'test-request-id'
        }
    }

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
            mock_market_data.return_value = {
                'stock': get_mock_raw_market_data()['SPY']['info'],
                'vix': get_mock_raw_market_data()['^VIX']['info']
            }
            
            # Create mock expiration data from the mock option data
            from src.models.option_data import ExpirationData, OptionData
            mock_option_chain = get_mock_raw_yfinance_option_data()
            expiration_data_list = []
            
            for exp_date in mock_option_chain['expirationDates']:
                calls = []
                puts = []
                
                # Process calls
                for call_data in mock_option_chain['options'][exp_date]['calls']:
                    call = OptionData(
                        strike=call_data['strike'],
                        last_price=call_data['lastPrice'],
                        implied_volatility=call_data['impliedVolatility'],
                        delta=call_data.get('delta'),
                        option_type='c',
                        contract_symbol=call_data.get('contractSymbol'),
                        last_trade_date=call_data.get('lastTradeDate'),
                        bid=call_data.get('bid'),
                        ask=call_data.get('ask'),
                        volume=call_data.get('volume'),
                        open_interest=call_data.get('openInterest')
                    )
                    calls.append(call)
                
                # Process puts
                for put_data in mock_option_chain['options'][exp_date]['puts']:
                    put = OptionData(
                        strike=put_data['strike'],
                        last_price=put_data['lastPrice'],
                        implied_volatility=put_data['impliedVolatility'],
                        delta=put_data.get('delta'),
                        option_type='p',
                        contract_symbol=put_data.get('contractSymbol'),
                        last_trade_date=put_data.get('lastTradeDate'),
                        bid=put_data.get('bid'),
                        ask=put_data.get('ask'),
                        volume=put_data.get('volume'),
                        open_interest=put_data.get('openInterest')
                    )
                    puts.append(put)
                
                expiration_data = ExpirationData(
                    expiration=exp_date,
                    calls=calls,
                    puts=puts
                )
                expiration_data_list.append(expiration_data)
            
            mock_options_data.return_value = expiration_data_list
            
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
    
    # Create mock data once to reuse across iterations
    mock_market_data_value = {
        'stock': get_mock_raw_market_data()['SPY']['info'],
        'vix': get_mock_raw_market_data()['^VIX']['info']
    }
    
    # Create mock expiration data from the mock option data
    from src.models.option_data import ExpirationData, OptionData
    mock_option_chain = get_mock_raw_yfinance_option_data()
    expiration_data_list = []
    
    for exp_date in mock_option_chain['expirationDates']:
        calls = []
        puts = []
        
        # Process calls
        for call_data in mock_option_chain['options'][exp_date]['calls']:
            call = OptionData(
                strike=call_data['strike'],
                last_price=call_data['lastPrice'],
                implied_volatility=call_data['impliedVolatility'],
                delta=call_data.get('delta'),
                option_type='c',
                contract_symbol=call_data.get('contractSymbol'),
                last_trade_date=call_data.get('lastTradeDate'),
                bid=call_data.get('bid'),
                ask=call_data.get('ask'),
                volume=call_data.get('volume'),
                open_interest=call_data.get('openInterest')
            )
            calls.append(call)
        
        # Process puts
        for put_data in mock_option_chain['options'][exp_date]['puts']:
            put = OptionData(
                strike=put_data['strike'],
                last_price=put_data['lastPrice'],
                implied_volatility=put_data['impliedVolatility'],
                delta=put_data.get('delta'),
                option_type='p',
                contract_symbol=put_data.get('contractSymbol'),
                last_trade_date=put_data.get('lastTradeDate'),
                bid=put_data.get('bid'),
                ask=put_data.get('ask'),
                volume=put_data.get('volume'),
                open_interest=put_data.get('openInterest')
            )
            puts.append(put)
        
        expiration_data = ExpirationData(
            expiration=exp_date,
            calls=calls,
            puts=puts
        )
        expiration_data_list.append(expiration_data)
    
    times = []
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}...")
        
        # Mock the external service calls
        with mock.patch.object(MarketDataFetcher, 'fetch_enhanced_market_data') as mock_market_data:
            with mock.patch.object(OptionsDataFetcher, 'fetch_filtered_option_chains') as mock_options_data:
                # Set up mock return values
                mock_market_data.return_value = mock_market_data_value
                mock_options_data.return_value = expiration_data_list
                
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