# Options Analytics API

A serverless backend built with AWS Lambda and API Gateway that provides real-time options analytics including implied volatility calculations and Greeks for any ticker symbol.

## Features

- Fetch option chain data for any ticker
- Calculate implied volatility using Black-Scholes model
- Calculate option Greeks (Delta)
- Retrieve current VIX data
- RESTful API with CORS support
- Serverless architecture for cost efficiency

## API Endpoint

```
GET /options-analytics?ticker=SYMBOL
```

### Parameters
- `ticker` (optional): Stock ticker symbol (defaults to "SPY")

### Response Format
```json
{
  "ticker": "SPY",
  "stockPrice": 450.25,
  "vixValue": 18.75,
  "dataTimestamp": "2025-01-16T14:30:00Z",
  "vixTimestamp": "2025-01-16T14:30:00Z",
  "expirationDates": [
    {
      "expiration": "2025-01-17",
      "calls": [...],
      "puts": [...]
    }
  ]
}
```

## Development

### Prerequisites
- Python 3.9+
- Node.js (for Serverless Framework)
- AWS CLI configured

### Installation
```bash
# Install Python dependencies
pip install -e .

# Install Serverless Framework
npm install -g serverless
npm install serverless-python-requirements

# Install development dependencies
pip install -e ".[dev]"
```

### Testing
```bash
pytest
```

### Deployment
```bash
serverless deploy
```

## Architecture

The system uses:
- **AWS Lambda**: Serverless compute for the API logic
- **API Gateway**: RESTful endpoint with CORS
- **Yahoo Finance API**: Market data source
- **py_vollib**: Options calculations library

## Project Structure

```
.
├── handler.py              # Main Lambda handler
├── src/
│   ├── models/            # Data models
│   └── services/          # Business logic services
├── tests/                 # Unit and integration tests
├── serverless.yml         # Serverless Framework configuration
├── pyproject.toml         # Python project configuration
└── requirements.txt       # Lambda dependencies
```