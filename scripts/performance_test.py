#!/usr/bin/env python3
"""
Performance testing script for Options Analytics API.
Measures Lambda execution time, memory usage, and throughput.
"""

import json
import sys
import time
import statistics
import concurrent.futures
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    response_time: float
    status_code: int
    response_size: int
    success: bool
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


class PerformanceTester:
    """Performance testing framework for Options Analytics API."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the performance tester.
        
        Args:
            base_url: Base URL of the deployed API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'OptionsAnalytics-PerformanceTest/1.0',
            'Accept': 'application/json'
        })
    
    def make_single_request(self, ticker: str = "SPY") -> PerformanceMetrics:
        """
        Make a single request and measure performance.
        
        Args:
            ticker: Ticker symbol to request
            
        Returns:
            PerformanceMetrics object
        """
        url = f"{self.base_url}/options-analytics?ticker={ticker}"
        start_time = time.time()
        timestamp = datetime.now()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            return PerformanceMetrics(
                response_time=response_time,
                status_code=response.status_code,
                response_size=len(response.content),
                success=response.status_code == 200,
                timestamp=timestamp
            )
            
        except requests.exceptions.Timeout:
            return PerformanceMetrics(
                response_time=time.time() - start_time,
                status_code=0,
                response_size=0,
                success=False,
                error="Timeout",
                timestamp=timestamp
            )
        except Exception as e:
            return PerformanceMetrics(
                response_time=time.time() - start_time,
                status_code=0,
                response_size=0,
                success=False,
                error=str(e),
                timestamp=timestamp
            )
    
    def run_sequential_test(self, num_requests: int = 10, ticker: str = "SPY", 
                          verbose: bool = True) -> Dict[str, Any]:
        """
        Run sequential performance test.
        
        Args:
            num_requests: Number of requests to make
            ticker: Ticker symbol to test
            verbose: Whether to print progress
            
        Returns:
            Performance test results
        """
        if verbose:
            print(f"\n🔄 Running Sequential Performance Test")
            print(f"Requests: {num_requests}, Ticker: {ticker}")
            print(f"{'='*50}")
        
        metrics = []
        start_time = time.time()
        
        for i in range(num_requests):
            if verbose:
                print(f"Request {i+1:3d}/{num_requests}...", end=' ')
            
            metric = self.make_single_request(ticker)
            metrics.append(metric)
            
            if verbose:
                if metric.success:
                    print(f"✅ {metric.response_time:.3f}s ({metric.response_size:,} bytes)")
                else:
                    print(f"❌ {metric.error or 'Failed'}")
        
        total_time = time.time() - start_time
        
        return self._analyze_metrics(metrics, total_time, "Sequential")
    
    def run_concurrent_test(self, num_requests: int = 10, max_workers: int = 5, 
                          ticker: str = "SPY", verbose: bool = True) -> Dict[str, Any]:
        """
        Run concurrent performance test.
        
        Args:
            num_requests: Number of requests to make
            max_workers: Maximum number of concurrent workers
            ticker: Ticker symbol to test
            verbose: Whether to print progress
            
        Returns:
            Performance test results
        """
        if verbose:
            print(f"\n⚡ Running Concurrent Performance Test")
            print(f"Requests: {num_requests}, Workers: {max_workers}, Ticker: {ticker}")
            print(f"{'='*50}")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            futures = [executor.submit(self.make_single_request, ticker) for _ in range(num_requests)]
            
            # Collect results
            metrics = []
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                metric = future.result()
                metrics.append(metric)
                
                if verbose:
                    if metric.success:
                        print(f"Request {i+1:3d} completed: ✅ {metric.response_time:.3f}s")
                    else:
                        print(f"Request {i+1:3d} completed: ❌ {metric.error or 'Failed'}")
        
        total_time = time.time() - start_time
        
        return self._analyze_metrics(metrics, total_time, "Concurrent")
    
    def run_load_test(self, duration_seconds: int = 60, requests_per_second: int = 2, 
                     ticker: str = "SPY", verbose: bool = True) -> Dict[str, Any]:
        """
        Run load test for specified duration.
        
        Args:
            duration_seconds: Test duration in seconds
            requests_per_second: Target requests per second
            ticker: Ticker symbol to test
            verbose: Whether to print progress
            
        Returns:
            Load test results
        """
        if verbose:
            print(f"\n🏋️  Running Load Test")
            print(f"Duration: {duration_seconds}s, Target RPS: {requests_per_second}, Ticker: {ticker}")
            print(f"{'='*50}")
        
        metrics = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        request_interval = 1.0 / requests_per_second
        
        request_count = 0
        next_request_time = start_time
        
        while time.time() < end_time:
            current_time = time.time()
            
            if current_time >= next_request_time:
                metric = self.make_single_request(ticker)
                metrics.append(metric)
                request_count += 1
                
                if verbose and request_count % 10 == 0:
                    elapsed = current_time - start_time
                    actual_rps = request_count / elapsed if elapsed > 0 else 0
                    print(f"Requests: {request_count:3d}, Elapsed: {elapsed:.1f}s, RPS: {actual_rps:.2f}")
                
                next_request_time += request_interval
            else:
                # Sleep for a short time to avoid busy waiting
                time.sleep(min(0.01, next_request_time - current_time))
        
        total_time = time.time() - start_time
        
        result = self._analyze_metrics(metrics, total_time, "Load Test")
        result['target_rps'] = requests_per_second
        result['actual_rps'] = len(metrics) / total_time if total_time > 0 else 0
        result['duration'] = duration_seconds
        
        return result
    
    def run_cold_start_test(self, num_tests: int = 5, wait_time: int = 300, 
                          ticker: str = "SPY", verbose: bool = True) -> Dict[str, Any]:
        """
        Test Lambda cold start performance.
        
        Args:
            num_tests: Number of cold start tests to run
            wait_time: Time to wait between tests (seconds)
            ticker: Ticker symbol to test
            verbose: Whether to print progress
            
        Returns:
            Cold start test results
        """
        if verbose:
            print(f"\n🥶 Running Cold Start Test")
            print(f"Tests: {num_tests}, Wait time: {wait_time}s, Ticker: {ticker}")
            print(f"{'='*50}")
        
        cold_start_metrics = []
        warm_metrics = []
        
        for i in range(num_tests):
            if verbose:
                print(f"\nCold Start Test {i+1}/{num_tests}")
            
            # Wait for Lambda to go cold
            if i > 0:
                if verbose:
                    print(f"Waiting {wait_time}s for Lambda to go cold...")
                time.sleep(wait_time)
            
            # Make cold start request
            if verbose:
                print("Making cold start request...", end=' ')
            cold_metric = self.make_single_request(ticker)
            cold_start_metrics.append(cold_metric)
            
            if verbose:
                if cold_metric.success:
                    print(f"✅ {cold_metric.response_time:.3f}s")
                else:
                    print(f"❌ {cold_metric.error or 'Failed'}")
            
            # Make warm requests immediately after
            if verbose:
                print("Making warm requests...", end=' ')
            
            warm_requests = []
            for j in range(3):  # 3 warm requests
                warm_metric = self.make_single_request(ticker)
                warm_requests.append(warm_metric)
                time.sleep(0.1)  # Small delay between requests
            
            warm_metrics.extend(warm_requests)
            
            if verbose:
                avg_warm_time = statistics.mean([m.response_time for m in warm_requests if m.success])
                successful_warm = sum(1 for m in warm_requests if m.success)
                print(f"✅ {successful_warm}/3 successful, avg: {avg_warm_time:.3f}s")
        
        # Analyze results
        successful_cold = [m for m in cold_start_metrics if m.success]
        successful_warm = [m for m in warm_metrics if m.success]
        
        results = {
            'test_type': 'Cold Start',
            'num_tests': num_tests,
            'wait_time': wait_time,
            'cold_start_requests': len(cold_start_metrics),
            'warm_requests': len(warm_metrics),
            'cold_start_success_rate': len(successful_cold) / len(cold_start_metrics) * 100 if cold_start_metrics else 0,
            'warm_success_rate': len(successful_warm) / len(warm_metrics) * 100 if warm_metrics else 0
        }
        
        if successful_cold:
            cold_times = [m.response_time for m in successful_cold]
            results['cold_start_stats'] = {
                'mean': statistics.mean(cold_times),
                'median': statistics.median(cold_times),
                'min': min(cold_times),
                'max': max(cold_times),
                'stdev': statistics.stdev(cold_times) if len(cold_times) > 1 else 0
            }
        
        if successful_warm:
            warm_times = [m.response_time for m in successful_warm]
            results['warm_stats'] = {
                'mean': statistics.mean(warm_times),
                'median': statistics.median(warm_times),
                'min': min(warm_times),
                'max': max(warm_times),
                'stdev': statistics.stdev(warm_times) if len(warm_times) > 1 else 0
            }
        
        if successful_cold and successful_warm:
            results['cold_vs_warm_ratio'] = results['cold_start_stats']['mean'] / results['warm_stats']['mean']
        
        return results
    
    def _analyze_metrics(self, metrics: List[PerformanceMetrics], total_time: float, 
                        test_type: str) -> Dict[str, Any]:
        """
        Analyze performance metrics and generate report.
        
        Args:
            metrics: List of performance metrics
            total_time: Total test execution time
            test_type: Type of test performed
            
        Returns:
            Analysis results
        """
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        
        results = {
            'test_type': test_type,
            'total_requests': len(metrics),
            'successful_requests': len(successful_metrics),
            'failed_requests': len(failed_metrics),
            'success_rate': len(successful_metrics) / len(metrics) * 100 if metrics else 0,
            'total_time': total_time,
            'requests_per_second': len(metrics) / total_time if total_time > 0 else 0
        }
        
        if successful_metrics:
            response_times = [m.response_time for m in successful_metrics]
            response_sizes = [m.response_size for m in successful_metrics]
            
            results['response_time_stats'] = {
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'p95': self._percentile(response_times, 95),
                'p99': self._percentile(response_times, 99),
                'stdev': statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
            
            results['response_size_stats'] = {
                'mean': statistics.mean(response_sizes),
                'median': statistics.median(response_sizes),
                'min': min(response_sizes),
                'max': max(response_sizes)
            }
        
        if failed_metrics:
            error_counts = {}
            for metric in failed_metrics:
                error = metric.error or 'Unknown'
                error_counts[error] = error_counts.get(error, 0) + 1
            results['error_breakdown'] = error_counts
        
        return results
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def print_performance_report(self, results: Dict[str, Any]):
        """Print formatted performance report."""
        print(f"\n📊 {results['test_type']} Performance Report")
        print(f"{'='*60}")
        
        # Basic stats
        print(f"Total Requests: {results['total_requests']}")
        print(f"Successful: {results['successful_requests']}")
        print(f"Failed: {results['failed_requests']}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Total Time: {results['total_time']:.3f}s")
        print(f"Requests/Second: {results['requests_per_second']:.2f}")
        
        # Response time stats
        if 'response_time_stats' in results:
            stats = results['response_time_stats']
            print(f"\nResponse Time Statistics:")
            print(f"  Mean: {stats['mean']:.3f}s")
            print(f"  Median: {stats['median']:.3f}s")
            print(f"  Min: {stats['min']:.3f}s")
            print(f"  Max: {stats['max']:.3f}s")
            print(f"  95th Percentile: {stats['p95']:.3f}s")
            print(f"  99th Percentile: {stats['p99']:.3f}s")
            print(f"  Std Dev: {stats['stdev']:.3f}s")
        
        # Response size stats
        if 'response_size_stats' in results:
            stats = results['response_size_stats']
            print(f"\nResponse Size Statistics:")
            print(f"  Mean: {stats['mean']:,.0f} bytes")
            print(f"  Median: {stats['median']:,.0f} bytes")
            print(f"  Min: {stats['min']:,} bytes")
            print(f"  Max: {stats['max']:,} bytes")
        
        # Load test specific
        if 'target_rps' in results:
            print(f"\nLoad Test Metrics:")
            print(f"  Target RPS: {results['target_rps']:.2f}")
            print(f"  Actual RPS: {results['actual_rps']:.2f}")
            print(f"  Duration: {results['duration']}s")
        
        # Cold start specific
        if 'cold_start_stats' in results:
            cold_stats = results['cold_start_stats']
            warm_stats = results.get('warm_stats', {})
            
            print(f"\nCold Start Statistics:")
            print(f"  Mean: {cold_stats['mean']:.3f}s")
            print(f"  Median: {cold_stats['median']:.3f}s")
            print(f"  Min: {cold_stats['min']:.3f}s")
            print(f"  Max: {cold_stats['max']:.3f}s")
            
            if warm_stats:
                print(f"\nWarm Request Statistics:")
                print(f"  Mean: {warm_stats['mean']:.3f}s")
                print(f"  Median: {warm_stats['median']:.3f}s")
                
                if 'cold_vs_warm_ratio' in results:
                    print(f"\nCold vs Warm Ratio: {results['cold_vs_warm_ratio']:.2f}x")
        
        # Error breakdown
        if 'error_breakdown' in results:
            print(f"\nError Breakdown:")
            for error, count in results['error_breakdown'].items():
                print(f"  {error}: {count}")
        
        # Performance assessment
        print(f"\n🎯 Performance Assessment:")
        
        if results['success_rate'] >= 95:
            print("  ✅ Reliability: Excellent")
        elif results['success_rate'] >= 90:
            print("  ⚠️  Reliability: Good")
        else:
            print("  ❌ Reliability: Poor")
        
        if 'response_time_stats' in results:
            mean_time = results['response_time_stats']['mean']
            if mean_time <= 2.0:
                print("  ✅ Response Time: Excellent")
            elif mean_time <= 5.0:
                print("  ⚠️  Response Time: Good")
            else:
                print("  ❌ Response Time: Poor")
        
        if results.get('requests_per_second', 0) >= 1.0:
            print("  ✅ Throughput: Good")
        else:
            print("  ⚠️  Throughput: Limited")


def get_api_endpoint_from_serverless(stage: str = "dev", region: str = "us-east-1") -> Optional[str]:
    """Get API endpoint URL from serverless info command."""
    import subprocess
    
    try:
        result = subprocess.run(
            ['serverless', 'info', '--stage', stage, '--region', region],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GET - ' in line and '/options-analytics' in line:
                    parts = line.split('GET - ')
                    if len(parts) > 1:
                        url = parts[1].strip()
                        if '/options-analytics' in url:
                            base_url = url.replace('/options-analytics', '')
                            return base_url
        
        return None
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return None


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Performance testing for Options Analytics API')
    parser.add_argument('--url', '-u', help='API base URL')
    parser.add_argument('--stage', '-s', default='dev', help='Deployment stage')
    parser.add_argument('--region', '-r', default='us-east-1', help='AWS region')
    parser.add_argument('--ticker', '-t', default='SPY', help='Ticker symbol to test')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    
    # Test type options
    parser.add_argument('--sequential', type=int, help='Run sequential test with N requests')
    parser.add_argument('--concurrent', type=int, help='Run concurrent test with N requests')
    parser.add_argument('--workers', type=int, default=5, help='Number of concurrent workers')
    parser.add_argument('--load', type=int, help='Run load test for N seconds')
    parser.add_argument('--rps', type=int, default=2, help='Target requests per second for load test')
    parser.add_argument('--cold-start', type=int, help='Run cold start test N times')
    parser.add_argument('--wait', type=int, default=300, help='Wait time between cold start tests')
    parser.add_argument('--all', action='store_true', help='Run all performance tests')
    
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
    tester = PerformanceTester(base_url, timeout=args.timeout)
    
    # Run tests based on arguments
    if args.all:
        # Run all tests
        print(f"🚀 Running Complete Performance Test Suite")
        print(f"API: {base_url}")
        print(f"Ticker: {args.ticker}")
        
        # Sequential test
        seq_results = tester.run_sequential_test(10, args.ticker)
        tester.print_performance_report(seq_results)
        
        # Concurrent test
        conc_results = tester.run_concurrent_test(10, args.workers, args.ticker)
        tester.print_performance_report(conc_results)
        
        # Load test
        load_results = tester.run_load_test(30, args.rps, args.ticker)
        tester.print_performance_report(load_results)
        
        # Cold start test
        cold_results = tester.run_cold_start_test(3, 180, args.ticker)  # Shorter wait for demo
        tester.print_performance_report(cold_results)
        
    elif args.sequential:
        results = tester.run_sequential_test(args.sequential, args.ticker)
        tester.print_performance_report(results)
        
    elif args.concurrent:
        results = tester.run_concurrent_test(args.concurrent, args.workers, args.ticker)
        tester.print_performance_report(results)
        
    elif args.load:
        results = tester.run_load_test(args.load, args.rps, args.ticker)
        tester.print_performance_report(results)
        
    elif args.cold_start:
        results = tester.run_cold_start_test(args.cold_start, args.wait, args.ticker)
        tester.print_performance_report(results)
        
    else:
        # Default: run a quick performance test
        print("Running default performance test (10 sequential requests)")
        results = tester.run_sequential_test(10, args.ticker)
        tester.print_performance_report(results)


if __name__ == '__main__':
    main()