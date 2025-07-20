"""
Data processor for structuring and formatting options analytics data.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.option_data import OptionData, ExpirationData, MarketData, StockData, VixData
from ..utils.data_formatter import (
    format_market_data_for_response,
    filter_valid_options,
    validate_ticker_symbol
)
from ..utils.time_utils import get_current_utc_timestamp
from ..utils.logging_utils import StructuredLogger
from ..utils.error_handling import CalculationError
from .options_calculator import OptionsCalculator


class DataProcessor:
    """Processes and structures options data for API responses."""
    
    def __init__(self, risk_free_rate: float = 0.03, logger: Optional[StructuredLogger] = None):
        """
        Initialize data processor.
        
        Args:
            risk_free_rate: Risk-free interest rate for calculations
            logger: Optional structured logger instance
        """
        self.calculator = OptionsCalculator(risk_free_rate, logger)
        self.logger = logger or StructuredLogger(__name__)
    
    def structure_options_by_expiration(
        self,
        raw_options_data: Dict[str, List[Dict[str, Any]]],
        underlying_price: float,
        min_moneyness: float = 0.85,
        max_moneyness: float = 1.15
    ) -> List[ExpirationData]:
        """
        Structure raw options data by expiration date with calculated IV and delta.
        Also calculates moneyness and filters options by moneyness range.
        
        Args:
            raw_options_data: Dictionary with expiration dates as keys and option lists as values
            underlying_price: Current underlying stock price
            min_moneyness: Minimum moneyness threshold (default: 0.85)
            max_moneyness: Maximum moneyness threshold (default: 1.15)
            
        Returns:
            List of ExpirationData objects with calculated values
        """
        from ..utils.calculation_utils import calculate_moneyness, is_within_moneyness_range
        
        expiration_data_list = []
        
        for expiration_date, options_list in raw_options_data.items():
            self.logger.info(f"Processing {len(options_list)} options for expiration {expiration_date}",
                           expiration_date=expiration_date, options_count=len(options_list))
            
            # Separate calls and puts
            calls_raw = [opt for opt in options_list if opt.get('option_type') == 'c']
            puts_raw = [opt for opt in options_list if opt.get('option_type') == 'p']
            
            # Convert to OptionData objects
            calls = self._convert_raw_options_to_objects(calls_raw)
            puts = self._convert_raw_options_to_objects(puts_raw)
            
            # Calculate IV and delta for all options
            processed_calls = self.calculator.process_options_with_iv(
                calls, underlying_price, expiration_date
            )
            processed_puts = self.calculator.process_options_with_iv(
                puts, underlying_price, expiration_date
            )
            
            # Filter out invalid options
            valid_calls = filter_valid_options(processed_calls)
            valid_puts = filter_valid_options(processed_puts)
            
            # Calculate moneyness and filter by moneyness range
            filtered_calls = []
            for call in valid_calls:
                call.moneyness = calculate_moneyness(call.strike, underlying_price)
                if is_within_moneyness_range(call.moneyness, min_moneyness, max_moneyness):
                    filtered_calls.append(call)
            
            filtered_puts = []
            for put in valid_puts:
                put.moneyness = calculate_moneyness(put.strike, underlying_price)
                if is_within_moneyness_range(put.moneyness, min_moneyness, max_moneyness):
                    filtered_puts.append(put)
            
            self.logger.info(
                f"Expiration {expiration_date}: {len(filtered_calls)} filtered calls, "
                f"{len(filtered_puts)} filtered puts (from "
                f"{len(valid_calls)} valid calls, {len(valid_puts)} valid puts)",
                expiration_date=expiration_date,
                filtered_calls=len(filtered_calls),
                filtered_puts=len(filtered_puts),
                valid_calls=len(valid_calls),
                valid_puts=len(valid_puts)
            )
            
            # Create ExpirationData object
            expiration_data = ExpirationData(
                expiration=expiration_date,
                calls=filtered_calls,
                puts=filtered_puts
            )
            
            expiration_data_list.append(expiration_data)
        
        # Sort by expiration date
        expiration_data_list.sort(key=lambda x: x.expiration)
        
        return expiration_data_list
    
    def _convert_raw_options_to_objects(self, raw_options: List[Dict[str, Any]]) -> List[OptionData]:
        """
        Convert raw option dictionaries to OptionData objects.
        
        Args:
            raw_options: List of raw option dictionaries
            
        Returns:
            List of OptionData objects
        """
        options = []
        
        for raw_option in raw_options:
            try:
                option = OptionData(
                    strike=float(raw_option.get('strike', 0)),
                    last_price=float(raw_option.get('last_price', 0)) if raw_option.get('last_price') is not None else None,
                    implied_volatility=float(raw_option.get('implied_volatility', 0)),  # implied_volatility_yf
                    delta=None,  # Will be calculated
                    option_type=raw_option.get('option_type', 'c'),
                    contract_symbol=raw_option.get('contract_symbol'),
                    last_trade_date=raw_option.get('last_trade_date'),
                    bid=float(raw_option.get('bid', 0)) if raw_option.get('bid') is not None else None,
                    ask=float(raw_option.get('ask', 0)) if raw_option.get('ask') is not None else None,
                    mid_price=None,  # Will be calculated
                    volume=int(raw_option.get('volume', 0)) if raw_option.get('volume') is not None else None,
                    open_interest=int(raw_option.get('open_interest', 0)) if raw_option.get('open_interest') is not None else None,
                    moneyness=None,  # Will be calculated
                    implied_volatility_bid=None,  # Will be calculated
                    implied_volatility_mid=None,  # Will be calculated
                    implied_volatility_ask=None   # Will be calculated
                )
                options.append(option)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to convert raw option to OptionData: {e}")
                continue
        
        return options
    
    def create_market_data_response(
        self,
        ticker: str,
        stock_price: float,
        vix_value: float,
        raw_options_data: Dict[str, List[Dict[str, Any]]],
        data_timestamp: Optional[datetime] = None,
        vix_timestamp: Optional[datetime] = None,
        filter_expirations: bool = True
    ) -> MarketData:
        """
        Create complete MarketData object from raw inputs.
        
        Args:
            ticker: Stock ticker symbol
            stock_price: Current stock price
            vix_value: Current VIX value
            raw_options_data: Raw options data by expiration
            data_timestamp: Timestamp for options data (defaults to current time)
            vix_timestamp: Timestamp for VIX data (defaults to current time)
            filter_expirations: Whether to filter expirations to target periods (2w, 1m, 6w, 2m)
            
        Returns:
            MarketData object with processed options data
        """
        # Validate and format ticker
        validated_ticker = validate_ticker_symbol(ticker)
        
        # Use current time if timestamps not provided
        current_time = get_current_utc_timestamp()
        if data_timestamp is None:
            data_timestamp = current_time
        if vix_timestamp is None:
            vix_timestamp = current_time
        
        # Structure options data by expiration
        expiration_dates = self.structure_options_by_expiration(
            raw_options_data, stock_price
        )
        
        # Filter expirations to target periods if requested
        if filter_expirations:
            from ..utils.expiration_selector import filter_expirations_by_target_periods
            try:
                expiration_dates = filter_expirations_by_target_periods(expiration_dates)
                self.logger.info(
                    f"Filtered expirations to {len(expiration_dates)} target periods",
                    filtered_count=len(expiration_dates)
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to filter expirations to target periods: {e}",
                    error=str(e)
                )
        
        # Create StockData and VixData objects
        stock_data = StockData(
            price=stock_price,
            previous_close=stock_price,  # Using same value as placeholder
            percent_change=0.0,  # Using 0.0 as placeholder
            timestamp=data_timestamp
        )
        
        vix_data = VixData(
            value=vix_value,
            previous_close=vix_value,  # Using same value as placeholder
            percent_change=0.0,  # Using 0.0 as placeholder
            timestamp=vix_timestamp
        )
        
        # Create MarketData object
        market_data = MarketData(
            ticker=validated_ticker,
            stock=stock_data,
            vix=vix_data,
            expiration_dates=expiration_dates
        )
        
        return market_data
    
    def format_api_response(
        self,
        ticker: str,
        stock_price: float,
        vix_value: float,
        raw_options_data: Dict[str, List[Dict[str, Any]]],
        data_timestamp: Optional[datetime] = None,
        vix_timestamp: Optional[datetime] = None,
        filter_expirations: bool = True
    ) -> Dict[str, Any]:
        """
        Create formatted API response from raw data inputs.
        
        Args:
            ticker: Stock ticker symbol
            stock_price: Current stock price
            vix_value: Current VIX value
            raw_options_data: Raw options data by expiration
            data_timestamp: Timestamp for options data
            vix_timestamp: Timestamp for VIX data
            filter_expirations: Whether to filter expirations to target periods (2w, 1m, 6w, 2m)
            
        Returns:
            Dictionary formatted for JSON API response
        """
        try:
            # Create MarketData object
            market_data = self.create_market_data_response(
                ticker=ticker,
                stock_price=stock_price,
                vix_value=vix_value,
                raw_options_data=raw_options_data,
                data_timestamp=data_timestamp,
                vix_timestamp=vix_timestamp,
                filter_expirations=filter_expirations
            )
            
            # Format for API response
            response = format_market_data_for_response(market_data)
            
            self.logger.info(
                f"Created API response for {ticker}: "
                f"{len(market_data.expiration_dates)} expiration dates, "
                f"total options: {sum(len(exp.calls) + len(exp.puts) for exp in market_data.expiration_dates)}",
                ticker=ticker,
                expiration_count=len(market_data.expiration_dates),
                total_options=sum(len(exp.calls) + len(exp.puts) for exp in market_data.expiration_dates)
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to format API response: {e}")
            raise
    
    def filter_expiration_dates_by_validity(
        self,
        expiration_dates: List[ExpirationData],
        min_options_per_expiration: int = 1
    ) -> List[ExpirationData]:
        """
        Filter expiration dates that have sufficient valid options.
        
        Args:
            expiration_dates: List of ExpirationData objects
            min_options_per_expiration: Minimum number of total options required
            
        Returns:
            Filtered list of ExpirationData objects
        """
        filtered_expirations = []
        
        for expiration in expiration_dates:
            total_options = len(expiration.calls) + len(expiration.puts)
            
            if total_options >= min_options_per_expiration:
                filtered_expirations.append(expiration)
            else:
                self.logger.info(
                    f"Filtering out expiration {expiration.expiration} "
                    f"with only {total_options} valid options",
                    expiration=expiration.expiration,
                    total_options=total_options
                )
        
        return filtered_expirations