"""
Error handling utilities with categorization and structured responses.
"""
import json
import traceback
from enum import Enum
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone

from .time_utils import format_timestamp_for_api, get_current_utc_timestamp
from .logging_utils import StructuredLogger


class ErrorType(Enum):
    """Error type categorization."""
    DATA_FETCH_ERROR = "DATA_FETCH_ERROR"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class OptionsAnalyticsError(Exception):
    """Base exception for options analytics errors."""
    
    def __init__(self, message: str, error_type: ErrorType, details: Optional[Dict] = None):
        """
        Initialize options analytics error.
        
        Args:
            message: Error message
            error_type: Error type category
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = get_current_utc_timestamp()


class DataFetchError(OptionsAnalyticsError):
    """Error during data fetching operations."""
    
    def __init__(self, message: str, source: str, ticker: Optional[str] = None, details: Optional[Dict] = None):
        """
        Initialize data fetch error.
        
        Args:
            message: Error message
            source: Data source that failed
            ticker: Ticker symbol (if applicable)
            details: Additional error details
        """
        error_details = details or {}
        error_details.update({
            'source': source,
            'ticker': ticker
        })
        super().__init__(message, ErrorType.DATA_FETCH_ERROR, error_details)


class CalculationError(OptionsAnalyticsError):
    """Error during calculation operations."""
    
    def __init__(self, message: str, calculation_type: str, details: Optional[Dict] = None):
        """
        Initialize calculation error.
        
        Args:
            message: Error message
            calculation_type: Type of calculation that failed
            details: Additional error details
        """
        error_details = details or {}
        error_details.update({
            'calculation_type': calculation_type
        })
        super().__init__(message, ErrorType.CALCULATION_ERROR, error_details)


class ValidationError(OptionsAnalyticsError):
    """Error during input validation."""
    
    def __init__(self, message: str, field: str, value: Any, details: Optional[Dict] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            details: Additional error details
        """
        error_details = details or {}
        error_details.update({
            'field': field,
            'value': str(value)
        })
        super().__init__(message, ErrorType.VALIDATION_ERROR, error_details)


class SystemError(OptionsAnalyticsError):
    """System-level error."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        """
        Initialize system error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, ErrorType.SYSTEM_ERROR, details)


class ErrorHandler:
    """Centralized error handling with logging and response formatting."""
    
    def __init__(self, logger: StructuredLogger):
        """
        Initialize error handler.
        
        Args:
            logger: StructuredLogger instance
        """
        self.logger = logger
    
    def handle_error(
        self,
        error: Union[Exception, OptionsAnalyticsError],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Handle error and return formatted response.
        
        Args:
            error: Exception or OptionsAnalyticsError
            context: Additional context information
            
        Returns:
            Formatted error response dictionary
        """
        context = context or {}
        
        if isinstance(error, OptionsAnalyticsError):
            return self._handle_options_analytics_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_options_analytics_error(
        self,
        error: OptionsAnalyticsError,
        context: Dict
    ) -> Dict[str, Any]:
        """Handle OptionsAnalyticsError instances."""
        # Log structured error
        self.logger.error(
            f"{error.error_type.value}: {error.message}",
            error_type=error.error_type.value,
            error_details=error.details,
            context=context
        )
        
        # Determine HTTP status code
        status_code = self._get_status_code_for_error_type(error.error_type)
        
        # Create response
        return self._create_error_response(
            status_code=status_code,
            error_message=error.message,
            error_type=error.error_type.value,
            details=error.details,
            timestamp=error.timestamp
        )
    
    def _handle_generic_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle generic exceptions."""
        # Log error with traceback
        self.logger.error(
            f"Unexpected error: {str(error)}",
            error_type="SYSTEM_ERROR",
            error_class=error.__class__.__name__,
            traceback=traceback.format_exc(),
            context=context
        )
        
        # Create generic error response
        return self._create_error_response(
            status_code=500,
            error_message=f"Internal server error: {str(error)}",
            error_type="SYSTEM_ERROR"
        )
    
    def _get_status_code_for_error_type(self, error_type: ErrorType) -> int:
        """Get appropriate HTTP status code for error type."""
        status_codes = {
            ErrorType.DATA_FETCH_ERROR: 500,
            ErrorType.CALCULATION_ERROR: 500,
            ErrorType.VALIDATION_ERROR: 400,
            ErrorType.SYSTEM_ERROR: 500
        }
        return status_codes.get(error_type, 500)
    
    def _create_error_response(
        self,
        status_code: int,
        error_message: str,
        error_type: str,
        details: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        response_body = {
            'error': error_message,
            'errorType': error_type,
            'timestamp': format_timestamp_for_api(timestamp or get_current_utc_timestamp())
        }
        
        # Add details if provided and not sensitive
        if details:
            # Filter out potentially sensitive information
            safe_details = {
                k: v for k, v in details.items()
                if k not in ['password', 'token', 'key', 'secret', 'api_key']
            }
            if safe_details:
                response_body['details'] = safe_details
        
        return {
            'statusCode': status_code,
            'headers': self._create_cors_headers(),
            'body': json.dumps(response_body)
        }
    
    def _create_cors_headers(self) -> Dict[str, str]:
        """Create CORS headers for error responses."""
        return {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, OPTIONS'
        }
    
    def log_and_raise_data_fetch_error(
        self,
        message: str,
        source: str,
        ticker: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Log and raise a DataFetchError.
        
        Args:
            message: Error message
            source: Data source that failed
            ticker: Ticker symbol
            original_error: Original exception that caused the error
        """
        details = {}
        if original_error:
            details['original_error'] = str(original_error)
            details['original_error_type'] = original_error.__class__.__name__
        
        error = DataFetchError(message, source, ticker, details)
        
        # Log the error
        self.logger.error(
            f"Data fetch failed: {message}",
            error_type=error.error_type.value,
            source=source,
            ticker=ticker,
            original_error=str(original_error) if original_error else None
        )
        
        raise error
    
    def log_and_raise_calculation_error(
        self,
        message: str,
        calculation_type: str,
        original_error: Optional[Exception] = None,
        **kwargs
    ):
        """
        Log and raise a CalculationError.
        
        Args:
            message: Error message
            calculation_type: Type of calculation that failed
            original_error: Original exception that caused the error
            **kwargs: Additional details
        """
        details = kwargs.copy()
        if original_error:
            details['original_error'] = str(original_error)
            details['original_error_type'] = original_error.__class__.__name__
        
        error = CalculationError(message, calculation_type, details)
        
        # Log the error
        self.logger.error(
            f"Calculation failed: {message}",
            error_type=error.error_type.value,
            calculation_type=calculation_type,
            original_error=str(original_error) if original_error else None,
            **kwargs
        )
        
        raise error
    
    def log_and_raise_validation_error(
        self,
        message: str,
        field: str,
        value: Any,
        **kwargs
    ):
        """
        Log and raise a ValidationError.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            **kwargs: Additional details
        """
        error = ValidationError(message, field, value, kwargs)
        
        # Log the error (avoid duplicate field/value in kwargs)
        log_kwargs = {k: v for k, v in kwargs.items() if k not in ['field', 'value']}
        self.logger.error(
            f"Validation failed: {message}",
            error_type=error.error_type.value,
            field=field,
            value=str(value),
            **log_kwargs
        )
        
        raise error


def create_error_handler(logger: StructuredLogger) -> ErrorHandler:
    """
    Create an ErrorHandler instance.
    
    Args:
        logger: StructuredLogger instance
        
    Returns:
        ErrorHandler instance
    """
    return ErrorHandler(logger)