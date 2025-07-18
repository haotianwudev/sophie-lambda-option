"""
Integration tests for data processor with real-world scenarios.
"""
import pytest
from datetime import datetime, timezone
from src.services.data_processor import DataProcessor


class TestDataProcessorIntegration:
    """Integration tests for complete data processing workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataProcessor(risk_free_rate=0.03)
        
        # Realistic options data sample
        self.realistic_options_data = {
            "2025-01-17": [
                # ATM calls
                {"strike": 450.0, "last_price": 2.50, "option_type": "c"},
                {"strike": 451.0, "last_price": 2.25, "option_type": "c"},
                {"strike": 452.0, "last_price": 2.00, "option_type": "c"},
                # ATM puts
                {"strike": 450.0, "last_price": 1.75, "option_type": "p"},
                {"strike": 451.0, "last_price": 2.00, "option_type": "p"},
                {"strike": 452.0, "last_price": 2.25, "option_type": "p"},
                # OTM calls
                {"strike": 455.0, "last_price": 1.25, "option_type": "c"},
                {"strike": 460.0, "last_price": 0.75, "option_type": "c"},
                # OTM puts
                {"strike": 445.0, "last_price": 0.50, "option_type": "p"},
                {"strike": 440.0, "last_price": 0.25, "option_type": "p"},
                # Invalid options (should be filtered out)
                {"strike": 0.0, "last_price": 1.00, "option_type": "c"},  # Invalid strike
                {"strike": 450.0, "last_price": None, "option_type": "c"},  # Invalid price
            ],
            "2025-01-24": [
                # Weekly options
                {"strike": 450.0, "last_price": 3.50, "option_type": "c"},
                {"strike": 450.0, "last_price": 2.75, "option_type": "p"},
                {"strike": 455.0, "last_price": 2.25, "option_type": "c"},
                {"strike": 445.0, "last_price": 1.50, "option_type": "p"},
            ],
            "2025-02-21": [
                # Monthly options
                {"strike": 450.0, "last_price": 5.50, "option_type": "c"},
                {"strike": 450.0, "last_price": 4.75, "option_type": "p"},
                {"strike": 460.0, "last_price": 3.25, "option_type": "c"},
                {"strike": 440.0, "last_price": 2.50, "option_type": "p"},
            ]
        }
    
    def test_complete_data_processing_workflow(self):
        """Test the complete data processing workflow with realistic data."""
        # Process the data
        response = self.processor.format_api_response(
            ticker="SPY",
            stock_price=450.25,
            vix_value=18.75,
            raw_options_data=self.realistic_options_data
        )
        
        # Verify response structure
        assert response["ticker"] == "SPY"
        assert response["stockPrice"] == 450.25
        assert response["vixValue"] == 18.75
        assert "dataTimestamp" in response
        assert "vixTimestamp" in response
        
        # Verify expiration dates are sorted
        expiration_dates = response["expirationDates"]
        assert len(expiration_dates) == 3
        assert expiration_dates[0]["expiration"] == "2025-01-17"
        assert expiration_dates[1]["expiration"] == "2025-01-24"
        assert expiration_dates[2]["expiration"] == "2025-02-21"
        
        # Verify first expiration has processed options
        first_exp = expiration_dates[0]
        assert len(first_exp["calls"]) > 0
        assert len(first_exp["puts"]) > 0
        
        # Verify options have calculated values
        first_call = first_exp["calls"][0]
        assert "strike" in first_call
        assert "lastPrice" in first_call
        assert "impliedVolatility" in first_call
        assert "delta" in first_call
        
        # Verify filtering worked (invalid options should be excluded)
        # We had 12 total options in first expiration, but 2 were invalid
        total_first_exp_options = len(first_exp["calls"]) + len(first_exp["puts"])
        assert total_first_exp_options == 10  # Should be exactly 10 after filtering out 2 invalid
    
    def test_data_processing_with_minimal_valid_options(self):
        """Test processing when most options are invalid."""
        minimal_data = {
            "2025-01-17": [
                {"strike": 450.0, "last_price": 2.50, "option_type": "c"},  # Valid
                {"strike": 0.0, "last_price": 1.00, "option_type": "c"},    # Invalid strike
                {"strike": 450.0, "last_price": None, "option_type": "p"},  # Invalid price
                {"strike": -10.0, "last_price": 1.00, "option_type": "p"},  # Invalid strike
            ]
        }
        
        response = self.processor.format_api_response(
            ticker="AAPL",
            stock_price=150.00,
            vix_value=20.00,
            raw_options_data=minimal_data
        )
        
        # Should still work with minimal valid data
        assert response["ticker"] == "AAPL"
        assert len(response["expirationDates"]) == 1
        
        # Should have filtered out invalid options
        exp_data = response["expirationDates"][0]
        total_options = len(exp_data["calls"]) + len(exp_data["puts"])
        assert total_options <= 1  # Only 1 valid option maximum
    
    def test_data_processing_with_custom_timestamps(self):
        """Test processing with custom timestamps."""
        data_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        vix_timestamp = datetime(2025, 1, 16, 14, 31, 0, tzinfo=timezone.utc)
        
        response = self.processor.format_api_response(
            ticker="MSFT",
            stock_price=300.00,
            vix_value=22.50,
            raw_options_data={"2025-01-17": [{"strike": 300.0, "last_price": 5.00, "option_type": "c"}]},
            data_timestamp=data_timestamp,
            vix_timestamp=vix_timestamp
        )
        
        assert response["dataTimestamp"] == "2025-01-16T14:30:00Z"
        assert response["vixTimestamp"] == "2025-01-16T14:31:00Z"
    
    def test_expiration_filtering_by_validity(self):
        """Test filtering expiration dates with insufficient valid options."""
        # Create data where one expiration has no valid options
        mixed_data = {
            "2025-01-17": [
                {"strike": 450.0, "last_price": 2.50, "option_type": "c"},  # Valid
                {"strike": 450.0, "last_price": 1.75, "option_type": "p"},  # Valid
            ],
            "2025-01-24": [
                {"strike": 0.0, "last_price": 1.00, "option_type": "c"},    # Invalid
                {"strike": 450.0, "last_price": None, "option_type": "p"},  # Invalid
            ]
        }
        
        # First, get the structured data
        market_data = self.processor.create_market_data_response(
            ticker="SPY",
            stock_price=450.25,
            vix_value=18.75,
            raw_options_data=mixed_data
        )
        
        # Filter expiration dates
        filtered_expirations = self.processor.filter_expiration_dates_by_validity(
            market_data.expiration_dates,
            min_options_per_expiration=1
        )
        
        # Should only have the first expiration with valid options
        assert len(filtered_expirations) == 1
        assert filtered_expirations[0].expiration == "2025-01-17"
    
    def test_error_handling_in_complete_workflow(self):
        """Test error handling throughout the complete workflow."""
        # Test with invalid ticker
        with pytest.raises(ValueError, match="Invalid ticker symbol"):
            self.processor.format_api_response(
                ticker="INVALID@TICKER",
                stock_price=450.25,
                vix_value=18.75,
                raw_options_data=self.realistic_options_data
            )
        
        # Test with empty options data
        response = self.processor.format_api_response(
            ticker="SPY",
            stock_price=450.25,
            vix_value=18.75,
            raw_options_data={}
        )
        
        # Should handle empty data gracefully
        assert response["ticker"] == "SPY"
        assert len(response["expirationDates"]) == 0
    
    def test_performance_with_large_dataset(self):
        """Test processing performance with a larger dataset."""
        # Create a larger dataset
        large_dataset = {}
        
        # Generate multiple expiration dates
        for month in range(1, 13):  # 12 months
            exp_date = f"2025-{month:02d}-15"
            options = []
            
            # Generate options for strikes from 400 to 500
            for strike in range(400, 501, 5):
                options.extend([
                    {"strike": float(strike), "last_price": 2.50, "option_type": "c"},
                    {"strike": float(strike), "last_price": 1.75, "option_type": "p"},
                ])
            
            large_dataset[exp_date] = options
        
        # Process the large dataset
        response = self.processor.format_api_response(
            ticker="SPY",
            stock_price=450.25,
            vix_value=18.75,
            raw_options_data=large_dataset
        )
        
        # Verify it processed successfully
        assert response["ticker"] == "SPY"
        assert len(response["expirationDates"]) == 12
        
        # Verify each expiration has processed options
        for exp_data in response["expirationDates"]:
            assert len(exp_data["calls"]) > 0
            assert len(exp_data["puts"]) > 0
            
            # Verify first option has all required fields
            first_call = exp_data["calls"][0]
            assert all(key in first_call for key in ["strike", "lastPrice", "impliedVolatility", "delta"])