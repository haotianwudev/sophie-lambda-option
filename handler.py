"""
Main Lambda handler for options analytics API.
Orchestrates all components to fetch and process options data.
"""

try:
    import unzip_requirements
except ImportError:
    pass

import json
import time
from typing import Dict, Any, Optional

from src.services.market_data_fetcher import MarketDataFetcher
from src.services.options_data_fetcher import OptionsDataFetcher
from src.services.data_processor import DataProcessor
from src.utils.data_formatter import validate_ticker_symbol
from src.utils.logging_utils import create_request_logger, configure_root_logger, performance_timer
from src.utils.error_handling import (
    create_error_handler, DataFetchError, ValidationError, SystemError
)

# Configure root logger for Lambda
configure_root_logger()


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
        
        # Add calls
        for call in expiration_data.calls:
            options_list.append({
                'strike': call.strike,
                'last_price': call.last_price,
                'option_type': call.option_type
            })
        
        # Add puts
        for put in expiration_data.puts:
            options_list.append({
                'strike': put.strike,
                'last_price': put.last_price,
                'option_type': put.option_type
            })
        
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
        data_processor = DataProcessor()
        
        # Fetch market data with performance tracking
        with performance_timer(logger, "market_data_fetch", ticker=validated_ticker):
            try:
                stock_price, vix_value, stock_timestamp, vix_timestamp = market_fetcher.fetch_market_data(validated_ticker)
                logger.log_data_fetch("market_data", validated_ticker, True, 
                                    stock_price=stock_price, vix_value=vix_value)
            except RuntimeError as e:
                logger.log_data_fetch("market_data", validated_ticker, False, error=str(e))
                error_handler.log_and_raise_data_fetch_error(
                    f"Failed to fetch market data: {str(e)}",
                    source="market_data",
                    ticker=validated_ticker,
                    original_error=e
                )
        
        # Fetch options data with performance tracking
        with performance_timer(logger, "options_data_fetch", ticker=validated_ticker):
            try:
                expiration_data_list = options_fetcher.fetch_all_option_chains(validated_ticker)
                
                if not expiration_data_list:
                    logger.log_data_fetch("options_data", validated_ticker, False, 
                                        reason="no_expiration_dates")
                    error_handler.log_and_raise_data_fetch_error(
                        f"No option expiration dates found for ticker {validated_ticker}",
                        source="options_data",
                        ticker=validated_ticker
                    )
                
                logger.log_data_fetch("options_data", validated_ticker, True,
                                    expiration_count=len(expiration_data_list))
                
            except RuntimeError as e:
                logger.log_data_fetch("options_data", validated_ticker, False, error=str(e))
                error_handler.log_and_raise_data_fetch_error(
                    f"Failed to fetch options data: {str(e)}",
                    source="options_data",
                    ticker=validated_ticker,
                    original_error=e
                )
        
        # Convert expiration data to format expected by data processor
        raw_options_data = convert_expiration_data_to_dict(expiration_data_list)
        
        # Process and format data with performance tracking
        with performance_timer(logger, "data_processing", ticker=validated_ticker):
            try:
                response_data = data_processor.format_api_response(
                    ticker=validated_ticker,
                    stock_price=stock_price,
                    vix_value=vix_value,
                    raw_options_data=raw_options_data,
                    data_timestamp=stock_timestamp,
                    vix_timestamp=vix_timestamp
                )
                
                # Log processing summary
                total_options = sum(
                    len(exp.get('calls', [])) + len(exp.get('puts', []))
                    for exp in response_data.get('expirationDates', [])
                )
                
                logger.log_calculation(
                    "options_processing",
                    count=sum(len(opts) for opts in raw_options_data.values()),
                    success_count=total_options,
                    expiration_dates=len(response_data.get('expirationDates', []))
                )
                
            except Exception as e:
                error_handler.log_and_raise_calculation_error(
                    f"Failed to process options data: {str(e)}",
                    calculation_type="options_processing",
                    original_error=e,
                    ticker=validated_ticker
                )
        
        # Create successful response
        response_body = json.dumps(response_data)
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