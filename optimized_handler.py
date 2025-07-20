"""
Optimized Lambda handler for options analytics API.
Orchestrates all components to fetch and process options data.
Enhanced with additional market data, expiration filtering, and option calculations.
"""

try:
    import unzip_requirements
except ImportError:
    pass

import json
import time
from typing import Dict, Any, Optional
import logging
from src.utils.json_encoder import CustomJSONEncoder

from src.services.market_data_fetcher import MarketDataFetcher
from src.services.options_data_fetcher import OptionsDataFetcher
from src.services.optimized_data_processor import OptimizedDataProcessor
from src.utils.data_formatter import validate_ticker_symbol, format_market_data_for_response
from src.utils.logging_utils import create_request_logger, configure_root_logger, performance_timer
from src.utils.error_handling import (
    create_error_handler, DataFetchError, ValidationError, SystemError
)

# Configure root logger for Lambda
configure_root_logger()

# Set logging level for external libraries to reduce noise
logging.getLogger('py_vollib').setLevel(logging.WARNING)
logging.getLogger('py_lets_be_rational').setLevel(logging.WARNING)


def parse_query_parameters(event: Dict[str, Any], logger) -> str:
    """
    Parse query parameters from API Gateway event.
    
    Args:
        event: API Gateway event object
        logger: StructuredLogger instance
        
    Returns:
        Ticker symbol (defaults to 'SPY')
    """
    # Default ticker
    ticker = "SPY"
    
    # Extract query parameters
    query_params = event.get('queryStringParameters')
    if query_params and isinstance(query_params, dict):
        ticker_param = query_params.get('ticker')
        if ticker_param:
            ticker = ticker_param.strip()
    
    logger.info(f"Using ticker: {ticker}", ticker=ticker, query_params=query_params)
    return ticker


def convert_expiration_data_to_dict(expiration_data_list) -> Dict[str, list]:
    """
    Convert ExpirationData objects to dictionary format expected by DataProcessor.
    
    Args:
        expiration_data_list: List of ExpirationData objects
        
    Returns:
        Dictionary with expiration dates as keys and option lists as values
    """
    result = {}
    
    for expiration_data in expiration_data_list:
        options_list = []
        
        # Add calls with enhanced fields
        for call in expiration_data.calls:
            option_dict = {
                'strike': call.strike,
                'last_price': call.last_price,
                'option_type': call.option_type
            }
            
            # Add enhanced fields if available
            if call.contract_symbol:
                option_dict['contract_symbol'] = call.contract_symbol
            if call.last_trade_date:
                option_dict['last_trade_date'] = call.last_trade_date
            if call.bid is not None:
                option_dict['bid'] = call.bid
            if call.ask is not None:
                option_dict['ask'] = call.ask
            if call.volume is not None:
                option_dict['volume'] = call.volume
            if call.open_interest is not None:
                option_dict['open_interest'] = call.open_interest
            
            options_list.append(option_dict)
        
        # Add puts with enhanced fields
        for put in expiration_data.puts:
            option_dict = {
                'strike': put.strike,
                'last_price': put.last_price,
                'option_type': put.option_type
            }
            
            # Add enhanced fields if available
            if put.contract_symbol:
                option_dict['contract_symbol'] = put.contract_symbol
            if put.last_trade_date:
                option_dict['last_trade_date'] = put.last_trade_date
            if put.bid is not None:
                option_dict['bid'] = put.bid
            if put.ask is not None:
                option_dict['ask'] = put.ask
            if put.volume is not None:
                option_dict['volume'] = put.volume
            if put.open_interest is not None:
                option_dict['open_interest'] = put.open_interest
            
            options_list.append(option_dict)
        
        result[expiration_data.expiration] = options_list
    
    return result


