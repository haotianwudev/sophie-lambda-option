#!/usr/bin/env python3
"""
Final integration and validation test script for Options Analytics API.
Comprehensive testing of all requirements for task 12.
"""

import json
import sys
import time
import requests
import argparse
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from urllib.parse import urljoin, urlencode
import re


class FinalValidationTester:
    """Final validation testing framework for Options Analytics API."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the final validation tester.
        
        Args:
            base_url: Base URL of the deployed API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'OptionsAnalytics-FinalValidation/1.0',
            'Accept': 'application/json'
        })
        
        # Test results storage
        self.test_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'api_endpoint': self.base_url,
            'tests': {},
            'summary': {}
        }
    
    def make_request(self, ticker: Optional[str] = None, 
                    additional_params: Optional[Dict[str, str]] = None,
                    custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Make a request to the options analytics endpoint.
        
        Args:
            ticker: Ticker symbol to request
            additional_params: Additional query parameters
            custom_headers: Custom headers for the request
            
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
        
        # Prepare headers
        headers = {}
        if custom_headers:
            headers.update(custom_headers)
        
        start_time = time.time()
        
        try:
            response = self.session.get(url, timeout=self.timeout, headers=headers)
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
        Validate the complete response structure against design specification.
        
        Args:
            data: Response data to validate
            
        Returns:
            Dictionary with detailed validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'structure_checks': {}
        }
        
        # Required top-level fields from design specification
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
        
        # Validate expiration dates structure
        if 'expirationDates' in data and isinstance(data['expirationDates'], list):
            exp_validation = self._validate_expiration_dates(data['expirationDates'])
            validation_results['errors'].extend(exp_validation['errors'])
            validation_results['warnings'].extend(exp_validation['warnings'])
            if exp_validation['errors']:
                validation_results['valid'] = False
            validation_results['structure_checks']['expirationDates_structure'] = len(exp_validation['errors']) == 0
        
        # Validate timestamp formats
        timestamp_validation = self._validate_timestamps(data)
        validation_results['errors'].extend(timestamp_validation['errors'])
        validation_results['warnings'].extend(timestamp_validation['warnings'])
        if timestamp_validation['errors']:
            validation_results['valid'] = False
        validation_results['structure_checks']['timestamps'] = len(timestamp_validation['errors']) == 0
        
        return validation_results
    
    def _validate_expiration_dates(self, expiration_dates: List[Dict]) -> Dict[str, Any]:
        """Validate expiration dates structure."""
        validation = {'errors': [], 'warnings': []}
        
        for i, exp_date in enumerate(expiration_dates):
            if not isinstance(exp_date, dict):
                validation['errors'].append(f"expirationDates[{i}] must be an object")
                continue
            
            # Check required fields in expiration date
            exp_required = ['expiration', 'calls', 'puts']
            for field in exp_required:
                if field not in exp_date:
                    validation['errors'].append(f"expirationDates[{i}] missing field: {field}")
            
            # Validate expiration date format (YYYY-MM-DD)
            if 'expiration' in exp_date:
                exp_str = exp_date['expiration']
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', exp_str):
                    validation['errors'].append(f"expirationDates[{i}].expiration must be in YYYY-MM-DD format")
            
            # Validate calls and puts arrays
            for option_type in ['calls', 'puts']:
                if option_type in exp_date:
                    if not isinstance(exp_date[option_type], list):
                        validation['errors'].append(f"expirationDates[{i}].{option_type} must be an array")
                    else:
                        # Validate individual options
                        option_validation = self._validate_options_array(
                            exp_date[option_type], f"expirationDates[{i}].{option_type}"
                        )
                        validation['errors'].extend(option_validation['errors'])
                        validation['warnings'].extend(option_validation['warnings'])
        
        return validation
    
    def _validate_options_array(self, options: List[Dict], path: str) -> Dict[str, Any]:
        """Validate individual options in calls/puts arrays."""
        validation = {'errors': [], 'warnings': []}
        
        for j, option in enumerate(options):
            if not isinstance(option, dict):
                validation['errors'].append(f"{path}[{j}] must be an object")
                continue
            
            # Required fields for options
            option_required = {
                'strike': (int, float),
                'lastPrice': (int, float)
            }
            
            for field, expected_type in option_required.items():
                if field not in option:
                    validation['errors'].append(f"{path}[{j}] missing required field: {field}")
                elif not isinstance(option[field], expected_type):
                    validation['errors'].append(f"{path}[{j}].{field} must be a number")
            
            # Optional fields that should be numbers if present
            optional_fields = ['impliedVolatility', 'delta']
            for field in optional_fields:
                if field in option and option[field] is not None:
                    if not isinstance(option[field], (int, float)):
                        validation['warnings'].append(f"{path}[{j}].{field} should be a number if present")
        
        return validation
    
    def _validate_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate timestamp formats and accuracy."""
        validation = {'errors': [], 'warnings': []}
        
        timestamp_fields = ['dataTimestamp', 'vixTimestamp']
        
        for field in timestamp_fields:
            if field in data:
                timestamp_str = data[field]
                
                # Check ISO format
                try:
                    parsed_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Check if timestamp is recent (within last hour)
                    now = datetime.now(timezone.utc)
                    time_diff = abs((now - parsed_time).total_seconds())
                    
                    if time_diff > 3600:  # More than 1 hour old
                        validation['warnings'].append(f"{field} is more than 1 hour old: {timestamp_str}")
                    
                except ValueError:
                    validation['errors'].append(f"{field} is not in valid ISO format: {timestamp_str}")
        
        return validation
    
    def test_multiple_tickers(self, tickers: List[str] = None) -> Dict[str, Any]:
        """
        Test API with various tickers (SPY, AAPL, MSFT).
        Requirement: Test complete API with various tickers
        """
        if tickers is None:
            tickers = ["SPY", "AAPL", "MSFT"]
        
        print(f"\n🎯 Testing Multiple Tickers: {', '.join(tickers)}")
        print("=" * 60)
        
        results = {
            'test_name': 'Multiple Tickers Test',
            'tickers_tested': tickers,
            'results': {},
            'summary': {
                'total_tickers': len(tickers),
                'successful_tickers': 0,
                'failed_tickers': 0,
                'avg_response_time': 0,
                'all_passed': True
            }
        }
        
        total_response_time = 0
        
        for ticker in tickers:
            print(f"\nTesting {ticker}...")
            
            result = self.make_request(ticker)
            
            ticker_result = {
                'ticker': ticker,
                'success': result['success'],
                'status_code': result.get('status_code'),
                'request_time': result.get('request_time', 0),
                'validation': None,
                'data_summary': None
            }
            
            if result['success']:
                # Validate response structure
                validation = self.validate_response_structure(result['data'])
                ticker_result['validation'] = validation
                
                # Create data summary
                data = result['data']
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
                    print(f"  ✅ {ticker}: {result['request_time']:.3f}s - {ticker_result['data_summary']['total_options']} options")
                else:
                    results['summary']['failed_tickers'] += 1
                    results['summary']['all_passed'] = False
                    print(f"  ❌ {ticker}: Validation failed")
                    for error in validation['errors'][:3]:  # Show first 3 errors
                        print(f"    Error: {error}")
                
                total_response_time += result['request_time']
            else:
                results['summary']['failed_tickers'] += 1
                results['summary']['all_passed'] = False
                print(f"  ❌ {ticker}: Request failed - {result.get('error', 'Unknown error')}")
            
            results['results'][ticker] = ticker_result
        
        # Calculate average response time
        if results['summary']['successful_tickers'] > 0:
            results['summary']['avg_response_time'] = total_response_time / results['summary']['successful_tickers']
        
        print(f"\n📊 Multiple Tickers Summary:")
        print(f"  Successful: {results['summary']['successful_tickers']}/{results['summary']['total_tickers']}")
        print(f"  Average Response Time: {results['summary']['avg_response_time']:.3f}s")
        
        return results
    
    def test_response_structure_validation(self) -> Dict[str, Any]:
        """
        Validate response structure matches design specification.
        Requirement: Validate response structure matches design specification
        """
        print(f"\n📋 Testing Response Structure Validation")
        print("=" * 60)
        
        result = self.make_request("SPY")
        
        test_result = {
            'test_name': 'Response Structure Validation',
            'success': result['success'],
            'validation': None,
            'structure_compliance': False
        }
        
        if result['success']:
            validation = self.validate_response_structure(result['data'])
            test_result['validation'] = validation
            test_result['structure_compliance'] = validation['valid']
            
            print(f"Status: {'✅ PASSED' if validation['valid'] else '❌ FAILED'}")
            
            if validation['valid']:
                print("  ✅ All required fields present and correctly typed")
                print("  ✅ Expiration dates structure is valid")
                print("  ✅ Timestamps are properly formatted")
            else:
                print("  ❌ Structure validation failed:")
                for error in validation['errors']:
                    print(f"    Error: {error}")
            
            if validation['warnings']:
                print("  ⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"    Warning: {warning}")
            
            # Print structure check details
            print(f"\n  Structure Checks:")
            for check, passed in validation['structure_checks'].items():
                status = "✅" if passed else "❌"
                print(f"    {status} {check}")
        else:
            print(f"  ❌ Could not validate structure - request failed: {result.get('error')}")
        
        return test_result
    
    def test_error_scenarios(self) -> Dict[str, Any]:
        """
        Test error scenarios (invalid ticker, network failures).
        Requirement: Test error scenarios (invalid ticker, network failures)
        """
        print(f"\n🚨 Testing Error Scenarios")
        print("=" * 60)
        
        test_cases = [
            {
                'name': 'Invalid Ticker Symbol',
                'ticker': 'INVALID_TICKER_SYMBOL_123',
                'expected_status': [400, 500],  # Could be either depending on implementation
                'should_have_error': True
            },
            {
                'name': 'Empty Ticker (Should Default to SPY)',
                'ticker': '',
                'expected_status': [200],
                'should_have_error': False
            },
            {
                'name': 'Very Long Ticker Symbol',
                'ticker': 'A' * 50,
                'expected_status': [400, 500],
                'should_have_error': True
            },
            {
                'name': 'Special Characters in Ticker',
                'ticker': 'SP@Y!',
                'expected_status': [400, 500],
                'should_have_error': True
            }
        ]
        
        results = {
            'test_name': 'Error Scenarios Test',
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
            
            result = self.make_request(test_case['ticker'])
            
            case_result = {
                'test_case': test_case,
                'success': result['success'],
                'status_code': result.get('status_code'),
                'error_message': result.get('error') or (result.get('data', {}).get('error') if isinstance(result.get('data'), dict) else None),
                'expected_behavior': False,
                'has_cors_headers': False
            }
            
            # Check if behavior matches expectations
            if test_case['should_have_error']:
                # Should fail or return error status
                case_result['expected_behavior'] = (
                    not result['success'] or 
                    result.get('status_code') in test_case['expected_status']
                )
            else:
                # Should succeed
                case_result['expected_behavior'] = (
                    result['success'] and 
                    result.get('status_code') in test_case['expected_status']
                )
            
            # Check CORS headers even in error responses
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
            print(f"    CORS Headers: {'✅' if case_result['has_cors_headers'] else '❌'}")
            
            if case_result['error_message']:
                print(f"    Error: {case_result['error_message']}")
            
            results['test_cases'].append(case_result)
        
        print(f"\n📊 Error Scenarios Summary:")
        print(f"  Passed: {results['summary']['passed_cases']}/{results['summary']['total_cases']}")
        
        return results
    
    def test_cors_functionality(self) -> Dict[str, Any]:
        """
        Verify CORS functionality for frontend integration.
        Requirement: Verify CORS functionality for frontend integration
        """
        print(f"\n🌐 Testing CORS Functionality")
        print("=" * 60)
        
        results = {
            'test_name': 'CORS Functionality Test',
            'tests': {},
            'summary': {
                'all_passed': True,
                'cors_enabled': False
            }
        }
        
        # Test 1: Regular GET request CORS headers
        print(f"\n  Test 1: GET Request CORS Headers")
        get_result = self.make_request("SPY")
        
        get_cors_test = {
            'success': get_result['success'],
            'headers_present': {},
            'headers_missing': []
        }
        
        if get_result['success']:
            headers = get_result.get('headers', {})
            
            # Required CORS headers
            required_cors_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            }
            
            for header, expected_value in required_cors_headers.items():
                if header in headers:
                    get_cors_test['headers_present'][header] = headers[header]
                    print(f"    ✅ {header}: {headers[header]}")
                else:
                    get_cors_test['headers_missing'].append(header)
                    print(f"    ❌ Missing: {header}")
            
            get_cors_test['all_headers_present'] = len(get_cors_test['headers_missing']) == 0
        else:
            get_cors_test['all_headers_present'] = False
            print(f"    ❌ GET request failed: {get_result.get('error')}")
        
        results['tests']['get_request'] = get_cors_test
        
        # Test 2: OPTIONS preflight request
        print(f"\n  Test 2: OPTIONS Preflight Request")
        
        try:
            # Make OPTIONS request
            url = urljoin(self.base_url, '/options-analytics')
            options_response = self.session.options(
                url,
                headers={
                    'Origin': 'https://example.com',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=self.timeout
            )
            
            options_cors_test = {
                'success': options_response.status_code in [200, 204],
                'status_code': options_response.status_code,
                'headers_present': {},
                'supports_preflight': False
            }
            
            if options_cors_test['success']:
                headers = dict(options_response.headers)
                
                # Check preflight response headers
                preflight_headers = [
                    'Access-Control-Allow-Origin',
                    'Access-Control-Allow-Methods',
                    'Access-Control-Allow-Headers'
                ]
                
                for header in preflight_headers:
                    if header in headers:
                        options_cors_test['headers_present'][header] = headers[header]
                        print(f"    ✅ {header}: {headers[header]}")
                
                options_cors_test['supports_preflight'] = len(options_cors_test['headers_present']) >= 2
                
                if options_cors_test['supports_preflight']:
                    print(f"    ✅ Preflight request supported")
                else:
                    print(f"    ⚠️  Preflight support unclear")
            else:
                print(f"    ❌ OPTIONS request failed: {options_response.status_code}")
        
        except Exception as e:
            options_cors_test = {
                'success': False,
                'error': str(e),
                'supports_preflight': False
            }
            print(f"    ❌ OPTIONS request error: {str(e)}")
        
        results['tests']['options_request'] = options_cors_test
        
        # Test 3: Cross-origin simulation
        print(f"\n  Test 3: Cross-Origin Request Simulation")
        
        cross_origin_result = self.make_request(
            "SPY",
            custom_headers={
                'Origin': 'https://myapp.example.com',
                'Referer': 'https://myapp.example.com/dashboard'
            }
        )
        
        cross_origin_test = {
            'success': cross_origin_result['success'],
            'cors_headers_in_response': False
        }
        
        if cross_origin_result['success']:
            headers = cross_origin_result.get('headers', {})
            cross_origin_test['cors_headers_in_response'] = 'Access-Control-Allow-Origin' in headers
            
            if cross_origin_test['cors_headers_in_response']:
                print(f"    ✅ Cross-origin request successful with CORS headers")
                print(f"    Access-Control-Allow-Origin: {headers.get('Access-Control-Allow-Origin')}")
            else:
                print(f"    ⚠️  Cross-origin request successful but missing CORS headers")
        else:
            print(f"    ❌ Cross-origin request failed: {cross_origin_result.get('error')}")
        
        results['tests']['cross_origin'] = cross_origin_test
        
        # Overall CORS assessment
        cors_working = (
            get_cors_test.get('all_headers_present', False) and
            cross_origin_test.get('cors_headers_in_response', False)
        )
        
        results['summary']['cors_enabled'] = cors_working
        results['summary']['all_passed'] = cors_working
        
        print(f"\n📊 CORS Summary:")
        print(f"  GET Request CORS: {'✅' if get_cors_test.get('all_headers_present') else '❌'}")
        print(f"  OPTIONS Support: {'✅' if options_cors_test.get('supports_preflight') else '❌'}")
        print(f"  Cross-Origin: {'✅' if cross_origin_test.get('cors_headers_in_response') else '❌'}")
        print(f"  Overall CORS: {'✅ ENABLED' if cors_working else '❌ ISSUES DETECTED'}")
        
        return results
    
    def test_timestamp_accuracy(self) -> Dict[str, Any]:
        """
        Confirm timestamps are properly formatted and accurate.
        Requirement: Confirm timestamps are properly formatted and accurate
        """
        print(f"\n⏰ Testing Timestamp Accuracy")
        print("=" * 60)
        
        # Make request and capture request time
        request_start = datetime.now(timezone.utc)
        result = self.make_request("SPY")
        request_end = datetime.now(timezone.utc)
        
        test_result = {
            'test_name': 'Timestamp Accuracy Test',
            'success': result['success'],
            'timestamp_tests': {},
            'summary': {
                'all_passed': True,
                'timestamps_accurate': False,
                'timestamps_formatted_correctly': False
            }
        }
        
        if result['success']:
            data = result['data']
            
            # Test timestamp fields
            timestamp_fields = ['dataTimestamp', 'vixTimestamp']
            
            for field in timestamp_fields:
                if field in data:
                    timestamp_str = data[field]
                    
                    field_test = {
                        'timestamp_string': timestamp_str,
                        'format_valid': False,
                        'accuracy_valid': False,
                        'parsed_time': None,
                        'time_difference': None
                    }
                    
                    print(f"\n  Testing {field}: {timestamp_str}")
                    
                    # Test format
                    try:
                        # Parse ISO format timestamp
                        parsed_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        field_test['format_valid'] = True
                        field_test['parsed_time'] = parsed_time.isoformat()
                        print(f"    ✅ Format: Valid ISO format")
                        
                        # Test accuracy (should be within request timeframe + reasonable buffer)
                        time_diff_start = abs((parsed_time - request_start).total_seconds())
                        time_diff_end = abs((parsed_time - request_end).total_seconds())
                        min_diff = min(time_diff_start, time_diff_end)
                        
                        field_test['time_difference'] = min_diff
                        
                        # Allow up to 5 minutes difference for data freshness
                        if min_diff <= 300:  # 5 minutes
                            field_test['accuracy_valid'] = True
                            print(f"    ✅ Accuracy: Within {min_diff:.1f} seconds of request")
                        else:
                            field_test['accuracy_valid'] = False
                            print(f"    ⚠️  Accuracy: {min_diff:.1f} seconds old (may be stale data)")
                        
                    except ValueError as e:
                        field_test['format_valid'] = False
                        print(f"    ❌ Format: Invalid ISO format - {str(e)}")
                    
                    test_result['timestamp_tests'][field] = field_test
                else:
                    print(f"  ❌ Missing timestamp field: {field}")
                    test_result['timestamp_tests'][field] = {
                        'missing': True,
                        'format_valid': False,
                        'accuracy_valid': False
                    }
            
            # Overall assessment
            all_formats_valid = all(
                test.get('format_valid', False) 
                for test in test_result['timestamp_tests'].values()
            )
            
            all_accurate = all(
                test.get('accuracy_valid', False) 
                for test in test_result['timestamp_tests'].values()
            )
            
            test_result['summary']['timestamps_formatted_correctly'] = all_formats_valid
            test_result['summary']['timestamps_accurate'] = all_accurate
            test_result['summary']['all_passed'] = all_formats_valid and all_accurate
            
        else:
            print(f"  ❌ Could not test timestamps - request failed: {result.get('error')}")
            test_result['summary']['all_passed'] = False
        
        print(f"\n📊 Timestamp Summary:")
        print(f"  Format Valid: {'✅' if test_result['summary']['timestamps_formatted_correctly'] else '❌'}")
        print(f"  Accuracy Valid: {'✅' if test_result['summary']['timestamps_accurate'] else '❌'}")
        
        return test_result
    
    def run_comprehensive_final_validation(self) -> Dict[str, Any]:
        """
        Run all final validation tests as specified in task 12.
        """
        print(f"\n🎯 FINAL INTEGRATION AND VALIDATION TEST SUITE")
        print(f"{'='*80}")
        print(f"API Endpoint: {self.base_url}")
        print(f"Test Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Run all test categories
        test_categories = [
            ('multiple_tickers', self.test_multiple_tickers),
            ('response_structure', self.test_response_structure_validation),
            ('error_scenarios', self.test_error_scenarios),
            ('cors_functionality', self.test_cors_functionality),
            ('timestamp_accuracy', self.test_timestamp_accuracy)
        ]
        
        for category_name, test_method in test_categories:
            try:
                self.test_results['tests'][category_name] = test_method()
            except Exception as e:
                print(f"\n❌ Error running {category_name}: {str(e)}")
                self.test_results['tests'][category_name] = {
                    'test_name': category_name,
                    'error': str(e),
                    'success': False
                }
        
        # Generate final summary
        self._generate_final_summary()
        
        return self.test_results
    
    def _generate_final_summary(self):
        """Generate comprehensive final summary."""
        print(f"\n{'='*80}")
        print(f"FINAL VALIDATION SUMMARY")
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
            elif category_name == 'cors_functionality':
                category_passed = results.get('summary', {}).get('all_passed', False)
            elif category_name == 'timestamp_accuracy':
                category_passed = results.get('summary', {}).get('all_passed', False)
            
            if category_passed:
                passed_categories += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            print(f"{status} {category_name.replace('_', ' ').title()}")
        
        # Overall assessment
        success_rate = (passed_categories / total_categories) * 100
        overall_success = success_rate >= 80  # 80% threshold for passing
        
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
        
        # Requirements mapping
        print(f"\nRequirements Coverage:")
        requirements_map = {
            'multiple_tickers': ['1.1', '1.2'],
            'response_structure': ['1.6', '1.7', '1.8'],
            'error_scenarios': ['3.1', '3.2', '3.3', '3.4', '3.5'],
            'cors_functionality': ['2.6'],
            'timestamp_accuracy': ['1.7']
        }
        
        covered_requirements = set()
        for category, reqs in requirements_map.items():
            if self.test_results['tests'].get(category, {}).get('summary', {}).get('all_passed', False):
                covered_requirements.update(reqs)
        
        all_requirements = set(['1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8', '2.6', '3.1', '3.2', '3.3', '3.4', '3.5'])
        coverage_rate = (len(covered_requirements) / len(all_requirements)) * 100
        
        print(f"Requirements Covered: {len(covered_requirements)}/{len(all_requirements)} ({coverage_rate:.1f}%)")
        
        if coverage_rate < 80:
            print("⚠️  Some requirements may not be fully validated")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Final validation testing for Options Analytics API')
    parser.add_argument('--url', '-u', required=True, help='API base URL')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--output', '-o', help='Output file for detailed results (JSON)')
    
    args = parser.parse_args()
    
    # Create tester and run comprehensive validation
    tester = FinalValidationTester(args.url, timeout=args.timeout)
    results = tester.run_comprehensive_final_validation()
    
    # Save detailed results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {args.output}")
    
    # Exit with appropriate code
    if results['summary']['overall_success']:
        print(f"\n🎉 Final validation completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Final validation failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()