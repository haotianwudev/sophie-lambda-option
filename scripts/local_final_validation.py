#!/usr/bin/env python3
"""
Local final validation test for the Options Analytics API handler.
Tests the handler function directly without requiring deployment.
"""

import json
import sys
import time
import os
from typing import Dict, Any, List
from datetime import datetime, timezone
import traceback

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the handler
from handler import get_options_analytics


class LocalFinalValidationTester:
    """Local validation testing for the Options Analytics handler."""
    
    def __init__(self):
        """Initialize the local tester."""
        self.test_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'test_type': 'local_handler_test',
            'tests': {},
            'summary': {}
        }
    
    def create_mock_event(self, ticker: str = None, additional_params: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Create a mock API Gateway event for testing.
        
        Args:
            ticker: Ticker symbol to include in query parameters
            additional_params: Additional query parameters
            
        Returns:
            Mock API Gateway event
        """
        query_params = {}
        
        if ticker is not None:
            query_params['ticker'] = ticker
        
        if additional_params:
            query_params.update(additional_params)
        
        return {
            'httpMethod': 'GET',
            'path': '/options-analytics',
            'queryStringParameters': query_params if query_params else None,
            'headers': {
                'Accept': 'application/json',
                'User-Agent': 'LocalValidationTest/1.0'
            },
            'requestContext': {
                'requestId': f'test-{int(time.time())}'
            }
        }
    
    def create_mock_context(self):
        """Create a mock Lambda context."""
        class MockContext:
            def __init__(self):
                self.function_name = 'options-analytics-test'
                self.function_version = '$LATEST'
                self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:options-analytics-test'
                self.memory_limit_in_mb = '512'
                self.remaining_time_in_millis = lambda: 30000
                self.log_group_name = '/aws/lambda/options-analytics-test'
                self.log_stream_name = '2025/01/16/[$LATEST]test'
                self.aws_request_id = f'test-{int(time.time())}'
        
        return MockContext()
    
    def call_handler(self, ticker: str = None, additional_params: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Call the handler function with mock event and context.
        
        Args:
            ticker: Ticker symbol to test
            additional_params: Additional query parameters
            
        Returns:
            Handler response with timing and error information
        """
        event = self.create_mock_event(ticker, additional_params)
        context = self.create_mock_context()
        
        start_time = time.time()
        
        try:
            response = get_options_analytics(event, context)
            execution_time = time.time() - start_time
            
            # Parse response body if it's JSON
            parsed_body = None
            if response.get('body'):
                try:
                    parsed_body = json.loads(response['body'])
                except json.JSONDecodeError:
                    parsed_body = {'error': 'Invalid JSON in response body'}
            
            return {
                'success': response.get('statusCode') == 200,
                'status_code': response.get('statusCode'),
                'headers': response.get('headers', {}),
                'body': response.get('body'),
                'parsed_body': parsed_body,
                'execution_time': execution_time,
                'event': event
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'execution_time': execution_time,
                'event': event
            }
    
    def validate_response_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response structure against design specification."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'structure_checks': {}
        }
        
        # Required top-level fields
        required_fields = {
            'ticker': str,
            'stockPrice': (int, float),
            'vixValue': (int, float),
            'dataTimestamp': str,
            'vixTimestamp': str,
            'expirationDates': list
        }
        
        # Check required fields and types
        for field, expected_type in required_fields.items():
            if field not in data:
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['valid'] = False
                validation_results['structure_checks'][field] = False
            else:
                if not isinstance(data[field], expected_type):
                    validation_results['errors'].append(f"{field} must be of type {expected_type.__name__}")
                    validation_results['valid'] = False
                    validation_results['structure_checks'][field] = False
                else:
                    validation_results['structure_checks'][field] = True
        
        # Validate expiration dates structure if present
        if 'expirationDates' in data and isinstance(data['expirationDates'], list):
            for i, exp_date in enumerate(data['expirationDates']):
                if not isinstance(exp_date, dict):
                    validation_results['errors'].append(f"expirationDates[{i}] must be an object")
                    continue
                
                # Check required fields
                for field in ['expiration', 'calls', 'puts']:
                    if field not in exp_date:
                        validation_results['errors'].append(f"expirationDates[{i}] missing field: {field}")
                
                # Validate options arrays
                for option_type in ['calls', 'puts']:
                    if option_type in exp_date and isinstance(exp_date[option_type], list):
                        for j, option in enumerate(exp_date[option_type]):
                            if isinstance(option, dict):
                                for req_field in ['strike', 'lastPrice']:
                                    if req_field not in option:
                                        validation_results['warnings'].append(
                                            f"expirationDates[{i}].{option_type}[{j}] missing {req_field}"
                                        )
        
        return validation_results
    
    def test_multiple_tickers_local(self, tickers: List[str] = None) -> Dict[str, Any]:
        """Test multiple tickers locally."""
        if tickers is None:
            tickers = ["SPY", "AAPL", "MSFT"]
        
        print(f"\n🎯 Local Testing Multiple Tickers: {', '.join(tickers)}")
        print("=" * 60)
        
        results = {
            'test_name': 'Local Multiple Tickers Test',
            'tickers_tested': tickers,
            'results': {},
            'summary': {
                'total_tickers': len(tickers),
                'successful_tickers': 0,
                'failed_tickers': 0,
                'avg_execution_time': 0,
                'all_passed': True
            }
        }
        
        total_execution_time = 0
        
        for ticker in tickers:
            print(f"\nTesting {ticker}...")
            
            result = self.call_handler(ticker)
            
            ticker_result = {
                'ticker': ticker,
                'success': result['success'],
                'status_code': result.get('status_code'),
                'execution_time': result.get('execution_time', 0),
                'validation': None,
                'data_summary': None,
                'error': result.get('error')
            }
            
            if result['success'] and result.get('parsed_body'):
                # Validate response structure
                validation = self.validate_response_structure(result['parsed_body'])
                ticker_result['validation'] = validation
                
                # Create data summary
                data = result['parsed_body']
                if 'expirationDates' in data:
                    exp_dates = data['expirationDates']
                    total_calls = sum(len(exp.get('calls', [])) for exp in exp_dates)
                    total_puts = sum(len(exp.get('puts', [])) for exp in exp_dates)
                    
                    ticker_result['data_summary'] = {
                        'ticker': data.get('ticker'),
                        'stock_price': data.get('stockPrice'),
                        'vix_value': data.get('vixValue'),
                        'expiration_dates': len(exp_dates),
                        'total_calls': total_calls,
                        'total_puts': total_puts,
                        'total_options': total_calls + total_puts
                    }
                
                if validation['valid']:
                    results['summary']['successful_tickers'] += 1
                    print(f"  ✅ {ticker}: {result['execution_time']:.3f}s - {ticker_result['data_summary']['total_options']} options")
                else:
                    results['summary']['failed_tickers'] += 1
                    results['summary']['all_passed'] = False
                    print(f"  ❌ {ticker}: Validation failed")
                    for error in validation['errors'][:3]:
                        print(f"    Error: {error}")
                
                total_execution_time += result['execution_time']
            else:
                results['summary']['failed_tickers'] += 1
                results['summary']['all_passed'] = False
                error_msg = result.get('error', 'Unknown error')
                print(f"  ❌ {ticker}: Handler failed - {error_msg}")
            
            results['results'][ticker] = ticker_result
        
        # Calculate average execution time
        if results['summary']['successful_tickers'] > 0:
            results['summary']['avg_execution_time'] = total_execution_time / results['summary']['successful_tickers']
        
        print(f"\n📊 Local Multiple Tickers Summary:")
        print(f"  Successful: {results['summary']['successful_tickers']}/{results['summary']['total_tickers']}")
        print(f"  Average Execution Time: {results['summary']['avg_execution_time']:.3f}s")
        
        return results
    
    def test_error_scenarios_local(self) -> Dict[str, Any]:
        """Test error scenarios locally."""
        print(f"\n🚨 Local Testing Error Scenarios")
        print("=" * 60)
        
        test_cases = [
            {
                'name': 'Invalid Ticker Symbol',
                'ticker': 'INVALID_TICKER_SYMBOL_123',
                'should_fail': True
            },
            {
                'name': 'Empty Ticker (Should Default to SPY)',
                'ticker': '',
                'should_fail': False
            },
            {
                'name': 'None Ticker (Should Default to SPY)',
                'ticker': None,
                'should_fail': False
            },
            {
                'name': 'Very Long Ticker Symbol',
                'ticker': 'A' * 50,
                'should_fail': True
            }
        ]
        
        results = {
            'test_name': 'Local Error Scenarios Test',
            'test_cases': [],
            'summary': {
                'total_cases': len(test_cases),
                'passed_cases': 0,
                'failed_cases': 0,
                'all_passed': True
            }
        }
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            print(f"    Ticker: '{test_case['ticker']}'")
            
            result = self.call_handler(test_case['ticker'])
            
            case_result = {
                'test_case': test_case,
                'success': result['success'],
                'status_code': result.get('status_code'),
                'execution_time': result.get('execution_time', 0),
                'error_message': result.get('error'),
                'expected_behavior': False,
                'has_cors_headers': False
            }
            
            # Check if behavior matches expectations
            if test_case['should_fail']:
                case_result['expected_behavior'] = not result['success'] or result.get('status_code') != 200
            else:
                case_result['expected_behavior'] = result['success'] and result.get('status_code') == 200
            
            # Check CORS headers
            headers = result.get('headers', {})
            case_result['has_cors_headers'] = 'Access-Control-Allow-Origin' in headers
            
            if case_result['expected_behavior']:
                results['summary']['passed_cases'] += 1
                status = "✅ PASSED"
            else:
                results['summary']['failed_cases'] += 1
                results['summary']['all_passed'] = False
                status = "❌ FAILED"
            
            print(f"    Result: {status}")
            print(f"    Status Code: {result.get('status_code', 'N/A')}")
            print(f"    Execution Time: {result.get('execution_time', 0):.3f}s")
            print(f"    CORS Headers: {'✅' if case_result['has_cors_headers'] else '❌'}")
            
            if case_result['error_message']:
                print(f"    Error: {case_result['error_message']}")
            
            results['test_cases'].append(case_result)
        
        print(f"\n📊 Local Error Scenarios Summary:")
        print(f"  Passed: {results['summary']['passed_cases']}/{results['summary']['total_cases']}")
        
        return results
    
    def test_response_structure_local(self) -> Dict[str, Any]:
        """Test response structure locally."""
        print(f"\n📋 Local Testing Response Structure")
        print("=" * 60)
        
        result = self.call_handler("SPY")
        
        test_result = {
            'test_name': 'Local Response Structure Test',
            'success': result['success'],
            'validation': None,
            'structure_compliance': False,
            'execution_time': result.get('execution_time', 0)
        }
        
        if result['success'] and result.get('parsed_body'):
            validation = self.validate_response_structure(result['parsed_body'])
            test_result['validation'] = validation
            test_result['structure_compliance'] = validation['valid']
            
            print(f"Status: {'✅ PASSED' if validation['valid'] else '❌ FAILED'}")
            print(f"Execution Time: {result['execution_time']:.3f}s")
            
            if validation['valid']:
                print("  ✅ All required fields present and correctly typed")
            else:
                print("  ❌ Structure validation failed:")
                for error in validation['errors']:
                    print(f"    Error: {error}")
            
            if validation['warnings']:
                print("  ⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"    Warning: {warning}")
        else:
            print(f"  ❌ Handler failed: {result.get('error', 'Unknown error')}")
        
        return test_result
    
    def test_cors_headers_local(self) -> Dict[str, Any]:
        """Test CORS headers in local response."""
        print(f"\n🌐 Local Testing CORS Headers")
        print("=" * 60)
        
        result = self.call_handler("SPY")
        
        test_result = {
            'test_name': 'Local CORS Headers Test',
            'success': result['success'],
            'cors_headers': {},
            'cors_compliant': False
        }
        
        if result['success']:
            headers = result.get('headers', {})
            
            # Required CORS headers
            required_cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Headers',
                'Access-Control-Allow-Methods'
            ]
            
            cors_present = 0
            for header in required_cors_headers:
                if header in headers:
                    test_result['cors_headers'][header] = headers[header]
                    cors_present += 1
                    print(f"  ✅ {header}: {headers[header]}")
                else:
                    print(f"  ❌ Missing: {header}")
            
            test_result['cors_compliant'] = cors_present == len(required_cors_headers)
            
            if test_result['cors_compliant']:
                print("  ✅ CORS headers properly configured")
            else:
                print("  ❌ CORS configuration incomplete")
        else:
            print(f"  ❌ Handler failed: {result.get('error')}")
        
        return test_result
    
    def test_timestamp_format_local(self) -> Dict[str, Any]:
        """Test timestamp formatting locally."""
        print(f"\n⏰ Local Testing Timestamp Format")
        print("=" * 60)
        
        result = self.call_handler("SPY")
        
        test_result = {
            'test_name': 'Local Timestamp Format Test',
            'success': result['success'],
            'timestamp_tests': {},
            'all_timestamps_valid': False
        }
        
        if result['success'] and result.get('parsed_body'):
            data = result['parsed_body']
            timestamp_fields = ['dataTimestamp', 'vixTimestamp']
            
            valid_timestamps = 0
            for field in timestamp_fields:
                if field in data:
                    timestamp_str = data[field]
                    
                    try:
                        # Try to parse ISO format
                        parsed_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        test_result['timestamp_tests'][field] = {
                            'timestamp': timestamp_str,
                            'valid': True,
                            'parsed': parsed_time.isoformat()
                        }
                        valid_timestamps += 1
                        print(f"  ✅ {field}: {timestamp_str} (Valid ISO format)")
                    except ValueError as e:
                        test_result['timestamp_tests'][field] = {
                            'timestamp': timestamp_str,
                            'valid': False,
                            'error': str(e)
                        }
                        print(f"  ❌ {field}: {timestamp_str} (Invalid format: {str(e)})")
                else:
                    test_result['timestamp_tests'][field] = {
                        'missing': True,
                        'valid': False
                    }
                    print(f"  ❌ Missing timestamp field: {field}")
            
            test_result['all_timestamps_valid'] = valid_timestamps == len(timestamp_fields)
        else:
            print(f"  ❌ Handler failed: {result.get('error')}")
        
        return test_result
    
    def run_comprehensive_local_validation(self) -> Dict[str, Any]:
        """Run comprehensive local validation tests."""
        print(f"\n🎯 LOCAL FINAL VALIDATION TEST SUITE")
        print(f"{'='*80}")
        print(f"Testing handler function directly (no deployment required)")
        print(f"Test Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Run all test categories
        test_categories = [
            ('multiple_tickers', self.test_multiple_tickers_local),
            ('response_structure', self.test_response_structure_local),
            ('error_scenarios', self.test_error_scenarios_local),
            ('cors_headers', self.test_cors_headers_local),
            ('timestamp_format', self.test_timestamp_format_local)
        ]
        
        for category_name, test_method in test_categories:
            try:
                self.test_results['tests'][category_name] = test_method()
            except Exception as e:
                print(f"\n❌ Error running {category_name}: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                self.test_results['tests'][category_name] = {
                    'test_name': category_name,
                    'error': str(e),
                    'success': False
                }
        
        # Generate summary
        self._generate_local_summary()
        
        return self.test_results
    
    def _generate_local_summary(self):
        """Generate local validation summary."""
        print(f"\n{'='*80}")
        print(f"LOCAL VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        total_categories = len(self.test_results['tests'])
        passed_categories = 0
        
        # Analyze each test category
        for category_name, results in self.test_results['tests'].items():
            category_passed = False
            
            if category_name == 'multiple_tickers':
                category_passed = results.get('summary', {}).get('all_passed', False)
            elif category_name == 'response_structure':
                category_passed = results.get('structure_compliance', False)
            elif category_name == 'error_scenarios':
                category_passed = results.get('summary', {}).get('all_passed', False)
            elif category_name == 'cors_headers':
                category_passed = results.get('cors_compliant', False)
            elif category_name == 'timestamp_format':
                category_passed = results.get('all_timestamps_valid', False)
            
            if category_passed:
                passed_categories += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            print(f"{status} {category_name.replace('_', ' ').title()}")
        
        # Overall assessment
        success_rate = (passed_categories / total_categories) * 100
        overall_success = success_rate >= 80
        
        self.test_results['summary'] = {
            'total_categories': total_categories,
            'passed_categories': passed_categories,
            'success_rate': success_rate,
            'overall_success': overall_success,
            'test_completed': datetime.now(timezone.utc).isoformat()
        }
        
        print(f"\n{'='*40}")
        print(f"OVERALL RESULT: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        print(f"Success Rate: {success_rate:.1f}% ({passed_categories}/{total_categories})")
        print(f"{'='*40}")


def main():
    """Main function for local testing."""
    print("🧪 Starting Local Final Validation Tests")
    
    try:
        tester = LocalFinalValidationTester()
        results = tester.run_comprehensive_local_validation()
        
        # Exit with appropriate code
        if results['summary']['overall_success']:
            print(f"\n🎉 Local validation completed successfully!")
            sys.exit(0)
        else:
            print(f"\n💥 Local validation failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Fatal error during local validation: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main()