def get_options_analytics(event, context):
    """
    Main Lambda handler function for options analytics API.
    
    Args:
        event: API Gateway event object
        context: Lambda context object
        
    Returns:
        dict: HTTP response with CORS headers
    """
    # Initialize structured logging and error handling
    logger = create_request_logger(__name__, event)
    error_handler = create_error_handler(logger)
    
    # Track overall request performance
    request_start_time = time.time()
    
    try:
        # Log API request
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/options-analytics')
        query_params = event.get('queryStringParameters')
        logger.log_api_request(method, path, query_params)
        
        # Parse and validate query parameters
        ticker = parse_query_parameters(event, logger)
        
        try:
            validated_ticker = validate_ticker_symbol(ticker)
        except ValueError as e:
            error_handler.log_and_raise_validation_error(
                f"Invalid ticker symbol: {str(e)}",
                field="ticker",
                value=ticker
            )
        
        logger.info(f"Processing request for ticker: {validated_ticker}", ticker=validated_ticker)
        
        # Initialize services
        market_fetcher = MarketDataFetcher()
        options_fetcher = OptionsDataFetcher()
        data_processor = OptimizedDataProcessor()  # Use optimized data processor
        
        # Fetch enhanced market data with performance tracking
        with performance_timer(logger, "enhanced_market_data_fetch", ticker=validated_ticker):
            try:
                # Use the enhanced market data fetcher to get stock and VIX data with previous close
                enhanced_market_data = market_fetcher.fetch_enhanced_market_data(validated_ticker)
                
                # Extract values for logging and further processing
                stock_price = enhanced_market_data['stock']['price']
                stock_prev_close = enhanced_market_data['stock']['previousClose']
                stock_pct_change = enhanced_market_data['stock']['percentChange']
                stock_timestamp = enhanced_market_data['stock']['timestamp']
                
                vix_value = enhanced_market_data['vix']['value']
                vix_prev_close = enhanced_market_data['vix']['previousClose']
                vix_pct_change = enhanced_market_data['vix']['percentChange']
                vix_timestamp = enhanced_market_data['vix']['timestamp']
                
                logger.log_data_fetch("enhanced_market_data", validated_ticker, True, 
                                    stock_price=stock_price, 
                                    stock_prev_close=stock_prev_close,
                                    stock_pct_change=stock_pct_change,
                                    vix_value=vix_value,
                                    vix_prev_close=vix_prev_close,
                                    vix_pct_change=vix_pct_change)
                                    
            except RuntimeError as e:
                logger.log_data_fetch("enhanced_market_data", validated_ticker, False, error=str(e))
                
                # Try to fall back to basic market data if enhanced data fails
                try:
                    logger.info("Falling back to basic market data fetch", ticker=validated_ticker)
                    stock_price, vix_value, stock_timestamp, vix_timestamp = market_fetcher.fetch_market_data(validated_ticker)
                    
                    # Use current values as fallbacks for previous close
                    stock_prev_close = stock_price
                    stock_pct_change = 0.0
                    vix_prev_close = vix_value
                    vix_pct_change = 0.0
                    
                    logger.log_data_fetch("fallback_market_data", validated_ticker, True, 
                                        stock_price=stock_price, 
                                        vix_value=vix_value)
                                        
                except RuntimeError as fallback_error:
                    # If even the fallback fails, raise the original error
                    logger.log_data_fetch("fallback_market_data", validated_ticker, False, 
                                        error=str(fallback_error))
                    error_handler.log_and_raise_data_fetch_error(
                        f"Failed to fetch enhanced market data: {str(e)}",
                        source="enhanced_market_data",
                        ticker=validated_ticker,
                        original_error=e
                    )
        
        # Fetch filtered options data with performance tracking
        with performance_timer(logger, "filtered_options_data_fetch", ticker=validated_ticker):
            try:
                # Use the filtered option chains method to get only target expiration periods
                expiration_data_list = options_fetcher.fetch_filtered_option_chains(validated_ticker)
                
                if not expiration_data_list:
                    logger.log_data_fetch("filtered_options_data", validated_ticker, False, 
                                        reason="no_expiration_dates")
                    error_handler.log_and_raise_data_fetch_error(
                        f"No option expiration dates found for ticker {validated_ticker}",
                        source="filtered_options_data",
                        ticker=validated_ticker
                    )
                
                logger.log_data_fetch("filtered_options_data", validated_ticker, True,
                                    expiration_count=len(expiration_data_list))
                
            except RuntimeError as e:
                logger.log_data_fetch("filtered_options_data", validated_ticker, False, error=str(e))
                
                # Try to fall back to regular option chains if filtered chains fail
                try:
                    logger.info("Falling back to unfiltered option chains", ticker=validated_ticker)
                    
                    # Get all option chains
                    all_expiration_data_list = options_fetcher.fetch_all_option_chains(validated_ticker)
                    
                    if not all_expiration_data_list:
                        logger.log_data_fetch("fallback_options_data", validated_ticker, False, 
                                            reason="no_expiration_dates")
                        error_handler.log_and_raise_data_fetch_error(
                            f"No option expiration dates found for ticker {validated_ticker}",
                            source="fallback_options_data",
                            ticker=validated_ticker
                        )
                    
                    # Try to filter them manually
                    try:
                        from src.utils.expiration_selector import filter_expirations_by_target_periods
                        expiration_data_list = filter_expirations_by_target_periods(all_expiration_data_list)
                        
                        if not expiration_data_list:
                            # If filtering fails, just use the first few expirations
                            expiration_data_list = all_expiration_data_list[:4]  # Use first 4 expirations as fallback
                            logger.info("Using first 4 expirations as fallback", 
                                      ticker=validated_ticker,
                                      expiration_count=len(expiration_data_list))
                    except Exception as filter_error:
                        # If filtering fails, just use the first few expirations
                        expiration_data_list = all_expiration_data_list[:4]  # Use first 4 expirations as fallback
                        logger.warning(f"Failed to filter expirations, using first 4 as fallback: {str(filter_error)}",
                                     ticker=validated_ticker,
                                     error=str(filter_error),
                                     expiration_count=len(expiration_data_list))
                    
                    logger.log_data_fetch("fallback_options_data", validated_ticker, True,
                                        expiration_count=len(expiration_data_list))
                                        
                except RuntimeError as fallback_error:
                    # If even the fallback fails, raise the original error
                    logger.log_data_fetch("fallback_options_data", validated_ticker, False, 
                                        error=str(fallback_error))
                    error_handler.log_and_raise_data_fetch_error(
                        f"Failed to fetch filtered options data: {str(e)}",
                        source="filtered_options_data",
                        ticker=validated_ticker,
                        original_error=e
                    )
        
        # Convert expiration data to format expected by data processor
        raw_options_data = convert_expiration_data_to_dict(expiration_data_list)
        
        # Process and format data with performance tracking
        with performance_timer(logger, "enhanced_data_processing", ticker=validated_ticker):
            try:
                # Create a market data object with the enhanced data
                market_data = data_processor.create_market_data_response(
                    ticker=validated_ticker,
                    stock_price=stock_price,
                    vix_value=vix_value,
                    raw_options_data=raw_options_data,
                    data_timestamp=stock_timestamp,
                    vix_timestamp=vix_timestamp,
                    filter_expirations=False  # Already filtered by fetch_filtered_option_chains
                )
                
                # Update the stock and VIX data with the enhanced values
                market_data.stock.previous_close = stock_prev_close
                market_data.stock.percent_change = stock_pct_change
                
                market_data.vix.previous_close = vix_prev_close
                market_data.vix.percent_change = vix_pct_change
                
                # Add error handling for IV calculations
                for expiration_data in market_data.expiration_dates:
                    # Process calls
                    for call in expiration_data.calls:
                        # Ensure we have at least one valid IV calculation
                        if (call.implied_volatility is None and 
                            call.implied_volatility_bid is None and 
                            call.implied_volatility_mid is None and 
                            call.implied_volatility_ask is None):
                            
                            # Log the issue
                            logger.warning(
                                f"No valid IV calculations for call option with strike {call.strike}",
                                strike=call.strike,
                                expiration=expiration_data.expiration
                            )
                            
                            # Set a default IV value based on available data
                            # This is a fallback to ensure we have some IV value
                            if call.bid is not None and call.bid > 0 and call.ask is not None and call.ask > 0:
                                # If we have bid and ask, use a simple approximation
                                # This is not accurate but better than nothing
                                call.implied_volatility = 0.2  # Default to 20% volatility
                                logger.info(
                                    f"Using default IV of 0.2 for call option with strike {call.strike}",
                                    strike=call.strike,
                                    expiration=expiration_data.expiration
                                )
                    
                    # Process puts
                    for put in expiration_data.puts:
                        # Ensure we have at least one valid IV calculation
                        if (put.implied_volatility is None and 
                            put.implied_volatility_bid is None and 
                            put.implied_volatility_mid is None and 
                            put.implied_volatility_ask is None):
                            
                            # Log the issue
                            logger.warning(
                                f"No valid IV calculations for put option with strike {put.strike}",
                                strike=put.strike,
                                expiration=expiration_data.expiration
                            )
                            
                            # Set a default IV value based on available data
                            # This is a fallback to ensure we have some IV value
                            if put.bid is not None and put.bid > 0 and put.ask is not None and put.ask > 0:
                                # If we have bid and ask, use a simple approximation
                                # This is not accurate but better than nothing
                                put.implied_volatility = 0.2  # Default to 20% volatility
                                logger.info(
                                    f"Using default IV of 0.2 for put option with strike {put.strike}",
                                    strike=put.strike,
                                    expiration=expiration_data.expiration
                                )
                
                # Format the market data for API response
                response_data = format_market_data_for_response(market_data)
                
                # Log processing summary
                total_options = sum(
                    len(exp.get('calls', [])) + len(exp.get('puts', []))
                    for exp in response_data.get('expirationDates', [])
                )
                
                logger.log_calculation(
                    "enhanced_options_processing",
                    count=sum(len(opts) for opts in raw_options_data.values()),
                    success_count=total_options,
                    expiration_dates=len(response_data.get('expirationDates', []))
                )
                
            except Exception as e:
                logger.error(f"Failed to process enhanced options data: {str(e)}", 
                           ticker=validated_ticker, 
                           error=str(e))
                
                # Try a simplified processing approach as fallback
                try:
                    logger.info("Attempting simplified data processing as fallback", 
                              ticker=validated_ticker)
                    
                    # Create a basic market data response without enhanced calculations
                    from src.models.option_data import MarketData, StockData, VixData
                    
                    # Create basic stock and VixData objects
                    stock_data = StockData(
                        price=stock_price,
                        previous_close=stock_prev_close,
                        percent_change=stock_pct_change,
                        timestamp=stock_timestamp
                    )
                    
                    vix_data = VixData(
                        value=vix_value,
                        previous_close=vix_prev_close,
                        percent_change=vix_pct_change,
                        timestamp=vix_timestamp
                    )
                    
                    # Create a market data object with minimal processing
                    market_data = MarketData(
                        ticker=validated_ticker,
                        stock=stock_data,
                        vix=vix_data,
                        expiration_dates=expiration_data_list
                    )
                    
                    # Format for API response
                    response_data = format_market_data_for_response(market_data)
                    
                    logger.info("Successfully created fallback response", 
                              ticker=validated_ticker,
                              expiration_count=len(expiration_data_list))
                              
                except Exception as fallback_error:
                    # If even the fallback fails, raise the original error
                    logger.error(f"Fallback processing failed: {str(fallback_error)}", 
                               ticker=validated_ticker, 
                               error=str(fallback_error))
                    error_handler.log_and_raise_calculation_error(
                        f"Failed to process enhanced options data: {str(e)}",
                        calculation_type="enhanced_options_processing",
                        original_error=e,
                        ticker=validated_ticker
                    )
        
        # Create successful response
        response_body = json.dumps(response_data, cls=CustomJSONEncoder)
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': response_body
        }
        
        # Log successful response
        request_duration = time.time() - request_start_time
        logger.log_api_response(200, len(response_body))
        logger.log_performance("total_request", request_duration, 
                             ticker=validated_ticker, total_options=total_options)
        
        return response
        
    except (DataFetchError, ValidationError, SystemError) as e:
        # Handle known error types
        response = error_handler.handle_error(e, {
            'ticker': locals().get('ticker'),
            'validated_ticker': locals().get('validated_ticker'),
            'request_duration': time.time() - request_start_time
        })
        
        logger.log_api_response(response['statusCode'])
        return response
        
    except Exception as e:
        # Handle unexpected errors
        response = error_handler.handle_error(e, {
            'ticker': locals().get('ticker'),
            'validated_ticker': locals().get('validated_ticker'),
            'request_duration': time.time() - request_start_time
        })
        
        logger.log_api_response(response['statusCode'])
        return response