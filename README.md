# Options Analytics API

A serverless AWS Lambda API that provides comprehensive options analytics including implied volatility calculations, Greeks, and market data analysis.

## 🚀 Features

- **Real-time Options Data**: Fetches live options data from Yahoo Finance
- **Implied Volatility Calculations**: Advanced IV calculations using Newton-Raphson method
- **Greeks Analysis**: Delta, Gamma, Theta, Vega calculations
- **Multi-Expiration Support**: Analyzes options across multiple expiration dates
- **Comprehensive Filtering**: Filters out invalid or illiquid options
- **Performance Monitoring**: Built-in logging and performance metrics
- **Container Deployment**: Deployed as Docker container on AWS Lambda

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Node.js and npm (for Serverless Framework)
- Python 3.12

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sophie-lambda
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Serverless Framework**
   ```bash
   npm install -g serverless
   ```

4. **Install project dependencies**
   ```bash
   npm install
   ```

## 🐳 Docker Deployment

This project is configured for container-based deployment to AWS Lambda using Amazon ECR.

### Build and Deploy

1. **Build Docker image**
   ```bash
   docker buildx build --platform linux/amd64 --provenance=false -t 633690269460.dkr.ecr.us-east-1.amazonaws.com/options-analytics-api-dev:latest . --push
   ```

2. **Deploy to AWS Lambda**
   ```bash
   serverless deploy --stage dev --region us-east-1
   ```

### Architecture

- **Base Image**: AWS Lambda Python 3.12 runtime
- **Multi-stage Build**: Optimized for size and performance
- **Dependencies**: All Python packages installed in Lambda task root
- **Single Architecture**: Built specifically for linux/amd64

## 📡 API Usage

### Endpoint
```
GET https://whl064peuf.execute-api.us-east-1.amazonaws.com/options-analytics
```

### Parameters
- `ticker` (required): Stock symbol (e.g., SPY, AAPL, TSLA)

### Example Request
```bash
curl "https://whl064peuf.execute-api.us-east-1.amazonaws.com/options-analytics?ticker=SPY"
```

### Response Format
```json
{
  "ticker": "SPY",
  "underlying_price": 627.58,
  "expiration_dates": [
    {
      "date": "2024-01-19",
      "calls": [...],
      "puts": [...]
    }
  ]
}
```

## 🏗️ Project Structure

```
sophie-lambda/
├── src/
│   ├── models/
│   │   └── option_data.py          # Data models
│   ├── services/
│   │   ├── data_processor.py       # Data processing logic
│   │   ├── market_data_fetcher.py  # Market data fetching
│   │   ├── options_calculator.py   # IV and Greeks calculations
│   │   └── options_data_fetcher.py # Options data fetching
│   └── utils/
│       ├── data_formatter.py       # Response formatting
│       ├── error_handling.py       # Error handling utilities
│       ├── logging_utils.py        # Logging configuration
│       └── time_utils.py           # Time utilities
├── tests/                          # Unit tests
├── scripts/                        # Testing and validation scripts
├── handler.py                      # Lambda entry point
├── Dockerfile                      # Container configuration
├── serverless.yml                  # Serverless Framework config
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Tests
```bash
python scripts/integration_test.py
```

### Performance Tests
```bash
python scripts/performance_test.py
```

## 📊 Performance

- **Response Time**: ~4-5 seconds for typical requests
- **Memory Usage**: ~174 MB
- **Options Processed**: 5,000+ options per request
- **Expiration Dates**: 25+ dates analyzed

## 🔧 Configuration

### Environment Variables
- `LOG_LEVEL`: Logging level (default: INFO)
- `AWS_REGION`: AWS region (default: us-east-1)

### Serverless Configuration
- **Runtime**: Container image
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Region**: us-east-1

## 🚨 Troubleshooting

### Common Issues

1. **Service Unavailable (503)**
   - Usually temporary, retry the request
   - Check Lambda logs for detailed error information

2. **Timeout Errors**
   - Increase Lambda timeout in serverless.yml
   - Consider optimizing data processing

3. **Memory Issues**
   - Increase Lambda memory allocation
   - Check for memory leaks in data processing

### Logs
```bash
serverless logs -f optionsAnalytics --stage dev --region us-east-1 --tail
```

## 📈 Monitoring

The API includes comprehensive logging:
- Request/response metrics
- Performance timing
- Error tracking
- Data processing statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Lambda logs
3. Open an issue in the repository