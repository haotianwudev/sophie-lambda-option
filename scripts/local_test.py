#!/usr/bin/env python3
"""
Local testing script for Options Analytics API.
Provides local testing capabilities with sample data and mock responses.
"""

import json
import sys
import os
import time
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from handler import get_options_analytics


class SampleDataGenerator:
    """Generate realistic sample data for testing."""
    
    @staticmethod
    def generate_sample_market_data(ticker: str = "SPY") -> Dict[str, Any]:
        """Generate sample market data."""
        return {
            'stock_price': 450.25 if ticker == "SPY" else 180.50,
            'vix_value': 18.75,
            'stock_timestamp': datetime.now(),
            'vix_timestamp': datetime.now()
        }
    
    @staticmethod
    def generate_sample_options_data(ticker: str = "SPY") -> list:
        """Generate sample options data with multiple expiration dates."""
        base_price = 450.25 if ticker == "SPY" else 180.50
        
        # Generate 3 expiration dates
        exp_dates = []
        for i in range(3):
            exp_date = datetime.now() + timedelta(days=7 + i*7)
            exp_dates.append(exp_date.strftime("%Y-%m-%d"))
        
        expiration_data = []
        
        for exp_date in exp_dates:
            # Generate strikes around current price
            strikes = []
            for i in range(-5, 6):  # 11 strikes total
                strike = base_price + (i * 5)  # $5 intervals
                strikes.append(strike)
            
            calls = []
            puts = []
            
            for strike in strikes:
                # Generate realistic option prices
                moneyness = strike / base_price
                
                # Calls
                if moneyness < 1.0:  # ITM calls
                    call_price = max(base_price - strike + 2.0, 0.5)
                else:  # OTM calls
                    call_price = max(5.0 - (moneyness - 1.0) * 20, 0.1)
                
                calls.append({
                    'strike': strike,
                    'last_price': round(call_price, 2),
                    'option_type': 'c'
                })
                
                # Puts
                if moneyness > 1.0:  # ITM puts
                    put_price = max(strike - base_price + 2.0, 0.5)
                else:  # OTM puts
                    put_price = max(5.0 - (1.0 - moneyness) * 20, 0.1)
                
                puts.append({
                    'strike': strike,
                    'last_price': round(put_price, 2),
                    'option_type': 'p'
                })
            
            # Create mock ExpirationData object
            exp_data = MagicMock()
            exp_data.expiration = exp_date
            exp_data.calls = [MagicMock(**call) for call in calls]
            exp_data.puts = [MagicMock(**put) for put in puts]
            
            expiration_data.append(exp_data)
        
        return expiration_data


