"""
Options data fetcher service for options analytics API.
Handles fetching option chains from Yahoo Finance and parsing into structured format.
"""
import yfinance as yf
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from src.models.option_data import OptionData, ExpirationData
from src.utils.time_utils import get_current_utc_timestamp


class OptionsDataFetcher:
    """Service for fetching options data from Yahoo Finance."""
    
    def __init__(self):
        """Initialize the options data fetcher."""
        pass
    
    def validate_ticker(self, ticker: str) -> str:
        """
        Validate and format ticker symbol.
        
        Args:
            ticker: Raw ticker symbol
            
        Returns:
            Formatted ticker symbol
            
        Raises:
            ValueError: If ticker is invalid
        """
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
        
        # Clean and format ticker
        formatted_ticker = ticker.strip().upper()
        
        if not formatted_ticker:
            raise ValueError("Ticker cannot be empty after formatting")
        
        # Basic validation - ticker should be alphanumeric with possible dots/hyphens
        if not all(c.isalnum() or c in '.-' for c in formatted_ticker):
            raise ValueError(f"Invalid ticker format: {formatted_ticker}")
        
        return formatted_ticker
    
    def fetch_option_expiration_dates(self, ticker: str) -> List[str]:
        """
        Fetch all available option expiration dates for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of expiration date strings in YYYY-MM-DD format
            
        Raises:
            RuntimeError: If expiration dates cannot be fetched
        """
        try:
            validated_ticker = self.validate_ticker(ticker)
            stock = yf.Ticker(validated_ticker)
            
            # Get option expiration dates
            expiration_dates = stock.options
            
            if not expiration_dates:
                raise ValueError(f"No option expiration dates found for ticker {validated_ticker}")
            
            return list(expiration_dates)
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise RuntimeError(f"Failed to fetch expiration dates for {ticker}: {str(e)}")
            raise RuntimeError(f"Failed to fetch expiration dates for {ticker}: {str(e)}")
    
    def parse_option_chain(self, option_chain: pd.DataFrame, option_type: str) -> List[OptionData]:
        """
        Parse option chain DataFrame into OptionData objects.
        
        Args:
            option_chain: DataFrame containing option data
            option_type: 'c' for calls, 'p' for puts
            
        Returns:
            List of OptionData objects
        """
        options = []
        
        if option_chain.empty:
            return options
        
        for _, row in option_chain.iterrows():
            try:
                # Extract required fields with fallbacks
                strike = float(row.get('strike', 0))
                last_price = float(row.get('lastPrice', 0))
                
                # Skip options with invalid data
                if strike <= 0 or last_price <= 0:
                    continue
                
                option_data = OptionData(
                    strike=strike,
                    last_price=last_price,
                    implied_volatility=None,  # Will be calculated later
                    delta=None,  # Will be calculated later
                    option_type=option_type
                )
                
                options.append(option_data)
                
            except (ValueError, TypeError, KeyError) as e:
                # Skip invalid option data
                continue
        
        return options
    
    def fetch_option_chain_for_expiration(self, ticker: str, expiration_date: str) -> ExpirationData:
        """
        Fetch option chain data for a specific expiration date.
        
        Args:
            ticker: Stock ticker symbol
            expiration_date: Expiration date in YYYY-MM-DD format
            
        Returns:
            ExpirationData object containing calls and puts
            
        Raises:
            RuntimeError: If option chain cannot be fetched
        """
        try:
            validated_ticker = self.validate_ticker(ticker)
            stock = yf.Ticker(validated_ticker)
            
            # Get option chain for specific expiration
            option_chain = stock.option_chain(expiration_date)
            
            # Parse calls and puts
            calls = self.parse_option_chain(option_chain.calls, 'c')
            puts = self.parse_option_chain(option_chain.puts, 'p')
            
            return ExpirationData(
                expiration=expiration_date,
                calls=calls,
                puts=puts
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch option chain for {ticker} expiration {expiration_date}: {str(e)}")
    
    def fetch_all_option_chains(self, ticker: str) -> List[ExpirationData]:
        """
        Fetch option chains for all available expiration dates.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of ExpirationData objects for all expiration dates
            
        Raises:
            RuntimeError: If option chains cannot be fetched
        """
        try:
            # Get all expiration dates
            expiration_dates = self.fetch_option_expiration_dates(ticker)
            
            option_chains = []
            
            for expiration_date in expiration_dates:
                try:
                    expiration_data = self.fetch_option_chain_for_expiration(ticker, expiration_date)
                    
                    # Only include expiration dates that have options
                    if expiration_data.calls or expiration_data.puts:
                        option_chains.append(expiration_data)
                        
                except RuntimeError:
                    # Skip expiration dates that fail to fetch
                    continue
            
            if not option_chains:
                raise ValueError(f"No valid option chains found for ticker {ticker}")
            
            return option_chains
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise RuntimeError(str(e))
            raise RuntimeError(f"Failed to fetch option chains for {ticker}: {str(e)}")


# Convenience functions for direct usage
def get_option_expiration_dates(ticker: str) -> List[str]:
    """
    Convenience function to fetch option expiration dates.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of expiration date strings
    """
    fetcher = OptionsDataFetcher()
    return fetcher.fetch_option_expiration_dates(ticker)


def get_option_chain_for_expiration(ticker: str, expiration_date: str) -> ExpirationData:
    """
    Convenience function to fetch option chain for specific expiration.
    
    Args:
        ticker: Stock ticker symbol
        expiration_date: Expiration date string
        
    Returns:
        ExpirationData object
    """
    fetcher = OptionsDataFetcher()
    return fetcher.fetch_option_chain_for_expiration(ticker, expiration_date)


def get_all_option_chains(ticker: str) -> List[ExpirationData]:
    """
    Convenience function to fetch all option chains.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        List of ExpirationData objects
    """
    fetcher = OptionsDataFetcher()
    return fetcher.fetch_all_option_chains(ticker)