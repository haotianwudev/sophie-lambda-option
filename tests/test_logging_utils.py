"""
Tests for logging utilities.
"""
import json
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, call
import pytest

from src.utils.logging_utils import (
    StructuredLogger, performance_timer, create_request_logger, configure_root_logger
)


class TestStructuredLogger:
    """Test StructuredLogger functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger_name = "test_logger"
        self.request_id = "test-request-123"
        self.structured_logger = StructuredLogger(self.logger_name, self.request_id)
    
    def test_logger_initialization(self):
        """Test logger initialization with request ID."""
        assert self.structured_logger.request_id == self.request_id
        assert self.structured_logger.logger.name == self.logger_name
    
    def test_logger_initialization_without_request_id(self):
        """Test logger initialization without request ID generates one."""
        logger = StructuredLogger("test")
        assert logger.request_id is not None
        assert len(logger.request_id) > 0
    
    @patch('src.utils.logging_utils.datetime')
    def test_create_log_entry(self, mock_datetime):
        """Test structured log entry creation."""
        # Mock datetime
        mock_timestamp = datetime(2025, 1, 16, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_timestamp
        
        entry = self.structured_logger._create_log_entry(
            'INFO', 
            'Test message',
            custom_field='custom_value'
        )
        
        expected_entry = {
            'timestamp': mock_timestamp.isoformat(),
            'level': 'INFO',
            'message': 'Test message',
            'request_id': self.request_id,
            'logger': self.logger_name,
            'custom_field': 'custom_value'
        }
        
        assert entry == expected_entry
    
    @patch('src.utils.logging_utils.datetime')
    def test_info_logging(self, mock_datetime):
        """Test info level logging."""
        mock_timestamp = datetime(2025, 1, 16, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_timestamp
        
        with patch.object(self.structured_logger.logger, 'info') as mock_info:
            self.structured_logger.info('Test info message', ticker='SPY')
            
            # Verify logger.info was called with JSON string
            mock_info.assert_called_once()
            logged_data = json.loads(mock_info.call_args[0][0])
            
            assert logged_data['level'] == 'INFO'
            assert logged_data['message'] == 'Test info message'
            assert logged_data['ticker'] == 'SPY'
            assert logged_data['request_id'] == self.request_id
    
    @patch('src.utils.logging_utils.datetime')
    def test_error_logging(self, mock_datetime):
        """Test error level logging."""
        mock_timestamp = datetime(2025, 1, 16, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_timestamp
        
        with patch.object(self.structured_logger.logger, 'error') as mock_error:
            self.structured_logger.error('Test error message', error_code=500)
            
            # Verify logger.error was called with JSON string
            mock_error.assert_called_once()
            logged_data = json.loads(mock_error.call_args[0][0])
            
            assert logged_data['level'] == 'ERROR'
            assert logged_data['message'] == 'Test error message'
            assert logged_data['error_code'] == 500
    
    def test_log_performance(self):
        """Test performance logging."""
        with patch.object(self.structured_logger, 'info') as mock_info:
            self.structured_logger.log_performance(
                'data_fetch', 
                2.5, 
                ticker='SPY',
                records_count=100
            )
            
            mock_info.assert_called_once_with(
                'Performance: data_fetch',
                operation='data_fetch',
                duration_seconds=2.5,
                ticker='SPY',
                records_count=100
            )
    
    def test_log_api_request(self):
        """Test API request logging."""
        with patch.object(self.structured_logger, 'info') as mock_info:
            self.structured_logger.log_api_request(
                'GET', 
                '/options-analytics',
                {'ticker': 'SPY'}
            )
            
            mock_info.assert_called_once_with(
                'API Request: GET /options-analytics',
                http_method='GET',
                path='/options-analytics',
                query_params={'ticker': 'SPY'}
            )
    
    def test_log_api_response(self):
        """Test API response logging."""
        with patch.object(self.structured_logger, 'info') as mock_info:
            self.structured_logger.log_api_response(200, 1024)
            
            mock_info.assert_called_once_with(
                'API Response: 200',
                status_code=200,
                response_size=1024
            )
    
    def test_log_data_fetch_success(self):
        """Test successful data fetch logging."""
        with patch.object(self.structured_logger, 'info') as mock_info:
            self.structured_logger.log_data_fetch(
                'yahoo_finance',
                'SPY',
                True,
                stock_price=450.25,
                vix_value=18.5
            )
            
            mock_info.assert_called_once_with(
                'Data fetch from yahoo_finance for SPY: SUCCESS',
                data_source='yahoo_finance',
                ticker='SPY',
                success=True,
                stock_price=450.25,
                vix_value=18.5
            )
    
    def test_log_data_fetch_failure(self):
        """Test failed data fetch logging."""
        with patch.object(self.structured_logger, 'error') as mock_error:
            self.structured_logger.log_data_fetch(
                'yahoo_finance',
                'SPY',
                False,
                error='Connection timeout'
            )
            
            mock_error.assert_called_once_with(
                'Data fetch from yahoo_finance for SPY: FAILED',
                data_source='yahoo_finance',
                ticker='SPY',
                success=False,
                error='Connection timeout'
            )
    
    def test_log_calculation(self):
        """Test calculation logging."""
        with patch.object(self.structured_logger, 'info') as mock_info:
            self.structured_logger.log_calculation(
                'implied_volatility',
                100,
                85,
                expiration_date='2025-01-17'
            )
            
            mock_info.assert_called_once_with(
                'Calculation: implied_volatility',
                calculation_type='implied_volatility',
                total_count=100,
                success_count=85,
                success_rate=85.0,
                expiration_date='2025-01-17'
            )
    
    def test_log_calculation_zero_count(self):
        """Test calculation logging with zero count."""
        with patch.object(self.structured_logger, 'info') as mock_info:
            self.structured_logger.log_calculation('delta', 0, 0)
            
            mock_info.assert_called_once_with(
                'Calculation: delta',
                calculation_type='delta',
                total_count=0,
                success_count=0,
                success_rate=0
            )


class TestPerformanceTimer:
    """Test performance timer context manager."""
    
    def test_performance_timer_success(self):
        """Test performance timer with successful operation."""
        mock_logger = Mock(spec=StructuredLogger)
        
        with performance_timer(mock_logger, 'test_operation', ticker='SPY'):
            time.sleep(0.01)  # Small delay to ensure measurable time
        
        # Verify log_performance was called
        mock_logger.log_performance.assert_called_once()
        call_args = mock_logger.log_performance.call_args
        
        assert call_args[0][0] == 'test_operation'  # operation name
        assert call_args[0][1] > 0  # duration should be positive
        assert call_args[1]['ticker'] == 'SPY'  # additional kwargs
    
    def test_performance_timer_with_exception(self):
        """Test performance timer when operation raises exception."""
        mock_logger = Mock(spec=StructuredLogger)
        
        with pytest.raises(ValueError):
            with performance_timer(mock_logger, 'failing_operation'):
                raise ValueError("Test error")
        
        # Verify log_performance was still called despite exception
        mock_logger.log_performance.assert_called_once()
        call_args = mock_logger.log_performance.call_args
        assert call_args[0][0] == 'failing_operation'


class TestCreateRequestLogger:
    """Test create_request_logger function."""
    
    def test_create_request_logger_with_event(self):
        """Test creating request logger with API Gateway event."""
        event = {
            'requestContext': {
                'requestId': 'api-gateway-request-123'
            }
        }
        
        logger = create_request_logger('test_handler', event)
        
        assert logger.request_id == 'api-gateway-request-123'
        assert logger.logger.name == 'test_handler'
    
    def test_create_request_logger_without_event(self):
        """Test creating request logger without event."""
        logger = create_request_logger('test_handler')
        
        assert logger.request_id is not None
        assert len(logger.request_id) > 0
        assert logger.logger.name == 'test_handler'
    
    def test_create_request_logger_with_empty_event(self):
        """Test creating request logger with empty event."""
        event = {}
        
        logger = create_request_logger('test_handler', event)
        
        assert logger.request_id is not None
        assert logger.logger.name == 'test_handler'
    
    def test_create_request_logger_with_event_no_request_context(self):
        """Test creating request logger with event missing requestContext."""
        event = {
            'httpMethod': 'GET',
            'path': '/options-analytics'
        }
        
        logger = create_request_logger('test_handler', event)
        
        assert logger.request_id is not None
        assert logger.logger.name == 'test_handler'


class TestConfigureRootLogger:
    """Test configure_root_logger function."""
    
    @patch('src.utils.logging_utils.logging.getLogger')
    def test_configure_root_logger(self, mock_get_logger):
        """Test root logger configuration."""
        mock_root_logger = Mock()
        mock_root_logger.handlers = [Mock(), Mock()]  # Existing handlers
        mock_get_logger.return_value = mock_root_logger
        
        configure_root_logger()
        
        # Verify existing handlers were removed
        assert mock_root_logger.removeHandler.call_count == 2
        
        # Verify new handler was added
        mock_root_logger.addHandler.assert_called_once()
        
        # Verify log level was set
        mock_root_logger.setLevel.assert_called_once()


class TestLoggingIntegration:
    """Integration tests for logging functionality."""
    
    def test_full_request_logging_flow(self):
        """Test complete request logging flow."""
        # Create logger with request ID
        event = {
            'requestContext': {'requestId': 'req-123'},
            'httpMethod': 'GET',
            'path': '/options-analytics',
            'queryStringParameters': {'ticker': 'SPY'}
        }
        
        logger = create_request_logger('handler', event)
        
        # Mock the underlying logger to capture calls
        with patch.object(logger.logger, 'info') as mock_info, \
             patch.object(logger.logger, 'error') as mock_error:
            
            # Log API request
            logger.log_api_request('GET', '/options-analytics', {'ticker': 'SPY'})
            
            # Log data fetch
            logger.log_data_fetch('yahoo_finance', 'SPY', True, stock_price=450.25)
            
            # Log calculation
            logger.log_calculation('implied_volatility', 50, 45)
            
            # Log performance
            logger.log_performance('total_request', 1.25, ticker='SPY')
            
            # Log API response
            logger.log_api_response(200, 2048)
            
            # Log error
            logger.error('Test error', error_type='TEST_ERROR')
            
            # Verify all logging calls were made
            assert mock_info.call_count == 5  # 5 info calls
            assert mock_error.call_count == 1  # 1 error call
            
            # Verify all logs contain request ID
            for call_args in mock_info.call_args_list:
                logged_data = json.loads(call_args[0][0])
                assert logged_data['request_id'] == 'req-123'
            
            # Verify error log contains request ID
            error_call_args = mock_error.call_args_list[0]
            logged_error_data = json.loads(error_call_args[0][0])
            assert logged_error_data['request_id'] == 'req-123'
    
    def test_performance_logging_accuracy(self):
        """Test that performance logging captures accurate timing."""
        logger = StructuredLogger('test')
        
        with patch.object(logger, 'log_performance') as mock_log_perf:
            start_time = time.time()
            
            with performance_timer(logger, 'test_op'):
                time.sleep(0.1)  # Sleep for 100ms
            
            end_time = time.time()
            actual_duration = end_time - start_time
            
            # Verify log_performance was called
            mock_log_perf.assert_called_once()
            logged_duration = mock_log_perf.call_args[0][1]
            
            # Duration should be close to actual (within 10ms tolerance)
            assert abs(logged_duration - actual_duration) < 0.01