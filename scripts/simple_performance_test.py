#!/usr/bin/env python3
"""
Simple performance test for local handler validation.
"""

import sys
import time
import os
from statistics import mean, median
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the handler
from handler import get_options_analytics


def create_mock_event(ticker: str = "SPY"):
    """Create a mock API Gateway event."""
    return {
        'httpMethod': 'GET',
        'path': '/options-analytics',
        'queryStringParameters': {'ticker': ticker} if ticker else None,
        'headers': {
            'Accept': 'application/json',
            'User-Agent': 'PerformanceTest/1.0'
        },
        'requestContext': {
            'requestId': f'perf-test-{int(time.time())}'
        }
    }


def create_mock_context():
    """Create a mock Lambda context."""
    class MockContext:
        def __init__(self):
            self.function_name = 'options-analytics-perf-test'
            self.function_version = '$LATEST'
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:options-analytics-perf-test'
            self.memory_limit_in_mb = '512'
            self.remaining_time_in_millis = lambda: 30000
            self.log_group_name = '/aws/lambda/options-analytics-perf-test'
            self.log_stream_name = '2025/01/16/[$LATEST]perf-test'
            self.aws_request_id = f'perf-test-{int(time.time())}'
    
    return MockContext()


def run_performance_test(num_requests: int = 5, tickers: list = None):
    """Run performance test with multiple requests."""
    if tickers is None:
        tickers = ["SPY", "AAPL", "MSFT"]
    
    print(f"\n🚀 Performance Test - {num_requests} requests per ticker")
    print(f"Testing tickers: {', '.join(tickers)}")
    print("=" * 60)
    
    all_results = []
    
    for ticker in tickers:
        print(f"\nTesting {ticker}...")
        ticker_results = []
        
        for i in range(num_requests):
            print(f"  Request {i+1}/{num_requests}...", end=" ")
            
            event = create_mock_event(ticker)
            context = create_mock_context()
            
            start_time = time.time()
            
            try:
                response = get_options_analytics(event, context)
                execution_time = time.time() - start_time
                
                success = response.get('statusCode') == 200
                response_size = len(response.get('body', ''))
                
                ticker_results.append({
                    'ticker': ticker,
                    'execution_time': execution_time,
                    'success': success,
                    'response_size': response_size,
                    'status_code': response.get('statusCode')
                })
                
                if success:
                    print(f"✅ {execution_time:.3f}s ({response_size:,} bytes)")
                else:
                    print(f"❌ Failed (Status: {response.get('statusCode')})")
                
            except Exception as e:
                execution_time = time.time() - start_time
                ticker_results.append({
                    'ticker': ticker,
                    'execution_time': execution_time,
                    'success': False,
                    'error': str(e),
                    'response_size': 0,
                    'status_code': 0
                })
                print(f"❌ Error: {str(e)}")
        
        # Calculate ticker statistics
        successful_requests = [r for r in ticker_results if r['success']]
        if successful_requests:
            execution_times = [r['execution_time'] for r in successful_requests]
            response_sizes = [r['response_size'] for r in successful_requests]
            
            print(f"\n  📊 {ticker} Statistics:")
            print(f"    Success Rate: {len(successful_requests)}/{num_requests} ({len(successful_requests)/num_requests*100:.1f}%)")
            print(f"    Avg Execution Time: {mean(execution_times):.3f}s")
            print(f"    Min Execution Time: {min(execution_times):.3f}s")
            print(f"    Max Execution Time: {max(execution_times):.3f}s")
            print(f"    Median Execution Time: {median(execution_times):.3f}s")
            print(f"    Avg Response Size: {mean(response_sizes):,.0f} bytes")
        
        all_results.extend(ticker_results)
    
    # Overall statistics
    print(f"\n{'='*60}")
    print(f"OVERALL PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    
    total_requests = len(all_results)
    successful_requests = [r for r in all_results if r['success']]
    success_rate = len(successful_requests) / total_requests * 100
    
    print(f"Total Requests: {total_requests}")
    print(f"Successful Requests: {len(successful_requests)}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if successful_requests:
        execution_times = [r['execution_time'] for r in successful_requests]
        response_sizes = [r['response_size'] for r in successful_requests]
        
        print(f"\nExecution Time Statistics:")
        print(f"  Average: {mean(execution_times):.3f}s")
        print(f"  Minimum: {min(execution_times):.3f}s")
        print(f"  Maximum: {max(execution_times):.3f}s")
        print(f"  Median: {median(execution_times):.3f}s")
        
        print(f"\nResponse Size Statistics:")
        print(f"  Average: {mean(response_sizes):,.0f} bytes")
        print(f"  Minimum: {min(response_sizes):,} bytes")
        print(f"  Maximum: {max(response_sizes):,} bytes")
        
        # Performance assessment
        avg_time = mean(execution_times)
        if avg_time < 5.0:
            print(f"\n✅ Performance: EXCELLENT (< 5s average)")
        elif avg_time < 10.0:
            print(f"\n✅ Performance: GOOD (< 10s average)")
        elif avg_time < 20.0:
            print(f"\n⚠️  Performance: ACCEPTABLE (< 20s average)")
        else:
            print(f"\n❌ Performance: POOR (> 20s average)")
        
        # Lambda timeout check (30s default)
        max_time = max(execution_times)
        if max_time > 25.0:
            print(f"⚠️  WARNING: Max execution time ({max_time:.3f}s) is close to Lambda timeout")
        
        return success_rate >= 80 and avg_time < 20.0
    else:
        print(f"\n❌ No successful requests to analyze")
        return False


def main():
    """Main function."""
    print("🧪 Starting Simple Performance Test")
    
    try:
        success = run_performance_test(num_requests=3, tickers=["SPY", "AAPL"])
        
        if success:
            print(f"\n🎉 Performance test PASSED!")
            sys.exit(0)
        else:
            print(f"\n💥 Performance test FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Fatal error during performance test: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()