# Requirements Document

## Introduction

This feature enhances the Options Data API handler to provide more comprehensive market data and analytics. The enhancements include adding stock and VIX price information with percentage changes, restructuring timestamp data, filtering options by specific expiration dates, adding more option data fields, calculating moneyness, and enhancing implied volatility calculations based on different price points. These improvements will make the API more useful for client applications including the SPY Options Data Viewer.

## Requirements

### Requirement 1

**User Story:** As a trader, I want the API to provide the stock's previous closing price and percentage change, so that I can quickly assess recent market movement.

#### Acceptance Criteria

1. WHEN the API is called THEN the system SHALL return the stock's previous closing price
2. WHEN the API is called THEN the system SHALL return the stock's percentage change from previous close
3. WHEN returning price information THEN the system SHALL include both raw values for programmatic use

### Requirement 2

**User Story:** As a trader, I want the API to provide the VIX index's previous closing value and percentage change, so that I can gauge market volatility context.

#### Acceptance Criteria

1. WHEN the API is called THEN the system SHALL return VIX's previous closing value
2. WHEN the API is called THEN the system SHALL return VIX's percentage change from previous close
3. WHEN returning VIX information THEN the system SHALL include raw values for programmatic use

### Requirement 3

**User Story:** As a developer, I want to restructure the timestamp data within the stock and VIX data objects in the API response, so that the data structure is more organized and consistent.

#### Acceptance Criteria

1. WHEN returning API data THEN the system SHALL include dataTimestamp within a stock data structure
2. WHEN returning API data THEN the system SHALL include vixTimestamp within a VIX data structure
3. WHEN returning timestamp information THEN the system SHALL use ISO 8601 format for consistency

### Requirement 4

**User Story:** As a trader, I want the API to provide options for specific expiration periods (2 weeks, 1 month, 6 weeks, and 2 months), so that I can focus on the most relevant timeframes for my trading strategy.

#### Acceptance Criteria

1. WHEN returning option data THEN the system SHALL identify and include options for the expiration date closest to 2 weeks from now
2. WHEN returning option data THEN the system SHALL identify and include options for the expiration date closest to 1 month from now
3. WHEN returning option data THEN the system SHALL identify and include options for the expiration date closest to 6 weeks from now
4. WHEN returning option data THEN the system SHALL identify and include options for the expiration date closest to 2 months from now
5. WHEN no exact match for a target expiration period exists THEN the system SHALL select the closest available expiration date

### Requirement 5

**User Story:** As a trader, I want the API to provide comprehensive option data including contract details, pricing, and trading activity, so that I can make more informed trading decisions.

#### Acceptance Criteria

1. WHEN returning option data THEN the system SHALL include 'contractSymbol' field
2. WHEN returning option data THEN the system SHALL include 'lastTradeDate' field
3. WHEN returning option data THEN the system SHALL include 'strike' field
4. WHEN returning option data THEN the system SHALL include 'lastPrice' field
5. WHEN returning option data THEN the system SHALL include 'bid' field
6. WHEN returning option data THEN the system SHALL include 'ask' field
7. WHEN returning option data THEN the system SHALL include 'volume' field
8. WHEN returning option data THEN the system SHALL include 'openInterest' field
9. WHEN returning option data THEN the system SHALL include 'impliedVolatility' field

### Requirement 6

**User Story:** As a trader, I want the API to filter options by moneyness within a specific range (0.85 to 1.15), so that I can focus on options that are near the money.

#### Acceptance Criteria

1. WHEN processing option data THEN the system SHALL calculate moneyness as the ratio of strike price to current stock price
2. WHEN returning option data THEN the system SHALL filter options to include only those with moneyness between 0.85 and 1.15
3. WHEN calculating moneyness for calls THEN the system SHALL use the formula: strike price / current stock price
4. WHEN calculating moneyness for puts THEN the system SHALL use the formula: strike price / current stock price
5. WHEN returning option data THEN the system SHALL include the calculated moneyness value for each option

### Requirement 7

**User Story:** As a trader, I want the API to provide implied volatility calculated based on bid, mid, and ask prices (not last price), so that I can better understand the volatility smile and potential pricing discrepancies.

#### Acceptance Criteria

1. WHEN processing option data THEN the system SHALL calculate the mid price as (bid + ask) / 2
2. WHEN processing option data THEN the system SHALL calculate implied volatility based on the bid price
3. WHEN processing option data THEN the system SHALL calculate implied volatility based on the mid price
4. WHEN processing option data THEN the system SHALL calculate implied volatility based on the ask price
5. WHEN returning implied volatility data THEN the system SHALL include all three IV values (bid IV, mid IV, ask IV)
6. WHEN calculating implied volatility THEN the system SHALL NOT use calculations based on lastPrice