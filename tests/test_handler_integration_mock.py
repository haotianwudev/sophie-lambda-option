"""
Integration tests for the enhanced options data API handler using mocks.
Tests the end-to-end flow with mock data and verifies the structure and content of the API response.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from handler import get_options_analytics
from src.models.option_data import OptionData, ExpirationData, MarketData, StockData, VixData
from tests.mock_data import (
    get_mock_stock_data,
    get_mock_vix_data,
    get_mock_option_chain,
    get_mock_api_response
)


class TestHandlerIntegrationWithMocks:
    """Integration tests for the enhanced Lambda handler with complete mocking."""
    
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
    @patch('src.utils.data_formatter.format_market_data_for_response')
    def test_successful_request_with_enhanced_data(self, mock_format, mock_data_processor, mock_options_fetcher, mock_market_fetcher):
        """Test successful request processing with enhanced market data and option fields."""
        # Mock market data fetcher with enhanced data
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher with filtered option chains
        mock_options_instance = mock_options_fetcher.return_value
        
        # Create mock expiration data with enhanced option fields
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
                    option_type='c',
                    contract_symbol=call_data['contractSymbol'],
                    last_trade_date=call_data['lastTradeDate'],
                    bid=call_data['bid'],
                    ask=call_data['ask'],
                    volume=call_data['volume'],
                    open_interest=call_data['openInterest']
                )
                calls.append(call)
            
            puts = []
            for put_data in data['puts']:
                put = OptionData(
                    strike=put_data['strike'],
                    last_price=put_data['lastPrice'],
                    implied_volatility=put_data['impliedVolatility'],
                    delta=put_data['delta'],
                    option_type='p',
                    contract_symbol=put_data['contractSymbol'],
                    last_trade_date=put_data['lastTradeDate'],
                    bid=put_data['bid'],
                    ask=put_data['ask'],
                    volume=put_data['volume'],
                    open_interest=put_data['openInterest']
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
        
        # Mock DataProcessor
        mock_processor_instance = mock_data_processor.return_value
        
        # Create a mock MarketData object
        stock_data = StockData(
            price=get_mock_stock_data()['price'],
            previous_close=get_mock_stock_data()['previousClose'],
            percent_change=get_mock_stock_data()['percentChange'],
            timestamp=datetime.fromisoformat(get_mock_stock_data()['timestamp'].replace('Z', '+00:00'))
        )
        
        vix_data = VixData(
            value=get_mock_vix_data()['value'],
            previous_close=get_mock_vix_data()['previousClose'],
            percent_change=get_mock_vix_data()['percentChange'],
            timestamp=datetime.fromisoformat(get_mock_vix_data()['timestamp'].replace('Z', '+00:00'))
        )
        
        market_data = MarketData(
            ticker='SPY',
            stock=stock_data,
            vix=vix_data,
            expiration_dates=expiration_data_list
        )
        
        # Mock create_market_data_response to return the mock MarketData
        mock_processor_instance.create_market_data_response.return_value = market_data
        
        # Mock format_market_data_for_response to return the expected API response
        mock_format.return_value = get_mock_api_response()
        
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
        
        # Verify enhanced stock data
        assert 'stock' in body
        assert 'price' in body['stock']
        assert 'previousClose' in body['stock']
        assert 'percentChange' in body['stock']
        assert 'timestamp' in body['stock']
        
        # Verify enhanced VIX data
        assert 'vix' in body
        assert 'value' in body['vix']
        assert 'previousClose' in body['vix']
        assert 'percentChange' in body['vix']
        assert 'timestamp' in body['vix']
        
        # Verify expiration dates
        assert 'expirationDates' in body
        assert len(body['expirationDates']) > 0
    
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
        
        # Mock options data fetcher to return empty list (to simplify test)
        mock_options_instance = mock_options_fetcher.return_value
        mock_options_instance.fetch_filtered_option_chains.return_value = []
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response - should fail with appropriate error
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        
        # Check error type and message
        assert body['errorType'] == 'DATA_FETCH_ERROR'
        assert 'No option expiration dates found' in body['error']
    
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
        
        # Verify response - should still fail with appropriate error
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        
        # Check error type and message
        assert body['errorType'] == 'CALCULATION_ERROR'
        assert 'Failed to process enhanced options data' in body['error']