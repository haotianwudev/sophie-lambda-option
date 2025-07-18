"""
Tests for error handling utilities.
"""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.utils.error_handling import (
    ErrorType, OptionsAnalyticsError, DataFetchError, CalculationError,
    ValidationError, SystemError, ErrorHandler
)
from src.utils.logging_utils import StructuredLogger


class TestOptionsAnalyticsError:
    """Test OptionsAnalyticsError and its subclasses."""
    
    def test_options_analytics_error_creation(self):
        """Test basic OptionsAnalyticsError creation."""
        error = OptionsAnalyticsError(
            "Test error",
            ErrorType.SYSTEM_ERROR,
            {"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.error_type == ErrorType.SYSTEM_ERROR
        assert error.details == {"key": "value"}
        assert isinstance(error.timestamp, datetime)
    
    def test_data_fetch_error_creation(self):
        """Test DataFetchError creation with source and ticker."""
        error = DataFetchError(
            "Failed to fetch data",
            source="yahoo_finance",
            ticker="SPY",
            details={"timeout": True}
        )
        
        assert error.message == "Failed to fetch data"
        assert error.error_type == ErrorType.DATA_FETCH_ERROR
        assert error.details["source"] == "yahoo_finance"
        assert error.details["ticker"] == "SPY"
        assert error.details["timeout"] is True
    
    def test_calculation_error_creation(self):
        """Test CalculationError creation."""
        error = CalculationError(
            "IV calculation failed",
            calculation_type="implied_volatility",
            details={"strike": 450.0}
        )
        
        assert error.message == "IV calculation failed"
        assert error.error_type == ErrorType.CALCULATION_ERROR
        assert error.details["calculation_type"] == "implied_volatility"
        assert error.details["strike"] == 450.0
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError(
            "Invalid ticker",
            field="ticker",
            value="INVALID@TICKER",
            details={"reason": "contains_special_chars"}
        )
        
        assert error.message == "Invalid ticker"
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.details["field"] == "ticker"
        assert error.details["value"] == "INVALID@TICKER"
        assert error.details["reason"] == "contains_special_chars"
    
    def test_system_error_creation(self):
        """Test SystemError creation."""
        error = SystemError(
            "Lambda timeout",
            details={"timeout_seconds": 30}
        )
        
        assert error.message == "Lambda timeout"
        assert error.error_type == ErrorType.SYSTEM_ERROR
        assert error.details["timeout_seconds"] == 30


class TestErrorHandler:
    """Test ErrorHandler functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock(spec=StructuredLogger)
        self.error_handler = ErrorHandler(self.mock_logger)
    
    def test_handle_options_analytics_error(self):
        """Test handling of OptionsAnalyticsError."""
        error = DataFetchError(
            "Failed to fetch market data",
            source="yahoo_finance",
            ticker="SPY"
        )
        
        response = self.error_handler.handle_error(error)
        
        # Verify response structure
        assert response["statusCode"] == 500
        assert "headers" in response
        assert "body" in response
        
        # Parse response body
        body = json.loads(response["body"])
        assert body["error"] == "Failed to fetch market data"
        assert body["errorType"] == "DATA_FETCH_ERROR"
        assert "timestamp" in body
        assert "details" in body
        assert body["details"]["source"] == "yahoo_finance"
        assert body["details"]["ticker"] == "SPY"
        
        # Verify logging was called
        self.mock_logger.error.assert_called_once()
    
    def test_handle_generic_error(self):
        """Test handling of generic exceptions."""
        error = ValueError("Invalid input")
        
        response = self.error_handler.handle_error(error)
        
        # Verify response structure
        assert response["statusCode"] == 500
        assert "headers" in response
        assert "body" in response
        
        # Parse response body
        body = json.loads(response["body"])
        assert "Internal server error: Invalid input" in body["error"]
        assert body["errorType"] == "SYSTEM_ERROR"
        assert "timestamp" in body
        
        # Verify logging was called
        self.mock_logger.error.assert_called_once()
    
    def test_validation_error_status_code(self):
        """Test that validation errors return 400 status code."""
        error = ValidationError(
            "Invalid ticker",
            field="ticker",
            value="INVALID"
        )
        
        response = self.error_handler.handle_error(error)
        assert response["statusCode"] == 400
    
    def test_cors_headers_in_error_response(self):
        """Test that CORS headers are included in error responses."""
        error = SystemError("Test error")
        
        response = self.error_handler.handle_error(error)
        
        headers = response["headers"]
        assert headers["Content-Type"] == "application/json"
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Access-Control-Allow-Headers"] == "Content-Type"
        assert headers["Access-Control-Allow-Methods"] == "GET, OPTIONS"
    
    def test_log_and_raise_data_fetch_error(self):
        """Test log_and_raise_data_fetch_error method."""
        original_error = ConnectionError("Network timeout")
        
        with pytest.raises(DataFetchError) as exc_info:
            self.error_handler.log_and_raise_data_fetch_error(
                "Failed to connect to API",
                source="yahoo_finance",
                ticker="AAPL",
                original_error=original_error
            )
        
        error = exc_info.value
        assert error.message == "Failed to connect to API"
        assert error.details["source"] == "yahoo_finance"
        assert error.details["ticker"] == "AAPL"
        assert error.details["original_error"] == "Network timeout"
        assert error.details["original_error_type"] == "ConnectionError"
        
        # Verify logging was called
        self.mock_logger.error.assert_called_once()
    
    def test_log_and_raise_calculation_error(self):
        """Test log_and_raise_calculation_error method."""
        original_error = ZeroDivisionError("Division by zero")
        
        with pytest.raises(CalculationError) as exc_info:
            self.error_handler.log_and_raise_calculation_error(
                "IV calculation failed",
                calculation_type="implied_volatility",
                original_error=original_error,
                strike=450.0,
                option_price=2.5
            )
        
        error = exc_info.value
        assert error.message == "IV calculation failed"
        assert error.details["calculation_type"] == "implied_volatility"
        assert error.details["strike"] == 450.0
        assert error.details["option_price"] == 2.5
        assert error.details["original_error"] == "Division by zero"
        
        # Verify logging was called
        self.mock_logger.error.assert_called_once()
    
    def test_log_and_raise_validation_error(self):
        """Test log_and_raise_validation_error method."""
        with pytest.raises(ValidationError) as exc_info:
            self.error_handler.log_and_raise_validation_error(
                "Invalid ticker format",
                field="ticker",
                value="INVALID@TICKER",
                reason="contains_special_chars"
            )
        
        error = exc_info.value
        assert error.message == "Invalid ticker format"
        assert error.details["field"] == "ticker"
        assert error.details["value"] == "INVALID@TICKER"
        assert error.details["reason"] == "contains_special_chars"
        
        # Verify logging was called
        self.mock_logger.error.assert_called_once()
    
    def test_sensitive_data_filtering(self):
        """Test that sensitive data is filtered from error responses."""
        error = SystemError(
            "Authentication failed",
            details={
                "username": "testuser",
                "password": "secret123",
                "api_key": "abc123",
                "token": "xyz789",
                "timeout": 30
            }
        )
        
        response = self.error_handler.handle_error(error)
        body = json.loads(response["body"])
        
        # Sensitive fields should be filtered out
        assert "password" not in body["details"]
        assert "api_key" not in body["details"]
        assert "token" not in body["details"]
        
        # Non-sensitive fields should remain
        assert body["details"]["username"] == "testuser"
        assert body["details"]["timeout"] == 30
    
    def test_error_context_logging(self):
        """Test that error context is properly logged."""
        error = DataFetchError("Test error", "test_source")
        context = {"ticker": "SPY", "request_id": "123"}
        
        self.error_handler.handle_error(error, context)
        
        # Verify context was passed to logger
        call_args = self.mock_logger.error.call_args
        assert call_args[1]["context"] == context


class TestErrorIntegration:
    """Integration tests for error handling in realistic scenarios."""
    
    def test_market_data_fetch_error_scenario(self):
        """Test error handling for market data fetch failures."""
        mock_logger = Mock(spec=StructuredLogger)
        error_handler = ErrorHandler(mock_logger)
        
        # Simulate network timeout during market data fetch
        original_error = TimeoutError("Request timed out after 30 seconds")
        
        with pytest.raises(DataFetchError) as exc_info:
            error_handler.log_and_raise_data_fetch_error(
                "Failed to fetch stock price for SPY",
                source="yahoo_finance",
                ticker="SPY",
                original_error=original_error
            )
        
        error = exc_info.value
        response = error_handler.handle_error(error)
        
        # Verify error response
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["errorType"] == "DATA_FETCH_ERROR"
        assert "SPY" in body["error"]
        assert body["details"]["source"] == "yahoo_finance"
    
    def test_calculation_error_scenario(self):
        """Test error handling for calculation failures."""
        mock_logger = Mock(spec=StructuredLogger)
        error_handler = ErrorHandler(mock_logger)
        
        # Simulate IV calculation failure
        with pytest.raises(CalculationError) as exc_info:
            error_handler.log_and_raise_calculation_error(
                "Implied volatility calculation failed for deep OTM option",
                calculation_type="implied_volatility",
                strike=600.0,
                option_price=0.01,
                underlying_price=450.0
            )
        
        error = exc_info.value
        response = error_handler.handle_error(error)
        
        # Verify error response
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["errorType"] == "CALCULATION_ERROR"
        assert "implied volatility" in body["error"].lower()
        assert body["details"]["strike"] == 600.0
    
    def test_validation_error_scenario(self):
        """Test error handling for input validation failures."""
        mock_logger = Mock(spec=StructuredLogger)
        error_handler = ErrorHandler(mock_logger)
        
        # Simulate invalid ticker validation
        with pytest.raises(ValidationError) as exc_info:
            error_handler.log_and_raise_validation_error(
                "Ticker symbol contains invalid characters",
                field="ticker",
                value="SPY@123",
                allowed_chars="alphanumeric and dots/dashes only"
            )
        
        error = exc_info.value
        response = error_handler.handle_error(error)
        
        # Verify error response
        assert response["statusCode"] == 400  # Bad Request for validation errors
        body = json.loads(response["body"])
        assert body["errorType"] == "VALIDATION_ERROR"
        assert "invalid characters" in body["error"]
        assert body["details"]["field"] == "ticker"
        assert body["details"]["value"] == "SPY@123"