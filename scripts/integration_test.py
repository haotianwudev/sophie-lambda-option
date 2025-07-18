#!/usr/bin/env python3
"""
Integration testing script for deployed Options Analytics API.
Tests the actual deployed API endpoint with real HTTP requests.
"""

import json
import sys
import time
import requests
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlencode


class IntegrationTester:
    """Integration testing framework for deployed Options Analytics API."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the integration tester.
        
        Args:
            base_url: Base URL of the deployed API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'OptionsAnalytics-IntegrationTest/1.0',
            'Accept': 'application/json'
        })
    
    def make_request(self, ticker: Optional[str] = None, 
                    additional_params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make a request to the options analytics endpoint.
        
        Args:
            ticker: Ticker symbol to request
            additional_params: Additional query parameters
            
        Returns:
            Dictionary containing response data and metadata
        """
        # Build query parameters
        params = {}
        if ticker:
            params['ticker'] = ticker
        if additional_params:
            params.update(additional_params)
        
        # Build URL
        endpoint = '/options-analytics'
        url = urljoin(self.base_url, endpoint)
        
        if params:
            url += '?' + urlencode(params)
        
        print(f"🌐 Making request to: {url}")
        
        start_time = time.time()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            request_time = time.time() - start_time
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {'error': 'Invalid JSON response', 'raw_response': response.text}
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response_data,
                'request_time': request_time,
                'response_size': len(response.content),
                'url': url
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'status_code': 0,
                'error': 'Request timeout',
                'request_time': time.time() - start_time,
                'url': url
            }
        except requests.exceptions.ConnectionError as e:
            return {
                'success': False,
                'status_code': 0,
                'error': f'Connection error: {str(e)}',
                'request_time': time.time() - start_time,
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 0,
                'error': f'Unexpected error: {str(e)}',
                'request_time': time.time() - start_time,
                'url': url
            }
    
    def validate_response_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the structure of a successful API response.
        
        Args:
            data: Response data to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required top-level fields
        required_fields = ['ticker', 'stockPrice', 'vixValue', 'dataTimestamp', 'expirationDates']
        
        for field in required_fields:
            if field not in data:
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['valid'] = False
        
        # Validate data types
        if 'stockPrice' in data and not isinstance(data['stockPrice'], (int, float)):
            validation_results['errors'].append("stockPrice must be a number")
            validation_results['valid'] = False
        
        if 'vixValue' in data and not isinstance(data['vixValue'], (int, float)):
            validation_results['errors'].append("vixValue must be a number")
            validation_results['valid'] = False
        
        if 'expirationDates' in data:
            if not isinstance(data['expirationDates'], list):
                validation_results['errors'].append("expirationDates must be an array")
                validation_results['valid'] = False
            else:
                # Validate expiration date structure
                for i, exp_date in enumerate(data['expirationDates']):
                    if not isinstance(exp_date, dict):
                        validation_results['errors'].append(f"expirationDates[{i}] must be an object")
                        continue
                    
                    # Check required fields in expiration date
                    exp_required = ['expiration', 'calls', 'puts']
                    for field in exp_required:
                        if field not in exp_date:
                            validation_results['errors'].append(f"expirationDates[{i}] missing field: {field}")
                    
                    # Validate calls and puts arrays
                    for option_type in ['calls', 'puts']:
                        if option_type in exp_date:
                            if not isinstance(exp_date[option_type], list):
                                validation_results['errors'].append(f"expirationDates[{i}].{option_type} must be an array")
                            else:
                                # Validate individual options
                                for j, option in enumerate(exp_date[option_type]):
                                    if not isinstance(option, dict):
                                        validation_results['errors'].append(f"expirationDates[{i}].{option_type}[{j}] must be an object")
                                        continue
                                    
                                    option_required = ['strike', 'lastPrice']
                                    for field in option_required:
                                        if field not in option:
                                            validation_results['warnings'].append(f"expirationDates[{i}].{option_type}[{j}] missing field: {field}")
        
        return validation_results
    
    def test_single_ticker(self, ticker: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Test a single ticker symbol.
        
        Args:
            ticker: Ticker symbol to test
            verbose: Whether to print detailed output
            
        Returns:
            Test results dictionary
        """
        if verbose:
            print(f"\n{'='*50}")
            print(f"Testing Ticker: {ticker}")
            print(f"{'='*50}")
        
        # Make the request
        result = self.make_request(ticker)
        
        if verbose:
            print(f"Status Code: {result.get('status_code', 'N/A')}")
            print(f"Request Time: {result.get('request_time', 0):.3f}s")
            print(f"Response Size: {result.get('response_size', 0)} bytes")
        
        if result['success']:
            # Validate response structure
            validation = self.validate_response_structure(result['data'])
            result['validation'] = validation
            
            if verbose:
                if validation['valid']:
                    print("✅ Response structure is valid")
                else:
                    print("❌ Response structure validation failed")
                    for error in validation['errors']:
                        print(f"  Error: {error}")
                
                if validation['warnings']:
                    print("⚠️  Warnings:")
                    for warning in validation['warnings']:
                        print(f"  Warning: {warning}")
                
                # Print data summary
                data = result['data']
                if 'expirationDates' in data:
                    exp_dates = data['expirationDates']
                    total_calls = sum(len(exp.get('calls', [])) for exp in exp_dates)
                    total_puts = sum(len(exp.get('puts', [])) for exp in exp_dates)
                    
                    print(f"\n📈 Data Summary:")
                    print(f"  Ticker: {data.get('ticker')}")
                    print(f"  Stock Price: ${data.get('stockPrice')}")
                    print(f"  VIX Value: {data.get('vixValue')}")
                    print(f"  Expiration Dates: {len(exp_dates)}")
                    print(f"  Total Calls: {total_calls}")
                    print(f"  Total Puts: {total_puts}")
                    print(f"  Total Options: {total_calls + total_puts}")
        else:
            if verbose:
                print(f"❌ Request failed: {result.get('error', 'Unknown error')}")
                if 'data' in result and isinstance(result['data'], dict):
                    if 'error' in result['data']:
                        print(f"API Error: {result['data']['error']}")
                        print(f"Error Type: {result['data'].get('errorType', 'Unknown')}")
        
        return result
    
    def test_cors_headers(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Test CORS headers in the API response.
        
        Args:
            verbose: Whether to print detailed output
            
        Returns:
            CORS test results
        """
        if verbose:
            print(f"\n{'='*50}")
            print(f"Testing CORS Headers")
            print(f"{'='*50}")
        
        result = self.make_request("SPY")
        
        cors_results = {
            'success': result['success'],
            'cors_enabled': False,
            'headers_present': [],
            'headers_missing': []
        }
        
        if result['success']:
            headers = result.get('headers', {})
            
            # Check for CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            }
            
            for header, expected_value in cors_headers.items():
                if header in headers:
                    cors_results['headers_present'].append(header)
                    if verbose:
                        print(f"✅ {header}: {headers[header]}")
                else:
                    cors_results['headers_missing'].append(header)
                    if verbose:
                        print(f"❌ Missing: {header}")
            
            cors_results['cors_enabled'] = len(cors_results['headers_missing']) == 0
            
            if verbose:
                if cors_results['cors_enabled']:
                    print("✅ CORS is properly configured")
                else:
                    print("❌ CORS configuration incomplete")
        else:
            if verbose:
                print(f"❌ Could not test CORS - request failed: {result.get('error')}")
        
        return cors_results
    
    def test_error_handling(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Test error handling with invalid inputs.
        
        Args:
            verbose: Whether to print detailed output
            
        Returns:
            Error handling test results
        """
        if verbose:
            print(f"\n{'='*50}")
            print(f"Testing Error Handling")
            print(f"{'='*50}")
        
        test_cases = [
            {'ticker': 'INVALID_TICKER_SYMBOL_123', 'expected_error': True},
            {'ticker': '', 'expected_error': False},  # Should default to SPY
            {'ticker': 'SPY', 'additional_params': {'invalid_param': 'value'}, 'expected_error': False}
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            if verbose:
                print(f"\nTest Case {i+1}: {test_case}")
            
            ticker = test_case.get('ticker')
            additional_params = test_case.get('additional_params')
            expected_error = test_case.get('expected_error', False)
            
            result = self.make_request(ticker, additional_params)
            
            test_result = {
                'test_case': test_case,
                'success': result['success'],
                'status_code': result.get('status_code'),
                'expected_error': expected_error,
                'correct_behavior': (not result['success']) == expected_error
            }
            
            if verbose:
                if test_result['correct_behavior']:
                    print(f"✅ Correct behavior - Expected error: {expected_error}, Got error: {not result['success']}")
                else:
                    print(f"❌ Incorrect behavior - Expected error: {expected_error}, Got error: {not result['success']}")
                
                if not result['success'] and 'data' in result:
                    print(f"Error details: {result['data']}")
            
            results.append(test_result)
        
        return {
            'test_cases': results,
            'all_passed': all(r['correct_behavior'] for r in results)
        }
    
    def run_performance_test(self, ticker: str = "SPY", num_requests: int = 5, 
                           verbose: bool = True) -> Dict[str, Any]:
        """
        Run performance tests with multiple requests.
        
        Args:
            ticker: Ticker symbol to test
            num_requests: Number of requests to make
            verbose: Whether to print detailed output
            
        Returns:
            Performance test results
        """
        if verbose:
            print(f"\n{'='*50}")
            print(f"Performance Testing - {num_requests} requests")
            print(f"{'='*50}")
        
        results = []
        total_start_time = time.time()
        
        for i in range(num_requests):
            if verbose:
                print(f"Request {i+1}/{num_requests}...", end=' ')
            
            result = self.make_request(ticker)
            results.append(result)
            
            if verbose:
                if result['success']:
                    print(f"✅ {result['request_time']:.3f}s")
                else:
                    print(f"❌ Failed")
        
        total_time = time.time() - total_start_time
        
        # Calculate statistics
        successful_requests = [r for r in results if r['success']]
        success_rate = len(successful_requests) / len(results) * 100
        
        if successful_requests:
            response_times = [r['request_time'] for r in successful_requests]
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            response_sizes = [r.get('response_size', 0) for r in successful_requests]
            avg_size = sum(response_sizes) / len(response_sizes)
        else:
            avg_time = min_time = max_time = avg_size = 0
        
        perf_results = {
            'total_requests': num_requests,
            'successful_requests': len(successful_requests),
            'success_rate': success_rate,
            'total_time': total_time,
            'avg_response_time': avg_time,
            'min_response_time': min_time,
            'max_response_time': max_time,
            'avg_response_size': avg_size,
            'requests_per_second': num_requests / total_time if total_time > 0 else 0
        }
        
        if verbose:
            print(f"\n📊 Performance Results:")
            print(f"  Total Requests: {perf_results['total_requests']}")
            print(f"  Successful: {perf_results['successful_requests']}")
            print(f"  Success Rate: {perf_results['success_rate']:.1f}%")
            print(f"  Total Time: {perf_results['total_time']:.3f}s")
            print(f"  Requests/Second: {perf_results['requests_per_second']:.2f}")
            
            if successful_requests:
                print(f"  Avg Response Time: {perf_results['avg_response_time']:.3f}s")
                print(f"  Min Response Time: {perf_results['min_response_time']:.3f}s")
                print(f"  Max Response Time: {perf_results['max_response_time']:.3f}s")
                print(f"  Avg Response Size: {perf_results['avg_response_size']:.0f} bytes")
        
        return perf_results
    
    def run_comprehensive_test(self, tickers: List[str] = None, 
                             performance_requests: int = 3) -> Dict[str, Any]:
        """
        Run a comprehensive test suite.
        
        Args:
            tickers: List of tickers to test
            performance_requests: Number of requests for performance testing
            
        Returns:
            Comprehensive test results
        """
        if tickers is None:
            tickers = ["SPY", "AAPL", "MSFT"]
        
        print(f"\n🧪 Running Comprehensive Integration Test Suite")
        print(f"API Endpoint: {self.base_url}")
        print(f"Testing {len(tickers)} tickers: {', '.join(tickers)}")
        
        all_results = {
            'api_endpoint': self.base_url,
            'test_timestamp': datetime.now().isoformat(),
            'ticker_tests': {},
            'cors_test': {},
            'error_handling_test': {},
            'performance_test': {},
            'summary': {}
        }
        
        # Test individual tickers
        print(f"\n1. Testing Individual Tickers")
        print(f"{'='*40}")
        
        successful_ticker_tests = 0
        for ticker in tickers:
            result = self.test_single_ticker(ticker, verbose=False)
            all_results['ticker_tests'][ticker] = result
            
            if result['success']:
                successful_ticker_tests += 1
                print(f"  {ticker:8} ✅ {result['request_time']:.3f}s")
            else:
                print(f"  {ticker:8} ❌ {result.get('error', 'Failed')}")
        
        # Test CORS
        print(f"\n2. Testing CORS Configuration")
        print(f"{'='*40}")
        cors_result = self.test_cors_headers(verbose=False)
        all_results['cors_test'] = cors_result
        
        if cors_result['cors_enabled']:
            print("  ✅ CORS properly configured")
        else:
            print("  ❌ CORS configuration issues")
            for header in cors_result['headers_missing']:
                print(f"    Missing: {header}")
        
        # Test error handling
        print(f"\n3. Testing Error Handling")
        print(f"{'='*40}")
        error_result = self.test_error_handling(verbose=False)
        all_results['error_handling_test'] = error_result
        
        if error_result['all_passed']:
            print("  ✅ Error handling working correctly")
        else:
            print("  ❌ Error handling issues detected")
            for test_case in error_result['test_cases']:
                if not test_case['correct_behavior']:
                    print(f"    Failed: {test_case['test_case']}")
        
        # Performance testing
        print(f"\n4. Performance Testing")
        print(f"{'='*40}")
        perf_result = self.run_performance_test("SPY", performance_requests, verbose=False)
        all_results['performance_test'] = perf_result
        
        print(f"  Requests: {perf_result['total_requests']}")
        print(f"  Success Rate: {perf_result['success_rate']:.1f}%")
        print(f"  Avg Response Time: {perf_result['avg_response_time']:.3f}s")
        print(f"  Requests/Second: {perf_result['requests_per_second']:.2f}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(tickers) + 3  # tickers + CORS + error handling + performance
        passed_tests = successful_ticker_tests
        
        if cors_result['cors_enabled']:
            passed_tests += 1
        if error_result['all_passed']:
            passed_tests += 1
        if perf_result['success_rate'] >= 80:  # Consider 80%+ success rate as passing
            passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        
        all_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_success': success_rate >= 80
        }
        
        print(f"Total Test Categories: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ INTEGRATION TESTS PASSED")
        else:
            print("❌ INTEGRATION TESTS FAILED")
        
        return all_results


def get_api_endpoint_from_serverless(stage: str = "dev", region: str = "us-east-1") -> Optional[str]:
    """
    Get API endpoint URL from serverless info command.
    
    Args:
        stage: Deployment stage
        region: AWS region
        
    Returns:
        API endpoint URL or None if not found
    """
    import subprocess
    
    try:
        # Run serverless info command
        result = subprocess.run(
            ['serverless', 'info', '--stage', stage, '--region', region],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse output to find endpoint
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GET - ' in line and '/options-analytics' in line:
                    # Extract URL
                    parts = line.split('GET - ')
                    if len(parts) > 1:
                        url = parts[1].strip()
                        # Remove the path to get base URL
                        if '/options-analytics' in url:
                            base_url = url.replace('/options-analytics', '')
                            return base_url
        
        return None
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return None


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Integration testing for deployed Options Analytics API')
    parser.add_argument('--url', '-u', help='API base URL (if not provided, will try to get from serverless info)')
    parser.add_argument('--stage', '-s', default='dev', help='Deployment stage (default: dev)')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--ticker', '-t', help='Single ticker to test')
    parser.add_argument('--tickers', nargs='+', help='List of tickers to test')
    parser.add_argument('--performance', '-p', type=int, default=3, help='Number of requests for performance testing')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Get API endpoint
    if args.url:
        base_url = args.url
    else:
        print("🔍 Getting API endpoint from serverless info...")
        base_url = get_api_endpoint_from_serverless(args.stage, args.region)
        
        if not base_url:
            print("❌ Could not get API endpoint. Please provide --url or ensure service is deployed")
            sys.exit(1)
        
        print(f"✅ Found API endpoint: {base_url}")
    
    # Create tester
    tester = IntegrationTester(base_url, timeout=args.timeout)
    
    if args.ticker:
        # Test single ticker
        result = tester.test_single_ticker(args.ticker, verbose=args.verbose)
        if not result['success']:
            sys.exit(1)
    else:
        # Run comprehensive test suite
        tickers = args.tickers if args.tickers else ["SPY", "AAPL", "MSFT"]
        results = tester.run_comprehensive_test(tickers, args.performance)
        
        # Exit with error code if tests failed
        if not results['summary']['overall_success']:
            sys.exit(1)


if __name__ == '__main__':
    main()