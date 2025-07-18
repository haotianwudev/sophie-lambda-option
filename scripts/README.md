# Deployment and Testing Scripts

This directory contains scripts for deploying and testing the Options Analytics API. These scripts provide comprehensive testing capabilities including local testing with sample data, integration testing of deployed APIs, and performance testing for Lambda execution time.

## Scripts Overview

### 1. Deployment Script (`deploy.sh`)
Enhanced deployment script with comprehensive error checking and validation.

### 2. Local Testing (`local_test.py`)
Local testing capabilities with sample data and mock responses.

### 3. Integration Testing (`integration_test.py`)
Integration testing for deployed API endpoints with real HTTP requests.

### 4. Performance Testing (`performance_test.py`)
Performance testing for Lambda execution time, memory usage, and throughput.

## Prerequisites

- **AWS CLI**: Configured with appropriate credentials
- **Node.js**: Version 14+ for Serverless Framework
- **Python**: Version 3.9+ with required packages
- **Serverless Framework**: Installed globally or locally

## Quick Start

### Deploy the API
```bash
# Basic deployment to dev stage
./deploy.sh

# Deploy to specific stage and region
./deploy.sh prod us-west-2

# Dry run to see what would be deployed
./deploy.sh dev us-east-1 --dry-run

# Verbose deployment with detailed output
./deploy.sh dev us-east-1 --verbose
```

### Test Locally
```bash
# Test single ticker with sample data
python3 scripts/local_test.py --ticker SPY

# Run full test suite
python3 scripts/local_test.py --suite

# Test with real data (requires internet)
python3 scripts/local_test.py --real-data --ticker AAPL

# Using npm scripts
npm run test-local
npm run test-local-suite
```

### Integration Testing
```bash
# Test deployed API (auto-detects endpoint)
python3 scripts/integration_test.py

# Test specific endpoint
python3 scripts/integration_test.py --url https://api.example.com

# Test specific ticker
python3 scripts/integration_test.py --ticker AAPL

# Test multiple tickers
python3 scripts/integration_test.py --tickers SPY AAPL MSFT

# Using npm scripts
npm run test-integration
```

### Performance Testing
```bash
# Quick performance test
python3 scripts/performance_test.py

# Sequential test with 20 requests
python3 scripts/performance_test.py --sequential 20

# Concurrent test with 10 requests and 5 workers
python3 scripts/performance_test.py --concurrent 10 --workers 5

# Load test for 60 seconds at 2 RPS
python3 scripts/performance_test.py --load 60 --rps 2

# Cold start test (3 iterations)
python3 scripts/performance_test.py --cold-start 3

# Run all performance tests
python3 scripts/performance_test.py --all

# Using npm scripts
npm run test-performance
npm run test-performance-all
npm run test-cold-start
```

## Detailed Usage

### Deployment Script (`deploy.sh`)

The deployment script provides comprehensive deployment capabilities with error checking and validation.

**Features:**
- Prerequisites checking (AWS CLI, Node.js, Python, Serverless)
- Automatic dependency installation
- Pre-deployment testing
- Dry-run capability
- Verbose output option
- Post-deployment validation

**Usage:**
```bash
./deploy.sh [stage] [region] [options]

Options:
  --verbose   Enable verbose output
  --dry-run   Show what would be deployed without actually deploying
  --help      Show help message

Examples:
  ./deploy.sh                           # Deploy to dev/us-east-1
  ./deploy.sh prod us-west-2           # Deploy to prod/us-west-2
  ./deploy.sh dev us-east-1 --verbose # Verbose deployment
  ./deploy.sh dev us-east-1 --dry-run  # Dry run
```

### Local Testing (`local_test.py`)

Local testing framework that can use either sample data or real API calls.

**Features:**
- Sample data generation for offline testing
- Real data testing with internet connection
- Multiple ticker testing
- Response validation
- Performance measurement
- Comprehensive test suite

**Usage:**
```bash
python3 scripts/local_test.py [options]

Options:
  --ticker, -t TICKER    Ticker symbol to test (default: SPY)
  --real-data, -r        Use real data instead of sample data
  --verbose, -v          Enable verbose output
  --suite, -s            Run full test suite
  --tickers TICKER...    List of tickers for test suite

Examples:
  python3 scripts/local_test.py --ticker AAPL
  python3 scripts/local_test.py --suite --verbose
  python3 scripts/local_test.py --real-data --ticker SPY
  python3 scripts/local_test.py --suite --tickers SPY AAPL MSFT
```

### Integration Testing (`integration_test.py`)

Integration testing framework for deployed APIs with comprehensive validation.

**Features:**
- Automatic endpoint discovery from Serverless
- Response structure validation
- CORS header testing
- Error handling validation
- Performance measurement
- Comprehensive test suite

