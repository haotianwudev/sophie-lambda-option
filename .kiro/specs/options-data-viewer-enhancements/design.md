# Design Document: Options Data API Enhancements

## Overview

This design document outlines the enhancements to the Options Data API handler to provide more comprehensive market data and analytics. The enhancements include adding stock and VIX price information with percentage changes, restructuring timestamp data, filtering options by specific expiration dates, adding more option data fields, calculating moneyness, and enhancing implied volatility calculations based on different price points.

The API will continue to be implemented as an AWS Lambda function, accessible via API Gateway, and will maintain backward compatibility with existing clients while providing enhanced data.

## Architecture

The enhanced Options Data API will maintain the existing serverless architecture:

1. **Client Request**: Clients make HTTP requests to the API Gateway endpoint
2. **API Gateway**: Routes the request to the Lambda function
3. **Lambda Function**: Processes the request, fetches market data, performs calculations, and returns the response
4. **Market Data Services**: External services used to fetch stock, options, and VIX data

The enhancements will primarily affect the data processing and response formatting components of the Lambda function, without changing the overall architecture.

## Components and Interfaces

### Enhanced Response Structure

The API response JSON structure will be enhanced as follows:

```json
{
  "ticker": "SPY",
  "stock": {
    "price": 627.58,
    "previousClose": 625.12,
    "percentChange": 0.39,
    "timestamp": "2025-07-19T00:17:06.058378Z"
  },
  "vix": {
    "value": 16.41,
    "previousClose": 16.85,
    "percentChange": -2.61,
    "timestamp": "2025-07-19T00:17:06.224920Z"
  },
  "expirationDates": [
    {
      "expiration": "2025-08-01",
      "daysToExpiration": 14,
      "expirationLabel": "2w",
      "calls": [
        {
          "contractSymbol": "SPY250801C00600000",
          "lastTradeDate": "2025-07-18T19:45:22Z",
          "strike": 600.0,
          "lastPrice": 30.25,
          "bid": 29.85,
          "ask": 30.65,
          "midPrice": 30.25,
          "volume": 1245,
          "openInterest": 3856,
          "moneyness": 0.955,
          "impliedVolatilityYF": 0.190,  // Original implied volatility from yfinance
          "impliedVolatilityBid": 0.182,
          "impliedVolatilityMid": 0.187,
          "impliedVolatilityAsk": 0.193,
          "delta": 0.65
        },
        // Additional call options...
      ],
      "puts": [
        // Put options with the same structure...
      ]
    },
    // Additional expiration dates (1m, 6w, 2m)...
  ]
}
```

### Market Data Service Integration

The existing market data fetching components will be enhanced to:

1. Fetch previous closing prices for the stock
2. Fetch previous VIX values
3. Calculate percentage changes

### Option Data Processing

The option data processing will be enhanced to:

1. Calculate moneyness for each option
2. Filter options by moneyness range (0.85 to 1.15)
3. Calculate implied volatility based on bid, mid, and ask prices
4. Select specific expiration dates (2w, 1m, 6w, 2m)

## Data Models

### Enhanced Stock Data Model

```typescript
interface StockData {
  price: number;
  previousClose: number;
  percentChange: number;
  timestamp: string;
}
```

### Enhanced VIX Data Model

```typescript
interface VixData {
  value: number;
  previousClose: number;
  percentChange: number;
  timestamp: string;
}
```

### Enhanced Option Data Model

```typescript
interface OptionData {
  contractSymbol: string;
  lastTradeDate: string;
  strike: number;
  lastPrice: number;
  bid: number;
  ask: number;
  midPrice: number;
  volume: number;
  openInterest: number;
  moneyness: number;
  impliedVolatilityYF: number;  // Original implied volatility from yfinance
  impliedVolatilityBid: number;
  impliedVolatilityMid: number;
  impliedVolatilityAsk: number;
  delta: number;
}
```

### API Response Model

```typescript
interface OptionsApiResponse {
  ticker: string;
  stock: StockData;
  vix: VixData;
  expirationDates: ExpirationData[];
}

interface ExpirationData {
  expiration: string;
  daysToExpiration: number;
  expirationLabel: string; // "2w", "1m", "6w", "2m"
  calls: OptionData[];
  puts: OptionData[];
}
```

## Implementation Details

### Previous Close and Percent Change Calculation

