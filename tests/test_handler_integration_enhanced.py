"""
Integration tests for the enhanced options data API handler.
Tests the end-to-end flow with mock data and verifies the structure and content of the API response.
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
    get_mock_option_chain,
    get_mock_api_response
)


class TestEnhancedHandlerIntegration:
    """Integration tests for the enhanced Lambda handler with mock data."""
    
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
    def test_successful_request_with_enhanced_data(self, mock_options_fetcher, mock_market_fetcher):
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
        
        # Verify option data structure for first expiration
        first_exp = body['expirationDates'][0]
        assert 'expiration' in first_exp
        assert 'calls' in first_exp
        assert 'puts' in first_exp
        
        # Verify enhanced option fields
        if first_exp['calls']:
            first_call = first_exp['calls'][0]
            assert 'contractSymbol' in first_call
            assert 'lastTradeDate' in first_call
            assert 'strike' in first_call
            assert 'lastPrice' in first_call
            assert 'bid' in first_call
            assert 'ask' in first_call
            assert 'volume' in first_call
            assert 'openInterest' in first_call
            assert 'moneyness' in first_call
            assert 'impliedVolatilityBid' in first_call or 'impliedVolatilityMid' in first_call or 'impliedVolatilityAsk' in first_call
        
        if first_exp['puts']:
            first_put = first_exp['puts'][0]
            assert 'contractSymbol' in first_put
            assert 'lastTradeDate' in first_put
            assert 'strike' in first_put
            assert 'lastPrice' in first_put
            assert 'bid' in first_put
            assert 'ask' in first_put
            assert 'volume' in first_put
            assert 'openInterest' in first_put
            assert 'moneyness' in first_put
            assert 'impliedVolatilityBid' in first_put or 'impliedVolatilityMid' in first_put or 'impliedVolatilityAsk' in first_put
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_expiration_date_filtering(self, mock_options_fetcher, mock_market_fetcher):
        """Test that expiration dates are properly filtered to target periods."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher with all expiration dates
        mock_options_instance = mock_options_fetcher.return_value
        
        # Create mock expiration data with all dates
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
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Check that we have expiration dates
        assert 'expirationDates' in body
        assert len(body['expirationDates']) > 0
        
        # Check for expiration labels (2w, 1m, 6w, 2m)
        expiration_labels = set()
        for exp in body['expirationDates']:
            if 'expirationLabel' in exp:
                expiration_labels.add(exp['expirationLabel'])
        
        # We should have at least some of the target labels
        assert len(expiration_labels.intersection({'2w', '1m', '6w', '2m'})) > 0
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_moneyness_calculation_and_filtering(self, mock_options_fetcher, mock_market_fetcher):
        """Test that moneyness is calculated and options are filtered by moneyness range."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher
        mock_options_instance = mock_options_fetcher.return_value
        
        # Create mock expiration data with wide range of strikes
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
        
        # Execute handler
        response = get_options_analytics(self.sample_event, self.sample_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Check that we have expiration dates
        assert 'expirationDates' in body
        assert len(body['expirationDates']) > 0
        
        # Check moneyness calculation and filtering
        for exp in body['expirationDates']:
            for call in exp['calls']:
                # Verify moneyness is calculated
                assert 'moneyness' in call
                
                # Verify moneyness is within range (0.85 to 1.15)
                assert 0.85 <= call['moneyness'] <= 1.15
            
            for put in exp['puts']:
                # Verify moneyness is calculated
                assert 'moneyness' in put
                
                # Verify moneyness is within range (0.85 to 1.15)
                assert 0.85 <= put['moneyness'] <= 1.15
    
    @patch('handler.MarketDataFetcher')
    @patch('handler.OptionsDataFetcher')
    def test_enhanced_iv_calculations(self, mock_options_fetcher, mock_market_fetcher):
        """Test that enhanced IV calculations are performed based on bid, mid, and ask prices."""
        # Mock market data fetcher
        mock_market_instance = mock_market_fetcher.return_value
        mock_market_instance.fetch_enhanced_market_data.return_value = {
            'stock': get_mock_stock_data(),
            'vix': get_mock_vix_data()
        }
        
        # Mock options data fetcher
        mock_options_instance = mock_options_fetcher.return_value
        
        # Create mock expiration data with bid/ask prices
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
                    bid=call_data['bid'],
                    ask=call_data['ask']
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
                    bid=put_data['bid'],
                    ask=put_data['ask']
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
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Check that we have expiration dates
        assert 'expirationDates' in body
        assert len(body['expirationDates']) > 0
        
        # Check enhanced IV calculations
        for exp in body['expirationDates']:
            for call in exp['calls']:
                # Verify enhanced IV fields
                assert 'impliedVolatilityYF' in call or 'impliedVolatility' in call
                
                # At least one of these should be present
                iv_fields = ['impliedVolatilityBid', 'impliedVolatilityMid', 'impliedVolatilityAsk']
                assert any(field in call for field in iv_fields)
            
            for put in exp['puts']:
                # Verify enhanced IV fields
                assert 'impliedVolatilityYF' in put or 'impliedVolatility' in put
                
                # At least one of these should be present
                iv_fields = ['impliedVolatilityBid', 'impliedVolatilityMid', 'impliedVolatilityAsk']
                assert any(field in put for field in iv_fields)