**Usage:**
```bash
python3 scripts/integration_test.py [options]

Options:
  --url, -u URL          API base URL
  --stage, -s STAGE      Deployment stage (default: dev)
  --region, -r REGION    AWS region (default: us-east-1)
  --ticker, -t TICKER    Single ticker to test
  --tickers TICKER...    List of tickers for test suite
  --timeout SECONDS      Request timeout (default: 30)
  --verbose, -v          Enable verbose output

Examples:
  python3 scripts/integration_test.py
  python3 scripts/integration_test.py --ticker AAPL
  python3 scripts/integration_test.py --tickers SPY AAPL MSFT
  python3 scripts/integration_test.py --url https://api.example.com
```

### Performance Testing (`performance_test.py`)

Comprehensive performance testing framework for Lambda execution time and throughput.

**Features:**
- Sequential performance testing
- Concurrent load testing
- Sustained load testing
- Cold start performance testing
- Detailed performance metrics
- Statistical analysis

**Usage:**
```bash
python3 scripts/performance_test.py [options]

Options:
  --url, -u URL          API base URL
  --stage, -s STAGE      Deployment stage (default: dev)
  --region, -r REGION    AWS region (default: us-east-1)
  --ticker, -t TICKER    Ticker symbol to test (default: SPY)
  --timeout SECONDS      Request timeout (default: 30)

Test Types:
  --sequential N         Run sequential test with N requests
  --concurrent N         Run concurrent test with N requests
  --workers N            Number of concurrent workers (default: 5)
  --load N               Run load test for N seconds
  --rps N                Target requests per second (default: 2)
  --cold-start N         Run cold start test N times
  --wait N               Wait time between cold start tests (default: 300)
  --all                  Run all performance tests

Examples:
  python3 scripts/performance_test.py --sequential 20
  python3 scripts/performance_test.py --concurrent 10 --workers 5
  python3 scripts/performance_test.py --load 60 --rps 2
  python3 scripts/performance_test.py --cold-start 5 --wait 180
  python3 scripts/performance_test.py --all
```

## Test Results and Metrics

### Local Testing Results
- Response validation
- Data structure verification
- Performance timing
- Error handling validation

### Integration Testing Results
- HTTP status codes
- Response structure validation
- CORS header verification
- Error handling testing
- Performance metrics

### Performance Testing Results
- Response time statistics (mean, median, percentiles)
- Throughput metrics (requests per second)
- Success/failure rates
- Cold start vs warm request comparison
- Memory usage indicators
- Error breakdown

## Performance Benchmarks

### Expected Performance Targets
- **Response Time**: < 5 seconds average
- **Success Rate**: > 95%
- **Cold Start**: < 10 seconds
- **Warm Requests**: < 3 seconds
- **Throughput**: > 1 request/second

### Performance Assessment Criteria
- **Excellent**: Response time ≤ 2s, Success rate ≥ 95%
- **Good**: Response time ≤ 5s, Success rate ≥ 90%
- **Poor**: Response time > 5s, Success rate < 90%

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Configured**
   ```bash
   aws configure
   # or set environment variables
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

2. **Serverless Framework Not Found**
   ```bash
   npm install -g serverless
   ```

3. **Python Dependencies Missing**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **API Endpoint Not Found**
   - Ensure the service is deployed
   - Check the stage and region parameters
   - Verify serverless info output

5. **High Response Times**
   - Check Lambda memory allocation (512MB recommended)
   - Verify timeout settings (30s recommended)
   - Monitor CloudWatch logs for errors

6. **Cold Start Issues**
   - Consider increasing memory allocation
   - Implement Lambda warming strategies
   - Monitor cold start frequency

### Debug Commands

```bash
# Check deployment status
serverless info --stage dev --region us-east-1

# View Lambda logs
serverless logs -f optionsAnalytics --stage dev --tail

# Test Lambda function directly
serverless invoke -f optionsAnalytics --stage dev --data '{"httpMethod":"GET","path":"/options-analytics","queryStringParameters":{"ticker":"SPY"}}'

# Check AWS credentials
aws sts get-caller-identity

# Validate serverless configuration
serverless print --stage dev
```

## CI/CD Integration

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Deploy API
  run: ./deploy.sh ${{ env.STAGE }} ${{ env.REGION }}

- name: Run Integration Tests
  run: python3 scripts/integration_test.py --stage ${{ env.STAGE }}

- name: Run Performance Tests
  run: python3 scripts/performance_test.py --sequential 10
```

## Monitoring and Alerting

After deployment, monitor the API using:
- AWS CloudWatch metrics
- Lambda execution logs
- API Gateway access logs
- Custom performance dashboards

Set up alerts for:
- High error rates (>5%)
- Long response times (>10s)
- Memory usage warnings
- Cold start frequency

## Best Practices

1. **Testing Strategy**
   - Run local tests during development
   - Use integration tests for deployment validation
   - Perform performance tests before production

2. **Deployment Strategy**
   - Use dry-run for validation
   - Deploy to staging before production
   - Monitor metrics after deployment

3. **Performance Optimization**
   - Monitor cold start frequency
   - Optimize Lambda memory allocation
   - Implement appropriate timeout values
   - Use performance test results for tuning

4. **Error Handling**
   - Test error scenarios regularly
   - Monitor error rates and types
   - Implement proper retry strategies
   - Log errors for debugging