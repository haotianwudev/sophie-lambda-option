"""
Logging utilities for structured logging and request tracing.
"""
import json
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class StructuredLogger:
    """Structured logger with request tracing and performance monitoring."""
    
    def __init__(self, name: str, request_id: Optional[str] = None):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            request_id: Optional request ID for tracing
        """
        self.logger = logging.getLogger(name)
        self.request_id = request_id or str(uuid.uuid4())
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _create_log_entry(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Create structured log entry.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields
            
        Returns:
            Structured log entry dictionary
        """
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'message': message,
            'request_id': self.request_id,
            'logger': self.logger.name
        }
        
        # Add additional fields
        entry.update(kwargs)
        
        return entry
    
    def info(self, message: str, **kwargs):
        """Log info message with structured format."""
        entry = self._create_log_entry('INFO', message, **kwargs)
        self.logger.info(json.dumps(entry))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured format."""
        entry = self._create_log_entry('WARNING', message, **kwargs)
        self.logger.warning(json.dumps(entry))
    
    def error(self, message: str, **kwargs):
        """Log error message with structured format."""
        entry = self._create_log_entry('ERROR', message, **kwargs)
        self.logger.error(json.dumps(entry))
    
    def debug(self, message: str, **kwargs):
        """Log debug message with structured format."""
        entry = self._create_log_entry('DEBUG', message, **kwargs)
        self.logger.debug(json.dumps(entry))
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """
        Log performance metrics.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            **kwargs: Additional metrics
        """
        self.info(
            f"Performance: {operation}",
            operation=operation,
            duration_seconds=round(duration, 4),
            **kwargs
        )
    
    def log_api_request(self, method: str, path: str, query_params: Optional[Dict] = None):
        """
        Log API request details.
        
        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
        """
        self.info(
            f"API Request: {method} {path}",
            http_method=method,
            path=path,
            query_params=query_params or {}
        )
    
    def log_api_response(self, status_code: int, response_size: Optional[int] = None):
        """
        Log API response details.
        
        Args:
            status_code: HTTP status code
            response_size: Response size in bytes
        """
        self.info(
            f"API Response: {status_code}",
            status_code=status_code,
            response_size=response_size
        )
    
    def log_data_fetch(self, source: str, ticker: str, success: bool, **kwargs):
        """
        Log data fetching operations.
        
        Args:
            source: Data source name
            ticker: Ticker symbol
            success: Whether fetch was successful
            **kwargs: Additional details
        """
        level = 'info' if success else 'error'
        message = f"Data fetch from {source} for {ticker}: {'SUCCESS' if success else 'FAILED'}"
        
        getattr(self, level)(
            message,
            data_source=source,
            ticker=ticker,
            success=success,
            **kwargs
        )
    
    def log_calculation(self, calculation_type: str, count: int, success_count: int, **kwargs):
        """
        Log calculation operations.
        
        Args:
            calculation_type: Type of calculation
            count: Total number of calculations attempted
            success_count: Number of successful calculations
            **kwargs: Additional details
        """
        success_rate = (success_count / count * 100) if count > 0 else 0
        
        self.info(
            f"Calculation: {calculation_type}",
            calculation_type=calculation_type,
            total_count=count,
            success_count=success_count,
            success_rate=round(success_rate, 2),
            **kwargs
        )


@contextmanager
def performance_timer(logger: StructuredLogger, operation: str, **kwargs):
    """
    Context manager for timing operations.
    
    Args:
        logger: StructuredLogger instance
        operation: Operation name
        **kwargs: Additional context
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.log_performance(operation, duration, **kwargs)


def create_request_logger(name: str, event: Optional[Dict] = None) -> StructuredLogger:
    """
    Create a request logger with request ID from Lambda event.
    
    Args:
        name: Logger name
        event: Lambda event object
        
    Returns:
        StructuredLogger instance
    """
    request_id = None
    
    if event:
        # Try to extract request ID from API Gateway event
        request_context = event.get('requestContext', {})
        request_id = request_context.get('requestId')
    
    return StructuredLogger(name, request_id)


def configure_root_logger():
    """Configure root logger for Lambda environment."""
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add new handler with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)