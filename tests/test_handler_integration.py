"""
Integration tests for the main Lambda handler with comprehensive error handling.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from handler import get_options_analytics, convert_expiration_data_to_dict
from src.models.option_data import OptionData, ExpirationData
from src.utils.error_handling import DataFetchError, ValidationError, CalculationError


class TestHandlerIntegration:
    """Integration tests for the Lambda handler with error handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_event = {
            'httpMethod': 'GET',
            'path': '/options-analytics',
            'queryStringParameters': {'ticker': 'SPY'},
            'requestContext': {'requestId': 'test-request-123'}
        }
        self.sample_context = {}
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    @patch('handler.DataProcessor')
    def test_successful_request_flow_with_logging(self, mock_data_processor, mock_options_fetcher, mock_market_fetcher):
        """Test successful request processing flow with comprehensive logging."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_market_data.return_value = (
            450.25,  # stock_price
            18.5,    # vix_value
            datetime.now(timezone.utc),  # stock_timestamp
            datetime.now(timezone.utc)   # vix_timestamp
        )
        
        # Mock options data fetcher
        mock_options_instance = mock_options_fetcher.return_value
        sample_expiration_data = [
            ExpirationData(
                expiration="2025-01-17",
                calls=[OptionData(strike=450.0, last_price=2.5, implied_volatility=None, delta=None, option_type='c')],
                puts=[OptionData(strike=450.0, last_price=1.8, implied_volatility=None, delta=None, option_type='p')]
            )
        ]
        mock_options_instance.fetch_all_option_chains.return_value = sample_expiration_data
        
        # Mock data processor
        mock_processor_instance = mock_data_processor.return_value
        mock_processor_instance.format_api_response.return_value = {
            "ticker": "SPY",
            "stockPrice": 450.25,
            "vixValue": 18.5,
            "expirationDates": [
                {
                    "expiration": "2025-01-17",
                    "calls": [{"strike": 450.0, "lastPrice": 2.5, "impliedVolatility": 0.18, "delta": 0.52}],
                    "puts": [{"strike": 450.0, "lastPrice": 1.8, "impliedVolatility": 0.17, "delta": -0.48}]
                }
            ]
        }
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response structure
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        # Verify response body
        body = json.loads(response['body'])
        assert body['ticker'] == 'SPY'
        assert body['stockPrice'] == 450.25
        assert body['vixValue'] == 18.5
        assert len(body['expirationDates']) == 1
    
    def test_invalid_ticker_validation_error(self):
        """Test handling of invalid ticker symbols with proper error categorization."""
        invalid_event = {
            'httpMethod': 'GET',
            'path': '/options-analytics',
            'queryStringParameters': {'ticker': 'INVALID@TICKER'},
            'requestContext': {'requestId': 'test-request-456'}
        }
        
        response = get_options_analytics(invalid_event, self.sample_context)
        
        # Verify error response
        assert response['statusCode'] == 400  # Validation errors should return 400
        body = json.loads(response['body'])
        assert body['errorType'] == 'VALIDATION_ERROR'
        assert 'Invalid ticker symbol' in body['error']
        assert 'timestamp' in body
        assert 'details' in body
        assert body['details']['field'] == 'ticker'
        assert body['details']['value'] == 'INVALID@TICKER'
    
    @patch('handler.MarketDataFetcher')
    def test_market_data_fetch_error_with_logging(self, mock_market_fetcher):
        """Test handling of market data fetch errors with structured logging."""
        # Mock market data fetcher to raise error
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_market_data.side_effect = RuntimeError("Connection timeout after 30 seconds")
        
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['errorType'] == 'DATA_FETCH_ERROR'
        assert 'Failed to fetch market data' in body['error']
        assert 'Connection timeout' in body['error']
        assert 'timestamp' in body
        assert 'details' in body
        assert body['details']['source'] == 'market_data'
        assert body['details']['ticker'] == 'SPY'
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_options_data_fetch_error_with_context(self, mock_options_fetcher, mock_market_fetcher):
        """Test handling of options data fetch errors with context logging."""
        # Mock successful market data fetch
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_market_data.return_value = (
            450.25, 18.5, datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
        
        # Mock options data fetcher to raise error
        mock_options_instance = mock_options_fetcher.return_value
        mock_options_instance.fetch_all_option_chains.side_effect = RuntimeError("No options data available for ticker")
        
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['errorType'] == 'DATA_FETCH_ERROR'
        assert 'Failed to fetch options data' in body['error']
        assert 'details' in body
        assert body['details']['source'] == 'options_data'
        assert body['details']['ticker'] == 'SPY'
        assert body['details']['original_error'] == 'No options data available for ticker'
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_no_expiration_dates_error_with_details(self, mock_options_fetcher, mock_market_fetcher):
        """Test handling when no expiration dates are found with detailed error info."""
        # Mock successful market data fetch
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_market_data.return_value = (
            450.25, 18.5, datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
        
        # Mock options data fetcher to return empty list
        mock_options_instance = mock_options_fetcher.return_value
        mock_options_instance.fetch_all_option_chains.return_value = []
        
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['errorType'] == 'DATA_FETCH_ERROR'
        assert 'No option expiration dates found for ticker SPY' in body['error']
        assert 'details' in body
        assert body['details']['source'] == 'options_data'
        assert body['details']['ticker'] == 'SPY'
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    @patch('handler.DataProcessor')
    def test_data_processing_calculation_error(self, mock_data_processor, mock_options_fetcher, mock_market_fetcher):
        """Test handling of data processing errors as calculation errors."""
        # Mock successful market and options data fetch
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_market_data.return_value = (
            450.25, 18.5, datetime.now(timezone.utc), datetime.now(timezone.utc)
        )
        
        mock_options_instance = mock_options_fetcher.return_value
        sample_expiration_data = [
            ExpirationData(
                expiration="2025-01-17",
                calls=[OptionData(strike=450.0, last_price=2.5, implied_volatility=None, delta=None, option_type='c')],
                puts=[]
            )
        ]
        mock_options_instance.fetch_all_option_chains.return_value = sample_expiration_data
        
        # Mock data processor to raise error
        mock_processor_instance = mock_data_processor.return_value
        mock_processor_instance.format_api_response.side_effect = ValueError("Invalid option price for IV calculation")
        
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['errorType'] == 'CALCULATION_ERROR'
        assert 'Failed to process options data' in body['error']
        assert 'details' in body
        assert body['details']['calculation_type'] == 'options_processing'
        assert body['details']['ticker'] == 'SPY'
    
    def test_unexpected_system_error_handling(self):
        """Test handling of unexpected system errors."""
        # Create an event that will cause an unexpected error
        malformed_event = {
            'httpMethod': 'GET',
            'path': '/options-analytics',
            'queryStringParameters': {'ticker': 'SPY'},
            'requestContext': {'requestId': 'test-request-789'}
        }
        
        # Patch validate_ticker_symbol to raise an unexpected error
        with patch('handler.validate_ticker_symbol', side_effect=AttributeError("Unexpected attribute error")):
            response = get_options_analytics(malformed_event, self.sample_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['errorType'] == 'SYSTEM_ERROR'
        assert 'Internal server error' in body['error']
        assert 'timestamp' in body
    
    def test_performance_logging_in_successful_request(self):
        """Test that performance metrics are logged during successful requests."""
        with patch('handler.MarketDataFetcher') as mock_market_fetcher, \
             patch('handler.OptionsDataFetcher') as mock_options_fetcher, \
             patch('handler.DataProcessor') as mock_data_processor, \
             patch('handler.create_request_logger') as mock_create_logger:
            
            # Mock logger
            mock_logger = Mock()
            mock_create_logger.return_value = mock_logger
            
            # Mock successful responses
            mock_market_instance = mock_market_fetcher.return_value
            mock_market_instance.fetch_market_data.return_value = (
                450.25, 18.5, datetime.now(timezone.utc), datetime.now(timezone.utc)
            )
            
            mock_options_instance = mock_options_fetcher.return_value
            mock_options_instance.fetch_all_option_chains.return_value = [
                ExpirationData(expiration="2025-01-17", calls=[], puts=[])
            ]
            
            mock_processor_instance = mock_data_processor.return_value
            mock_processor_instance.format_api_response.return_value = {
                "ticker": "SPY",
                "expirationDates": [{"expiration": "2025-01-17", "calls": [], "puts": []}]
            }
            
            response = get_options_analytics(self.sample_event, self.sample_context)
            
            # Verify performance logging was called
            assert mock_logger.log_performance.call_count >= 3  # At least market_data_fetch, options_data_fetch, data_processing
            assert mock_logger.log_api_request.called
            assert mock_logger.log_api_response.called
            assert mock_logger.log_data_fetch.call_count >= 2  # market_data and options_data
    
    def test_request_id_propagation(self):
        """Test that request ID is properly propagated through logging."""
        with patch('handler.create_request_logger') as mock_create_logger:
            mock_logger = Mock()
            mock_create_logger.return_value = mock_logger
            
            # Mock error to trigger error handling
            with patch('handler.validate_ticker_symbol', side_effect=ValueError("Test error")):
                response = get_options_analytics(self.sample_event, self.sample_context)
            
            # Verify create_request_logger was called with event
            mock_create_logger.assert_called_once_with('handler', self.sample_event)
    
    def test_cors_headers_in_all_error_responses(self):
        """Test that CORS headers are present in all error responses."""
        test_cases = [
            # Validation error
            {
                'event': {
                    'httpMethod': 'GET',
                    'path': '/options-analytics',
                    'queryStringParameters': {'ticker': 'INVALID@TICKER'},
                    'requestContext': {'requestId': 'test-1'}
                },
                'expected_status': 400
            },
            # System error
            {
                'event': {
                    'httpMethod': 'GET',
                    'path': '/options-analytics',
                    'queryStringParameters': {'ticker': 'SPY'},
                    'requestContext': {'requestId': 'test-2'}
                },
                'expected_status': 500,
                'patch_target': 'handler.MarketDataFetcher',
                'patch_side_effect': RuntimeError("Test error")
            }
        ]
        
        for test_case in test_cases:
            if 'patch_target' in test_case:
                with patch(test_case['patch_target']) as mock_service:
                    mock_instance = mock_service.return_value
                    mock_instance.fetch_market_data.side_effect = test_case['patch_side_effect']
                    response = get_options_analytics(test_case['event'], self.sample_context)
            else:
                response = get_options_analytics(test_case['event'], self.sample_context)
            
            # Verify CORS headers
            assert response['statusCode'] == test_case['expected_status']
            headers = response['headers']
            assert headers['Access-Control-Allow-Origin'] == '*'
            assert headers['Access-Control-Allow-Headers'] == 'Content-Type'
            assert headers['Access-Control-Allow-Methods'] == 'GET, OPTIONS'
    
    def test_error_response_structure_consistency(self):
        """Test that all error responses have consistent structure."""
        # Test validation error
        invalid_event = {
            'httpMethod': 'GET',
            'path': '/options-analytics',
            'queryStringParameters': {'ticker': 'INVALID@TICKER'},
            'requestContext': {'requestId': 'test-request'}
        }
        
        response = get_options_analytics(invalid_event, self.sample_context)
        body = json.loads(response['body'])
        
        # Verify required fields
        required_fields = ['error', 'errorType', 'timestamp']
        for field in required_fields:
            assert field in body, f"Missing required field: {field}"
        
        # Verify error type is valid
        valid_error_types = ['DATA_FETCH_ERROR', 'CALCULATION_ERROR', 'SYSTEM_ERROR', 'VALIDATION_ERROR']
        assert body['errorType'] in valid_error_types
        
        # Verify timestamp format
        assert body['timestamp'].endswith('Z')  # ISO format with Z suffix


class TestConvertExpirationDataToDict:
    """Test the convert_expiration_data_to_dict helper function."""
    
    def test_convert_expiration_data_to_dict(self):
        """Test conversion of ExpirationData objects to dictionary format."""
        expiration_data_list = [
            ExpirationData(
                expiration="2025-01-17",
                calls=[
                    OptionData(strike=450.0, last_price=2.5, implied_volatility=0.18, delta=0.52, option_type='c'),
                    OptionData(strike=455.0, last_price=1.8, implied_volatility=0.19, delta=0.45, option_type='c')
                ],
                puts=[
                    OptionData(strike=450.0, last_price=1.9, implied_volatility=0.17, delta=-0.48, option_type='p')
                ]
            ),
            ExpirationData(
                expiration="2025-01-24",
                calls=[
                    OptionData(strike=450.0, last_price=3.2, implied_volatility=0.20, delta=0.55, option_type='c')
                ],
                puts=[]
            )
        ]
        
        result = convert_expiration_data_to_dict(expiration_data_list)
        
        # Verify structure
        assert "2025-01-17" in result
        assert "2025-01-24" in result
        
        # Verify 2025-01-17 data
        jan_17_options = result["2025-01-17"]
        assert len(jan_17_options) == 3  # 2 calls + 1 put
        
        # Check call options
        call_options = [opt for opt in jan_17_options if opt['option_type'] == 'c']
        assert len(call_options) == 2
        assert call_options[0]['strike'] == 450.0
        assert call_options[0]['last_price'] == 2.5
        assert call_options[1]['strike'] == 455.0
        assert call_options[1]['last_price'] == 1.8
        
        # Check put options
        put_options = [opt for opt in jan_17_options if opt['option_type'] == 'p']
        assert len(put_options) == 1
        assert put_options[0]['strike'] == 450.0
        assert put_options[0]['last_price'] == 1.9
        
        # Verify 2025-01-24 data
        jan_24_options = result["2025-01-24"]
        assert len(jan_24_options) == 1  # 1 call + 0 puts
        assert jan_24_options[0]['option_type'] == 'c'
        assert jan_24_options[0]['strike'] == 450.0
    
    def test_convert_empty_expiration_data(self):
        """Test conversion with empty expiration data list."""
        result = convert_expiration_data_to_dict([])
        assert result == {}
    
    def test_convert_expiration_data_with_empty_options(self):
        """Test conversion with expiration dates that have no options."""
        expiration_data_list = [
            ExpirationData(
                expiration="2025-01-17",
                calls=[],
                puts=[]
            )
        ]
        
        result = convert_expiration_data_to_dict(expiration_data_list)
        
        assert "2025-01-17" in result
        assert result["2025-01-17"] == []