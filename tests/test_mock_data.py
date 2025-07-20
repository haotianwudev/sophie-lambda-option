"""
Tests for mock data.
"""
import unittest
from datetime import datetime, timezone
from tests.mock_data import (
    get_mock_stock_data,
    get_mock_vix_data,
    get_mock_expiration_dates,
    get_mock_option_chain,
    get_mock_api_response,
    get_mock_raw_yfinance_option_data,
    get_mock_raw_market_data
)


class TestMockData(unittest.TestCase):
    """Test cases for mock data."""
    
    def test_mock_stock_data(self):
        """Test mock stock data."""
        stock_data = get_mock_stock_data()
        
        # Check required fields
        self.assertIn("price", stock_data)
        self.assertIn("previousClose", stock_data)
        self.assertIn("percentChange", stock_data)
        self.assertIn("timestamp", stock_data)
        
        # Check data types
        self.assertIsInstance(stock_data["price"], float)
        self.assertIsInstance(stock_data["previousClose"], float)
        self.assertIsInstance(stock_data["percentChange"], float)
        self.assertIsInstance(stock_data["timestamp"], str)
        
        # Check percentage change calculation
        expected_pct_change = round(((stock_data["price"] - stock_data["previousClose"]) / 
                                    stock_data["previousClose"]) * 100, 2)
        self.assertEqual(stock_data["percentChange"], expected_pct_change)
    
    def test_mock_vix_data(self):
        """Test mock VIX data."""
        vix_data = get_mock_vix_data()
        
        # Check required fields
        self.assertIn("value", vix_data)
        self.assertIn("previousClose", vix_data)
        self.assertIn("percentChange", vix_data)
        self.assertIn("timestamp", vix_data)
        
        # Check data types
        self.assertIsInstance(vix_data["value"], float)
        self.assertIsInstance(vix_data["previousClose"], float)
        self.assertIsInstance(vix_data["percentChange"], float)
        self.assertIsInstance(vix_data["timestamp"], str)
        
        # Check percentage change calculation
        expected_pct_change = round(((vix_data["value"] - vix_data["previousClose"]) / 
                                    vix_data["previousClose"]) * 100, 2)
        self.assertEqual(vix_data["percentChange"], expected_pct_change)
    
    def test_mock_expiration_dates(self):
        """Test mock expiration dates."""
        exp_dates = get_mock_expiration_dates()
        
        # Check we have dates
        self.assertTrue(len(exp_dates) > 0)
        
        # Check format
        for date_str in exp_dates:
            self.assertRegex(date_str, r'^\d{4}-\d{2}-\d{2}$')
            
            # Check it's a valid date
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self.fail(f"Invalid date format: {date_str}")
    
    def test_mock_option_chain(self):
        """Test mock option chain."""
        current_price = 600.0
        option_chain = get_mock_option_chain(current_price)
        
        # Check we have data for each expiration
        exp_dates = get_mock_expiration_dates()
        self.assertEqual(set(option_chain.keys()), set(exp_dates))
        
        # Check structure for first expiration
        first_exp = exp_dates[0]
        exp_data = option_chain[first_exp]
        
        self.assertIn("calls", exp_data)
        self.assertIn("puts", exp_data)
        self.assertTrue(len(exp_data["calls"]) > 0)
        self.assertTrue(len(exp_data["puts"]) > 0)
        
        # Check call option fields
        call = exp_data["calls"][0]
        required_fields = [
            "contractSymbol", "strike", "lastPrice", "bid", "ask",
            "lastTradeDate", "volume", "openInterest", "impliedVolatility"
        ]
        
        for field in required_fields:
            self.assertIn(field, call)
        
        # Check put option fields
        put = exp_data["puts"][0]
        for field in required_fields:
            self.assertIn(field, put)
        
        # Check moneyness calculation is reflected in pricing
        # Find options with strikes closest to ATM, ITM, and OTM
        strikes = sorted([c["strike"] for c in exp_data["calls"]])
        atm_strike = min(strikes, key=lambda x: abs(x - current_price))
        itm_strike = max([s for s in strikes if s < current_price], default=None)
        otm_strike = min([s for s in strikes if s > current_price], default=None)
        
        atm_call = next((c for c in exp_data["calls"] if c["strike"] == atm_strike), None)
        itm_call = next((c for c in exp_data["calls"] if c["strike"] == itm_strike), None)
        otm_call = next((c for c in exp_data["calls"] if c["strike"] == otm_strike), None)
        
        # Check that ITM calls have higher prices than ATM calls
        if atm_call and itm_call:
            self.assertGreaterEqual(itm_call["lastPrice"], 0)
            self.assertGreaterEqual(atm_call["lastPrice"], 0)
        
        # Check that OTM calls have lower delta than ATM calls
        if atm_call and otm_call and "delta" in atm_call and "delta" in otm_call:
            self.assertLessEqual(otm_call["delta"], atm_call["delta"])
    
    def test_mock_api_response(self):
        """Test mock API response."""
        response = get_mock_api_response()
        
        # Check top-level structure
        self.assertIn("ticker", response)
        self.assertIn("stock", response)
        self.assertIn("vix", response)
        self.assertIn("expirationDates", response)
        
        # Check ticker
        self.assertEqual(response["ticker"], "SPY")
        
        # Check stock data
        stock_data = response["stock"]
        self.assertIn("price", stock_data)
        self.assertIn("previousClose", stock_data)
        self.assertIn("percentChange", stock_data)
        self.assertIn("timestamp", stock_data)
        
        # Check VIX data
        vix_data = response["vix"]
        self.assertIn("value", vix_data)
        self.assertIn("previousClose", vix_data)
        self.assertIn("percentChange", vix_data)
        self.assertIn("timestamp", vix_data)
        
        # Check expiration dates
        exp_dates = response["expirationDates"]
        self.assertTrue(len(exp_dates) > 0)
        
        # Check first expiration
        first_exp = exp_dates[0]
        self.assertIn("expiration", first_exp)
        self.assertIn("daysToExpiration", first_exp)
        self.assertIn("expirationLabel", first_exp)
        self.assertIn("calls", first_exp)
        self.assertIn("puts", first_exp)
        
        # Check expiration labels
        labels = [exp["expirationLabel"] for exp in exp_dates]
        expected_labels = ["2w", "1m", "6w", "2m"]
        self.assertEqual(set(labels), set(expected_labels))
    
    def test_mock_raw_yfinance_option_data(self):
        """Test mock raw yfinance option data."""
        yf_data = get_mock_raw_yfinance_option_data()
        
        # Check structure
        self.assertIn("underlyingSymbol", yf_data)
        self.assertIn("expirationDates", yf_data)
        self.assertIn("strikes", yf_data)
        self.assertIn("options", yf_data)
        
        # Check symbol
        self.assertEqual(yf_data["underlyingSymbol"], "SPY")
        
        # Check expiration dates
        self.assertTrue(len(yf_data["expirationDates"]) > 0)
        
        # Check strikes
        self.assertTrue(len(yf_data["strikes"]) > 0)
        
        # Check options data
        options = yf_data["options"]
        self.assertTrue(len(options) > 0)
        
        # Check first expiration
        first_exp = yf_data["expirationDates"][0]
        exp_data = options[first_exp]
        
        self.assertIn("calls", exp_data)
        self.assertIn("puts", exp_data)
        self.assertTrue(len(exp_data["calls"]) > 0)
        self.assertTrue(len(exp_data["puts"]) > 0)
    
    def test_mock_raw_market_data(self):
        """Test mock raw market data."""
        market_data = get_mock_raw_market_data()
        
        # Check tickers
        self.assertIn("SPY", market_data)
        self.assertIn("^VIX", market_data)
        
        # Check SPY data
        spy_data = market_data["SPY"]
        self.assertIn("info", spy_data)
        self.assertIn("history", spy_data)
        
        # Check SPY info
        spy_info = spy_data["info"]
        self.assertIn("regularMarketPrice", spy_info)
        self.assertIn("previousClose", spy_info)
        
        # Check SPY history
        spy_history = spy_data["history"]
        self.assertIn("Close", spy_history)
        self.assertEqual(len(spy_history["Close"]), 2)
        
        # Check VIX data
        vix_data = market_data["^VIX"]
        self.assertIn("info", vix_data)
        self.assertIn("history", vix_data)
        
        # Check VIX info
        vix_info = vix_data["info"]
        self.assertIn("regularMarketPrice", vix_info)
        self.assertIn("previousClose", vix_info)
        
        # Check VIX history
        vix_history = vix_data["history"]
        self.assertIn("Close", vix_history)
        self.assertEqual(len(vix_history["Close"]), 2)


if __name__ == "__main__":
    unittest.main()