"""
Integration tests for error scenarios in the enhanced options data API handler.
Tests the handling of missing previous close data, invalid option data, and missing expiration dates.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from handler import get_options_analytics
from src.models.option_data import OptionData, ExpirationData
from tests.mock_data import (
    get_mock_stock_data,
    get_mock_vix_data,
    get_mock_option_chain
)


class TestHandlerErrorScenarios:
    """Integration tests for error handling in the enhanced Lambda handler."""
    
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
    def test_missing_previous_close_data(self, mock_options_fetcher, mock_market_fetcher):
        """Test handling of missing previous close data."""
        # Mock market data fetcher to fail on enhanced data but succeed on basic data
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.side_effect = RuntimeError("Failed to fetch previous close data")
        
        # Mock successful basic market data fetch
        stock_data = get_mock_stock_data()
        vix_data = get_mock_vix_data()
        mock_market_instance.fetch_market_data.return_value = (
            stock_data['price'],
            vix_data['value'],
            datetime.fromisoformat(stock_data['timestamp'].replace('Z', '+00:00')),
            datetime.fromisoformat(vix_data['timestamp'].replace('Z', '+00:00'))
        )
        
        # Mock options data fetcher
        mock_options_instance = mock_options_fetcher.return_value
        
        # Create mock expiration data
        stock_price = stock_data['price']
        option_chain = get_mock_option_chain(stock_price)
        
        # Convert the option chain to ExpirationData objects
        expiration_data_list = []
        for exp_date, data in option_chain.items():
            calls = []
            for call_data in data['calls']:
                call = OptionData(
                    strike=call_data['strike'],
                    last_price=call_data['lastPrice'],
                    implied_volatility=call_data['impliedVolatility'],
                    delta=call_data['delta'],
                    option_type='c'
                )
                calls.append(call)
            
            puts = []
            for put_data in data['puts']:
                put = OptionData(
                    strike=put_data['strike'],
                    last_price=put_data['lastPrice'],
                    implied_volatility=put_data['impliedVolatility'],
                    delta=put_data['delta'],
                    option_type='p'
                )
                puts.append(put)
            
            expiration_data = ExpirationData(
                expiration=exp_date,
                calls=calls,
                puts=puts
            )
            expiration_data_list.append(expiration_data)
        
        # Set up the mock to return filtered expirations
        mock_options_instance.fetch_filtered_option_chains.return_value = expiration_data_list
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response - should still succeed with fallback data
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Check that we have stock and VIX data
        assert 'stock' in body
        assert 'vix' in body
        
        # Check that we have price data but may have fallback values for previous close
        assert 'price' in body['stock']
        assert 'previousClose' in body['stock']
        assert 'percentChange' in body['stock']
        
        assert 'value' in body['vix']
        assert 'previousClose' in body['vix']
        assert 'percentChange' in body['vix']
        
        # In fallback mode, percent change might be 0 or price might equal previous close
        assert body['stock']['percentChange'] == 0.0 or body['stock']['price'] == body['stock']['previousClose']
        assert body['vix']['percentChange'] == 0.0 or body['vix']['value'] == body['vix']['previousClose']
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_invalid_option_data(self, mock_options_fetcher, mock_market_fetcher):
        """Test handling of invalid option data."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher
        mock_options_instance = mock_options_fetcher.return_value
        
        # Create mock expiration data with some invalid options
        stock_price = get_mock_stock_data()['price']
        option_chain = get_mock_option_chain(stock_price)
        
        # Convert the option chain to ExpirationData objects with some invalid data
        expiration_data_list = []
        for exp_date, data in option_chain.items():
            calls = []
            for i, call_data in enumerate(data['calls']):
                # Make some options invalid (negative strike, zero last price)
                if i % 3 == 0:
                    call = OptionData(
                        strike=-1,  # Invalid strike
                        last_price=0,  # Invalid price
                        implied_volatility=None,
                        delta=None,
                        option_type='c'
                    )
                else:
                    call = OptionData(
                        strike=call_data['strike'],
                        last_price=call_data['lastPrice'],
                        implied_volatility=call_data['impliedVolatility'],
                        delta=call_data['delta'],
                        option_type='c'
                    )
                calls.append(call)
            
            puts = []
            for i, put_data in enumerate(data['puts']):
                # Make some options invalid
                if i % 3 == 0:
                    put = OptionData(
                        strike=-1,  # Invalid strike
                        last_price=0,  # Invalid price
                        implied_volatility=None,
                        delta=None,
                        option_type='p'
                    )
                else:
                    put = OptionData(
                        strike=put_data['strike'],
                        last_price=put_data['lastPrice'],
                        implied_volatility=put_data['impliedVolatility'],
                        delta=put_data['delta'],
                        option_type='p'
                    )
                puts.append(put)
            
            expiration_data = ExpirationData(
                expiration=exp_date,
                calls=calls,
                puts=puts
            )
            expiration_data_list.append(expiration_data)
        
        # Set up the mock to return filtered expirations
        mock_options_instance.fetch_filtered_option_chains.return_value = expiration_data_list
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response - should still succeed with valid options
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Check that we have expiration dates
        assert 'expirationDates' in body
        assert len(body['expirationDates']) > 0
        
        # Check that invalid options were filtered out
        for exp in body['expirationDates']:
            for call in exp['calls']:
                # Verify all strikes are positive
                assert call['strike'] > 0
                
                # Verify all prices are positive
                assert call['lastPrice'] > 0
            
            for put in exp['puts']:
                # Verify all strikes are positive
                assert put['strike'] > 0
                
                # Verify all prices are positive
                assert put['lastPrice'] > 0
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_missing_expiration_dates(self, mock_options_fetcher, mock_market_fetcher):
        """Test handling of missing expiration dates."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher to return empty list
        mock_options_instance = mock_options_fetcher.return_value
        mock_options_instance.fetch_filtered_option_chains.return_value = []
        
        # Also mock the fallback to return empty list
        mock_options_instance.fetch_all_option_chains.return_value = []
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response - should fail with appropriate error
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        
        # Check error type and message
        assert body['errorType'] == 'DATA_FETCH_ERROR'
        assert 'No option expiration dates found' in body['error']
        assert 'ticker' in body['details']
        assert body['details']['ticker'] == 'SPY'
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_fallback_to_unfiltered_expirations(self, mock_options_fetcher, mock_market_fetcher):
        """Test fallback to unfiltered expirations when filtered expirations fail."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher to fail on filtered chains but succeed on all chains
        mock_options_instance = mock_options_fetcher.return_value
        mock_options_instance.fetch_filtered_option_chains.side_effect = RuntimeError("Failed to filter expirations")
        
        # Create mock expiration data for all chains
        stock_price = get_mock_stock_data()['price']
        option_chain = get_mock_option_chain(stock_price)
        
        # Convert the option chain to ExpirationData objects
        expiration_data_list = []
        for exp_date, data in option_chain.items():
            calls = []
            for call_data in data['calls']:
                call = OptionData(
                    strike=call_data['strike'],
                    last_price=call_data['lastPrice'],
                    implied_volatility=call_data['impliedVolatility'],
                    delta=call_data['delta'],
                    option_type='c'
                )
                calls.append(call)
            
            puts = []
            for put_data in data['puts']:
                put = OptionData(
                    strike=put_data['strike'],
                    last_price=put_data['lastPrice'],
                    implied_volatility=put_data['impliedVolatility'],
                    delta=put_data['delta'],
                    option_type='p'
                )
                puts.append(put)
            
            expiration_data = ExpirationData(
                expiration=exp_date,
                calls=calls,
                puts=puts
            )
            expiration_data_list.append(expiration_data)
        
        # Set up the mock to return all expirations as fallback
        mock_options_instance.fetch_all_option_chains.return_value = expiration_data_list
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response - should still succeed with fallback expirations
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Check that we have expiration dates
        assert 'expirationDates' in body
        assert len(body['expirationDates']) > 0
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_fallback_data_processing(self, mock_options_fetcher, mock_market_fetcher):
        """Test fallback data processing when enhanced processing fails."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher
        mock_options_instance = mock_options_fetcher.return_value
        
        # Create mock expiration data
        stock_price = get_mock_stock_data()['price']
        option_chain = get_mock_option_chain(stock_price)
        
        # Convert the option chain to ExpirationData objects
        expiration_data_list = []
        for exp_date, data in option_chain.items():
            calls = []
            for call_data in data['calls']:
                call = OptionData(
                    strike=call_data['strike'],
                    last_price=call_data['lastPrice'],
                    implied_volatility=call_data['impliedVolatility'],
                    delta=call_data['delta'],
                    option_type='c'
                )
                calls.append(call)
            
            puts = []
            for put_data in data['puts']:
                put = OptionData(
                    strike=put_data['strike'],
                    last_price=put_data['lastPrice'],
                    implied_volatility=put_data['impliedVolatility'],
                    delta=put_data['delta'],
                    option_type='p'
                )
                puts.append(put)
            
            expiration_data = ExpirationData(
                expiration=exp_date,
                calls=calls,
                puts=puts
            )
            expiration_data_list.append(expiration_data)
        
        # Set up the mock to return filtered expirations
        mock_options_instance.fetch_filtered_option_chains.return_value = expiration_data_list
        
        # Mock DataProcessor to fail on format_api_response but succeed on create_market_data_response
        with patch('handler.DataProcessor') as mock_data_processor:
            mock_processor_instance = mock_data_processor.return_value
            mock_processor_instance.format_api_response.side_effect = ValueError("Failed to format API response")
            
            # Execute handler
            response = get_options_analytics(self.sample_event, self.sample_context)
            
            # Verify response - should still succeed with fallback processing
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            
            # Check that we have basic data structure
            assert 'ticker' in body
            assert 'stock' in body
            assert 'vix' in body
            assert 'expirationDates' in body
</content>