1. Fetch current stock price from market data provider
2. Fetch previous day's closing price from market data provider
3. Calculate percent change: `((currentPrice - previousClose) / previousClose) * 100`
4. Apply the same logic for VIX data

### Timestamp Restructuring

1. Move the existing `dataTimestamp` into the stock data structure
2. Move the existing `vixTimestamp` into the VIX data structure
3. Ensure all timestamps are in ISO 8601 format

### Expiration Date Selection

1. Calculate target dates from current date:
   - 2 weeks: current date + 14 days
   - 1 month: current date + 30 days
   - 6 weeks: current date + 42 days
   - 2 months: current date + 60 days
2. For each target date, find the closest available expiration date
3. Include only these four expiration dates in the response

```python
def find_closest_expiration_dates(all_expirations, current_date):
    target_periods = {
        "2w": 14,  # 2 weeks in days
        "1m": 30,  # 1 month in days
        "6w": 42,  # 6 weeks in days
        "2m": 60   # 2 months in days
    }
    
    result = {}
    
    for label, days in target_periods.items():
        target_date = current_date + timedelta(days=days)
        closest_exp = min(all_expirations, key=lambda x: abs((x - target_date).days))
        result[label] = closest_exp
    
    return result
```

### Moneyness Calculation and Filtering

1. For each option, calculate moneyness as `strike / current_stock_price`
2. Filter options to include only those with moneyness between 0.85 and 1.15
3. Include the moneyness value in the option data

```python
def calculate_moneyness(strike_price, current_price):
    return strike_price / current_price

def filter_by_moneyness(options, current_price, min_moneyness=0.85, max_moneyness=1.15):
    filtered_options = []
    
    for option in options:
        moneyness = calculate_moneyness(option.strike, current_price)
        if min_moneyness <= moneyness <= max_moneyness:
            option.moneyness = moneyness
            filtered_options.append(option)
    
    return filtered_options
```

### Implied Volatility Calculation

1. Calculate mid price as `(bid + ask) / 2`
2. Calculate implied volatility using the bid price
3. Calculate implied volatility using the mid price
4. Calculate implied volatility using the ask price
5. Include all three IV values in the option data

```python
def calculate_implied_volatilities(option, current_price, time_to_expiration, risk_free_rate):
    # Calculate mid price
    mid_price = (option.bid + option.ask) / 2
    option.midPrice = mid_price
    
    # Calculate IVs using the Black-Scholes model
    option_type = 'c' if option.option_type == 'call' else 'p'
    
    try:
        # Only calculate if bid > 0
        iv_bid = implied_volatility(
            price=option.bid,
            S=current_price,
            K=option.strike,
            t=time_to_expiration,
            r=risk_free_rate,
            flag=option_type
        ) if option.bid > 0 else None
        
        iv_mid = implied_volatility(
            price=mid_price,
            S=current_price,
            K=option.strike,
            t=time_to_expiration,
            r=risk_free_rate,
            flag=option_type
        )
        
        # Only calculate if ask > 0
        iv_ask = implied_volatility(
            price=option.ask,
            S=current_price,
            K=option.strike,
            t=time_to_expiration,
            r=risk_free_rate,
            flag=option_type
        ) if option.ask > 0 else None
        
        option.impliedVolatilityBid = iv_bid
        option.impliedVolatilityMid = iv_mid
        option.impliedVolatilityAsk = iv_ask
        
    except Exception as e:
        logger.warning(f"Failed to calculate IV: {e}")
```

## Error Handling

The enhanced API will maintain the existing error handling mechanisms:

1. Input validation for ticker symbols
2. Error handling for market data service failures
3. Error handling for calculation failures (e.g., invalid inputs for IV calculation)
4. Appropriate HTTP status codes and error messages in the response

## Testing Strategy

### Unit Tests

1. Test previous close and percent change calculations
2. Test expiration date selection logic
3. Test moneyness calculation and filtering
4. Test implied volatility calculations with different price inputs

### Integration Tests

1. Test the end-to-end flow with mock market data
2. Verify the structure and content of the API response

### Performance Tests

1. Measure the impact of additional calculations on Lambda execution time
2. Ensure the enhanced API meets performance requirements

## Deployment Considerations

1. The enhanced API will be deployed as an update to the existing Lambda function
2. A staged deployment approach will be used to minimize risk
3. Monitoring will be in place to detect any issues with the enhanced API