class LocalTester:
    """Local testing framework for the Options Analytics API."""
    
    def __init__(self, use_sample_data: bool = True):
        self.use_sample_data = use_sample_data
        self.sample_generator = SampleDataGenerator()
    
    def create_test_event(self, ticker: Optional[str] = None, 
                         additional_params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a test API Gateway event."""
        query_params = {}
        
        if ticker:
            query_params['ticker'] = ticker
        
        if additional_params:
            query_params.update(additional_params)
        
        return {
            'httpMethod': 'GET',
            'path': '/options-analytics',
            'queryStringParameters': query_params if query_params else None,
            'headers': {
                'Content-Type': 'application/json',
                'User-Agent': 'LocalTester/1.0'
            },
            'requestContext': {
                'requestId': f'test-{int(time.time())}',
                'stage': 'test',
                'httpMethod': 'GET'
            }
        }
    
    def create_test_context(self) -> MagicMock:
        """Create a test Lambda context."""
        context = MagicMock()
        context.function_name = 'options-analytics-test'
        context.function_version = '1'
        context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:options-analytics-test'
        context.memory_limit_in_mb = 512
        context.remaining_time_in_millis = lambda: 30000
        context.aws_request_id = f'test-{int(time.time())}'
        return context
    
    def mock_market_data_fetcher(self, ticker: str):
        """Mock the MarketDataFetcher for testing."""
        sample_data = self.sample_generator.generate_sample_market_data(ticker)
        
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_market_data.return_value = (
            sample_data['stock_price'],
            sample_data['vix_value'],
            sample_data['stock_timestamp'],
            sample_data['vix_timestamp']
        )
        return mock_fetcher
    
    def mock_options_data_fetcher(self, ticker: str):
        """Mock the OptionsDataFetcher for testing."""
        sample_data = self.sample_generator.generate_sample_options_data(ticker)
        
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all_option_chains.return_value = sample_data
        return mock_fetcher
    
    def run_test(self, ticker: str = "SPY", verbose: bool = True) -> Dict[str, Any]:
        """Run a single test with the specified ticker."""
        print(f"\n{'='*50}")
        print(f"Testing Options Analytics API - Ticker: {ticker}")
        print(f"{'='*50}")
        
        # Create test event and context
        event = self.create_test_event(ticker)
        context = self.create_test_context()
        
        if verbose:
            print(f"📋 Test Event:")
            print(json.dumps(event, indent=2, default=str))
        
        start_time = time.time()
        
        if self.use_sample_data:
            # Mock external dependencies
            with patch('handler.MarketDataFetcher') as mock_market_class, \
                 patch('handler.OptionsDataFetcher') as mock_options_class:
                
                # Set up mocks
                mock_market_class.return_value = self.mock_market_data_fetcher(ticker)
                mock_options_class.return_value = self.mock_options_data_fetcher(ticker)
                
                # Run the handler
                response = get_options_analytics(event, context)
        else:
            # Run with real data (requires internet connection)
            print("⚠️  Using real data - requires internet connection")
            response = get_options_analytics(event, context)
        
        execution_time = time.time() - start_time
        
        # Parse and validate response
        status_code = response.get('statusCode', 0)
        headers = response.get('headers', {})
        body = response.get('body', '{}')
        
        try:
            parsed_body = json.loads(body)
        except json.JSONDecodeError:
            parsed_body = {'error': 'Invalid JSON response'}
        
        # Print results
        print(f"\n📊 Test Results:")
        print(f"Status Code: {status_code}")
        print(f"Execution Time: {execution_time:.3f}s")
        print(f"Response Size: {len(body)} bytes")
        
        if verbose:
            print(f"\n📋 Response Headers:")
            for key, value in headers.items():
                print(f"  {key}: {value}")
        
        if status_code == 200:
            print(f"\n✅ SUCCESS - API returned valid response")
            
            # Validate response structure
            required_fields = ['ticker', 'stockPrice', 'vixValue', 'dataTimestamp', 'expirationDates']
            missing_fields = [field for field in required_fields if field not in parsed_body]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
            else:
                print(f"✅ All required fields present")
                
                # Print summary statistics
                exp_dates = parsed_body.get('expirationDates', [])
                total_calls = sum(len(exp.get('calls', [])) for exp in exp_dates)
                total_puts = sum(len(exp.get('puts', [])) for exp in exp_dates)
                
                print(f"\n📈 Data Summary:")
                print(f"  Ticker: {parsed_body.get('ticker')}")
                print(f"  Stock Price: ${parsed_body.get('stockPrice')}")
                print(f"  VIX Value: {parsed_body.get('vixValue')}")
                print(f"  Expiration Dates: {len(exp_dates)}")
                print(f"  Total Calls: {total_calls}")
                print(f"  Total Puts: {total_puts}")
                print(f"  Total Options: {total_calls + total_puts}")
        else:
            print(f"\n❌ ERROR - API returned error response")
            if 'error' in parsed_body:
                print(f"Error: {parsed_body['error']}")
                print(f"Error Type: {parsed_body.get('errorType', 'Unknown')}")
        
        if verbose and status_code == 200:
            print(f"\n📋 Sample Response Data:")
            # Show first expiration date with limited options
            if exp_dates:
                first_exp = exp_dates[0]
                sample_exp = {
                    'expiration': first_exp.get('expiration'),
                    'calls': first_exp.get('calls', [])[:3],  # First 3 calls
                    'puts': first_exp.get('puts', [])[:3]     # First 3 puts
                }
                print(json.dumps(sample_exp, indent=2))
        
        return {
            'status_code': status_code,
            'execution_time': execution_time,
            'response_size': len(body),
            'success': status_code == 200,
            'response': response
        }
    
    def run_test_suite(self, tickers: list = None, verbose: bool = False) -> Dict[str, Any]:
        """Run a comprehensive test suite."""
        if tickers is None:
            tickers = ["SPY", "AAPL", "MSFT", "INVALID_TICKER"]
        
        print(f"\n🧪 Running Options Analytics API Test Suite")
        print(f"Testing {len(tickers)} tickers: {', '.join(tickers)}")
        print(f"Using sample data: {self.use_sample_data}")
        
        results = {}
        total_start_time = time.time()
        
        for ticker in tickers:
            try:
                result = self.run_test(ticker, verbose=verbose)
                results[ticker] = result
            except Exception as e:
                print(f"\n❌ Test failed for {ticker}: {str(e)}")
                results[ticker] = {
                    'status_code': 500,
                    'execution_time': 0,
                    'response_size': 0,
                    'success': False,
                    'error': str(e)
                }
        
        total_time = time.time() - total_start_time
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"TEST SUITE SUMMARY")
        print(f"{'='*60}")
        
        successful_tests = sum(1 for r in results.values() if r.get('success', False))
        total_tests = len(results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"Total Execution Time: {total_time:.3f}s")
        
        # Performance summary
        successful_times = [r['execution_time'] for r in results.values() if r.get('success', False)]
        if successful_times:
            avg_time = sum(successful_times) / len(successful_times)
            max_time = max(successful_times)
            min_time = min(successful_times)
            
            print(f"\nPerformance Summary (successful tests):")
            print(f"  Average: {avg_time:.3f}s")
            print(f"  Minimum: {min_time:.3f}s")
            print(f"  Maximum: {max_time:.3f}s")
        
        # Individual results
        print(f"\nIndividual Results:")
        for ticker, result in results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            time_str = f"{result['execution_time']:.3f}s" if result['execution_time'] > 0 else "N/A"
            print(f"  {ticker:12} {status} ({time_str})")
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'total_time': total_time,
            'results': results
        }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Local testing for Options Analytics API')
    parser.add_argument('--ticker', '-t', default='SPY', help='Ticker symbol to test (default: SPY)')
    parser.add_argument('--real-data', '-r', action='store_true', help='Use real data instead of sample data')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--suite', '-s', action='store_true', help='Run full test suite')
    parser.add_argument('--tickers', nargs='+', help='List of tickers for test suite')
    
    args = parser.parse_args()
    
    # Create tester
    tester = LocalTester(use_sample_data=not args.real_data)
    
    if args.suite:
        # Run test suite
        tickers = args.tickers if args.tickers else ["SPY", "AAPL", "MSFT"]
        results = tester.run_test_suite(tickers=tickers, verbose=args.verbose)
        
        # Exit with error code if any tests failed
        if results['successful_tests'] < results['total_tests']:
            sys.exit(1)
    else:
        # Run single test
        result = tester.run_test(ticker=args.ticker, verbose=args.verbose)
        
        # Exit with error code if test failed
        if not result['success']:
            sys.exit(1)


if __name__ == '__main__':
    main()