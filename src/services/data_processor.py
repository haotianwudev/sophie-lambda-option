"""
Data processor for structuring and formatting options analytics data.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.option_data import OptionData, ExpirationData, MarketData
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
        underlying_price: float
    ) -> List[ExpirationData]:
        """
        Structure raw options data by expiration date with calculated IV and delta.
        
        Args:
            raw_options_data: Dictionary with expiration dates as keys and option lists as values
            underlying_price: Current underlying stock price
            
        Returns:
            List of ExpirationData objects with calculated values
        """
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
            
            self.logger.info(
                f"Expiration {expiration_date}: {len(valid_calls)} valid calls, "
                f"{len(valid_puts)} valid puts (filtered from "
                f"{len(calls)} calls, {len(puts)} puts)",
                expiration_date=expiration_date,
                valid_calls=len(valid_calls),
                valid_puts=len(valid_puts),
                total_calls=len(calls),
                total_puts=len(puts)
            )
            
            # Create ExpirationData object
            expiration_data = ExpirationData(
                expiration=expiration_date,
                calls=valid_calls,
                puts=valid_puts
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
                    implied_volatility=None,  # Will be calculated
                    delta=None,  # Will be calculated
                    option_type=raw_option.get('option_type', 'c')
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
        vix_timestamp: Optional[datetime] = None
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
        
        # Create MarketData object
        market_data = MarketData(
            ticker=validated_ticker,
            stock_price=stock_price,
            vix_value=vix_value,
            data_timestamp=data_timestamp,
            vix_timestamp=vix_timestamp,
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
        vix_timestamp: Optional[datetime] = None
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
                vix_timestamp=vix_timestamp
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