# Options Analytics API Documentation

## Overview

The Options Analytics API provides comprehensive options data and analytics for a given stock ticker. The API has been enhanced with additional market data, expiration date filtering, moneyness calculations, and improved implied volatility calculations.

## Endpoint

```
GET https://whl064peuf.execute-api.us-east-1.amazonaws.com/options-analytics
```

## Request Parameters

| Parameter | Type   | Required | Description                                |
|-----------|--------|----------|--------------------------------------------|
| ticker    | string | Yes      | Stock symbol (e.g., SPY, AAPL, TSLA)       |

## Response Format

The API returns a JSON object with the following structure:

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
          "impliedVolatilityYF": 0.190,
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

## Response Fields

### Top Level

| Field           | Type   | Description                                   |
|-----------------|--------|-----------------------------------------------|
| ticker          | string | The stock ticker symbol (uppercase)           |
| stock           | object | Stock price information                       |
| vix             | object | VIX index information                         |
| expirationDates | array  | List of option expiration dates with options  |

### Stock Object

| Field         | Type   | Description                                          |
|---------------|--------|------------------------------------------------------|
| price         | number | Current stock price                                  |
| previousClose | number | Previous day's closing price                         |
| percentChange | number | Percentage change from previous close                |
| timestamp     | string | Timestamp of the stock data (ISO 8601 format)        |

### VIX Object

| Field         | Type   | Description                                          |
|---------------|--------|------------------------------------------------------|
| value         | number | Current VIX index value                              |
| previousClose | number | Previous day's VIX closing value                     |
| percentChange | number | Percentage change from previous close                |
| timestamp     | string | Timestamp of the VIX data (ISO 8601 format)          |

### Expiration Date Object

| Field            | Type   | Description                                                |
|------------------|--------|------------------------------------------------------------|
| expiration       | string | Expiration date in YYYY-MM-DD format                       |
| daysToExpiration | number | Number of days until expiration                            |
| expirationLabel  | string | Label indicating target period (2w, 1m, 6w, 2m)            |
| calls            | array  | List of call options for this expiration                   |
| puts             | array  | List of put options for this expiration                    |

### Option Object

| Field                | Type   | Description                                                |
|----------------------|--------|------------------------------------------------------------|
| contractSymbol       | string | Option contract symbol (e.g., SPY250801C00600000)          |
| lastTradeDate        | string | Date and time of the last trade (ISO 8601 format)          |
| strike              | number | Strike price of the option                                 |
| lastPrice           | number | Last traded price of the option                            |
| bid                 | number | Current bid price                                          |
| ask                 | number | Current ask price                                          |
| midPrice            | number | Calculated mid price ((bid + ask) / 2)                     |
| volume              | number | Trading volume for the day                                 |
| openInterest        | number | Open interest for the option                               |
| moneyness           | number | Ratio of strike price to current stock price               |
| impliedVolatilityYF | number | Original implied volatility from yfinance                  |
| impliedVolatilityBid| number | Implied volatility calculated using bid price              |
| impliedVolatilityMid| number | Implied volatility calculated using mid price              |
| impliedVolatilityAsk| number | Implied volatility calculated using ask price              |
| delta               | number | Delta of the option (rate of change relative to underlying)|

## Enhancements

### Stock and VIX Data

The API now includes previous closing prices and percentage changes for both the stock and VIX index, providing context for current market conditions.

### Expiration Date Selection

The API filters option expiration dates to focus on specific target periods:
- **2w**: Closest expiration to 2 weeks from now
- **1m**: Closest expiration to 1 month from now
- **6w**: Closest expiration to 6 weeks from now
- **2m**: Closest expiration to 2 months from now

### Moneyness Calculation and Filtering

Options are filtered to include only those with moneyness between 0.85 and 1.15, focusing on options that are near the money. Moneyness is calculated as:

```
moneyness = strike_price / current_stock_price
```

### Enhanced Implied Volatility Calculations

The API now provides multiple implied volatility calculations:
- **impliedVolatilityYF**: Original implied volatility from yfinance
- **impliedVolatilityBid**: Implied volatility calculated using bid price
- **impliedVolatilityMid**: Implied volatility calculated using mid price ((bid + ask) / 2)
- **impliedVolatilityAsk**: Implied volatility calculated using ask price

### Additional Option Fields

The API now includes additional option data fields:
- Contract symbol
- Last trade date
- Bid and ask prices
- Mid price
- Volume
- Open interest

## Error Responses

| Status Code | Description                                                |
|-------------|------------------------------------------------------------|
| 400         | Bad Request - Invalid parameters or ticker symbol          |
| 404         | Not Found - No data available for the requested ticker     |
| 500         | Internal Server Error - Server-side error                  |
| 503         | Service Unavailable - Temporary service issue              |

Error response format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message",
    "details": {
      "field": "ticker",
      "value": "INVALID"
    }
  }
}
```

## Rate Limits

- Maximum of 100 requests per minute per IP address
- Maximum of 1000 requests per day per IP address

## Example Usage

### cURL

```bash
curl "https://whl064peuf.execute-api.us-east-1.amazonaws.com/options-analytics?ticker=SPY"
```

### Python

```python
import requests

response = requests.get(
    "https://whl064peuf.execute-api.us-east-1.amazonaws.com/options-analytics",
    params={"ticker": "SPY"}
)

data = response.json()
print(f"SPY price: ${data['stock']['price']}")
print(f"SPY change: {data['stock']['percentChange']}%")
print(f"VIX: {data['vix']['value']}")
```

### JavaScript

```javascript
fetch("https://whl064peuf.execute-api.us-east-1.amazonaws.com/options-analytics?ticker=SPY")
  .then(response => response.json())
  .then(data => {
    console.log(`SPY price: $${data.stock.price}`);
    console.log(`SPY change: ${data.stock.percentChange}%`);
    console.log(`VIX: ${data.vix.value}`);
  });
```