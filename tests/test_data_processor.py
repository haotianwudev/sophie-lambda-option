"""
Unit tests for data processor.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from src.services.data_processor import DataProcessor
from src.models.option_data import OptionData, ExpirationData, MarketData


class TestDataProcessor:
    """Test cases for DataProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataProcessor(risk_free_rate=0.03)
        
        # Sample raw options data
        self.sample_raw_options = {
            "2025-01-17": [
                {
                    "strike": 450.0,
                    "last_price": 2.50,
                    "option_type": "c"
                },
                {
                    "strike": 450.0,
                    "last_price": 1.75,
                    "option_type": "p"
                },
                {
                    "strike": 455.0,
                    "last_price": 1.25,
                    "option_type": "c"
                }
            ],
            "2025-01-24": [
                {
                    "strike": 450.0,
                    "last_price": 3.00,
                    "option_type": "c"
                },
                {
                    "strike": 450.0,
                    "last_price": 2.25,
                    "option_type": "p"
                }
            ]
        }
    
    def test_convert_raw_options_to_objects(self):
        """Test converting raw option dictionaries to OptionData objects."""
        raw_options = [
            {"strike": 450.0, "last_price": 2.50, "option_type": "c"},
            {"strike": 455.0, "last_price": 1.75, "option_type": "p"},
        ]
        
        options = self.processor._convert_raw_options_to_objects(raw_options)
        
        assert len(options) == 2
        assert options[0].strike == 450.0
        assert options[0].last_price == 2.50
        assert options[0].option_type == "c"
        assert options[0].implied_volatility is None
        assert options[0].delta is None
        
        assert options[1].strike == 455.0
        assert options[1].last_price == 1.75
        assert options[1].option_type == "p"
    
    def test_convert_raw_options_invalid_data(self):
        """Test converting raw options with invalid data."""
        raw_options = [
            {"strike": 450.0, "last_price": 2.50, "option_type": "c"},  # Valid
            {"strike": "invalid", "last_price": 2.50, "option_type": "c"},  # Invalid strike
            {"strike": 455.0, "last_price": None, "option_type": "p"},  # None price (should be handled)
            {"strike": 460.0, "option_type": "c"},  # Missing last_price
        ]
        
        options = self.processor._convert_raw_options_to_objects(raw_options)
        
        # Should get 3 valid options (invalid strike filtered out)
        assert len(options) == 3
        assert options[0].strike == 450.0
        assert options[1].strike == 455.0
        assert options[1].last_price is None
        assert options[2].strike == 460.0
    
    @patch('src.services.data_processor.OptionsCalculator')
    def test_structure_options_by_expiration(self, mock_calculator_class):
        """Test structuring options data by expiration date."""
        # Mock the calculator
        mock_calculator = Mock()
        mock_calculator_class.return_value = mock_calculator
        
        # Mock processed options with IV and delta
        mock_processed_calls = [
            OptionData(450.0, 2.50, 0.185, 0.52, 'c'),
            OptionData(455.0, 1.25, 0.190, 0.45, 'c')
        ]
        mock_processed_puts = [
            OptionData(450.0, 1.75, 0.188, -0.48, 'p')
        ]
        
        mock_calculator.process_options_with_iv.side_effect = [
            mock_processed_calls,  # First call for calls
            mock_processed_puts,   # Second call for puts
            [OptionData(450.0, 3.00, 0.175, 0.55, 'c')],  # Third call for second expiration calls
            [OptionData(450.0, 2.25, 0.180, -0.45, 'p')]   # Fourth call for second expiration puts
        ]
        
        # Create new processor to use mocked calculator
        processor = DataProcessor()
        
        result = processor.structure_options_by_expiration(
            self.sample_raw_options, 
            underlying_price=450.25
        )
        
        assert len(result) == 2
        
        # Check first expiration (2025-01-17)
        exp1 = result[0]
        assert exp1.expiration == "2025-01-17"
        assert len(exp1.calls) == 2
        assert len(exp1.puts) == 1
        assert exp1.calls[0].strike == 450.0
        assert exp1.calls[0].implied_volatility == 0.185
        
        # Check second expiration (2025-01-24)
        exp2 = result[1]
        assert exp2.expiration == "2025-01-24"
        assert len(exp2.calls) == 1
        assert len(exp2.puts) == 1
    
    def test_create_market_data_response(self):
        """Test creating complete MarketData object."""
        with patch.object(self.processor, 'structure_options_by_expiration') as mock_structure:
            # Mock the structured expiration data
            mock_expiration = ExpirationData(
                expiration="2025-01-17",
                calls=[OptionData(450.0, 2.50, 0.185, 0.52, 'c')],
                puts=[OptionData(450.0, 1.75, 0.188, -0.48, 'p')]
            )
            mock_structure.return_value = [mock_expiration]
            
            # Test timestamps
            data_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
            vix_timestamp = datetime(2025, 1, 16, 14, 31, 0, tzinfo=timezone.utc)
            
            result = self.processor.create_market_data_response(
                ticker="spy",
                stock_price=450.25,
                vix_value=18.75,
                raw_options_data=self.sample_raw_options,
                data_timestamp=data_timestamp,
                vix_timestamp=vix_timestamp
            )
            
            assert isinstance(result, MarketData)
            assert result.ticker == "SPY"  # Should be uppercase
            assert result.stock_price == 450.25
            assert result.vix_value == 18.75
            assert result.data_timestamp == data_timestamp
            assert result.vix_timestamp == vix_timestamp
            assert len(result.expiration_dates) == 1
            
            # Verify structure_options_by_expiration was called correctly
            mock_structure.assert_called_once_with(self.sample_raw_options, 450.25)
    
    def test_create_market_data_response_default_timestamps(self):
        """Test creating MarketData with default timestamps."""
        with patch.object(self.processor, 'structure_options_by_expiration') as mock_structure:
            mock_structure.return_value = []
            
            with patch('src.services.data_processor.get_current_utc_timestamp') as mock_time:
                mock_timestamp = datetime(2025, 1, 16, 15, 0, 0, tzinfo=timezone.utc)
                mock_time.return_value = mock_timestamp
                
                result = self.processor.create_market_data_response(
                    ticker="AAPL",
                    stock_price=150.00,
                    vix_value=20.00,
                    raw_options_data={}
                )
                
                assert result.data_timestamp == mock_timestamp
                assert result.vix_timestamp == mock_timestamp
    
    def test_format_api_response(self):
        """Test formatting complete API response."""
        with patch.object(self.processor, 'create_market_data_response') as mock_create:
            # Mock MarketData object
            mock_market_data = MarketData(
                ticker="SPY",
                stock_price=450.25,
                vix_value=18.75,
                data_timestamp=datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc),
                vix_timestamp=datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc),
                expiration_dates=[
                    ExpirationData(
                        expiration="2025-01-17",
                        calls=[OptionData(450.0, 2.50, 0.185, 0.52, 'c')],
                        puts=[OptionData(450.0, 1.75, 0.188, -0.48, 'p')]
                    )
                ]
            )
            mock_create.return_value = mock_market_data
            
            result = self.processor.format_api_response(
                ticker="SPY",
                stock_price=450.25,
                vix_value=18.75,
                raw_options_data=self.sample_raw_options
            )
            
            # Verify response structure
            assert result["ticker"] == "SPY"
            assert result["stockPrice"] == 450.25
            assert result["vixValue"] == 18.75
            assert result["dataTimestamp"] == "2025-01-16T14:30:00Z"
            assert result["vixTimestamp"] == "2025-01-16T14:30:00Z"
            assert len(result["expirationDates"]) == 1
            
            exp_data = result["expirationDates"][0]
            assert exp_data["expiration"] == "2025-01-17"
            assert len(exp_data["calls"]) == 1
            assert len(exp_data["puts"]) == 1
            assert exp_data["calls"][0]["strike"] == 450.0
            assert exp_data["calls"][0]["impliedVolatility"] == 0.185
    
    def test_format_api_response_error_handling(self):
        """Test API response formatting with error."""
        with patch.object(self.processor, 'create_market_data_response') as mock_create:
            mock_create.side_effect = ValueError("Test error")
            
            with pytest.raises(ValueError, match="Test error"):
                self.processor.format_api_response(
                    ticker="SPY",
                    stock_price=450.25,
                    vix_value=18.75,
                    raw_options_data=self.sample_raw_options
                )
    
    def test_filter_expiration_dates_by_validity(self):
        """Test filtering expiration dates by minimum options count."""
        expirations = [
            ExpirationData(
                expiration="2025-01-17",
                calls=[OptionData(450.0, 2.50, 0.185, 0.52, 'c')],
                puts=[OptionData(450.0, 1.75, 0.188, -0.48, 'p')]
            ),
            ExpirationData(
                expiration="2025-01-24",
                calls=[],
                puts=[]
            ),
            ExpirationData(
                expiration="2025-01-31",
                calls=[OptionData(455.0, 1.25, 0.190, 0.45, 'c')],
                puts=[]
            )
        ]
        
        # Filter with minimum 1 option
        filtered = self.processor.filter_expiration_dates_by_validity(expirations, min_options_per_expiration=1)
        assert len(filtered) == 2
        assert filtered[0].expiration == "2025-01-17"
        assert filtered[1].expiration == "2025-01-31"
        
        # Filter with minimum 2 options
        filtered = self.processor.filter_expiration_dates_by_validity(expirations, min_options_per_expiration=2)
        assert len(filtered) == 1
        assert filtered[0].expiration == "2025-01-17"
    
    def test_filter_expiration_dates_empty_list(self):
        """Test filtering empty expiration dates list."""
        filtered = self.processor.filter_expiration_dates_by_validity([])
        assert len(filtered) == 0
    
    def test_invalid_ticker_handling(self):
        """Test handling of invalid ticker symbols."""
        with patch.object(self.processor, 'structure_options_by_expiration'):
            with pytest.raises(ValueError, match="Invalid ticker symbol"):
                self.processor.create_market_data_response(
                    ticker="INVALID@TICKER",
                    stock_price=450.25,
                    vix_value=18.75,
                    raw_options_data={}
                )