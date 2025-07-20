"""
Optimized options calculator for implied volatility and Greeks calculations.
"""
from typing import Optional, List, Dict, Any
from functools import lru_cache
import numpy as np

from ..models.option_data import OptionData
from ..utils.time_utils import calculate_time_to_expiration
from ..utils.logging_utils import StructuredLogger
from ..utils.optimized_calculation_utils import (
    calculate_mid_price, 
    cached_implied_volatility,
    calculate_implied_volatilities_batch
)


class OptimizedOptionsCalculator:
    """Optimized calculator for options implied volatility and Greeks."""
    
    def __init__(self, risk_free_rate: float = 0.03, logger: Optional[StructuredLogger] = None):
        """
        Initialize options calculator.
        
        Args:
            risk_free_rate: Risk-free interest rate (default 3%)
            logger: Optional structured logger instance
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logger or StructuredLogger(__name__)
    
    @lru_cache(maxsize=128)
    def calculate_implied_volatility(
        self,
        option_price: float,
        underlying_price: float,
        strike_price: float,
        time_to_expiration: float,
        option_type: str
    ) -> Optional[float]:
        """
        Calculate implied volatility using Black-Scholes model with caching.
        
        Args:
            option_price: Current option price
            underlying_price: Current underlying stock price
            strike_price: Option strike price
            time_to_expiration: Time to expiration in years
            option_type: 'c' for call, 'p' for put
            
        Returns:
            Implied volatility as decimal (e.g., 0.20 for 20%) or None if calculation fails
        """
        # Validate inputs
        if option_price <= 0 or underlying_price <= 0 or strike_price <= 0:
            return None
        
        if time_to_expiration <= 0:
            return None
        
        if option_type not in ['c', 'p']:
            return None
        
        # Use cached implementation
        return cached_implied_volatility(
            price=option_price,
            S=underlying_price,
            K=strike_price,
            t=time_to_expiration,
            r=self.risk_free_rate,
            flag=option_type
        )
    
    @lru_cache(maxsize=128)
    def calculate_delta(
        self,
        underlying_price: float,
        strike_price: float,
        time_to_expiration: float,
        implied_vol: float,
        option_type: str
    ) -> Optional[float]:
        """
        Calculate option delta using Black-Scholes model with caching.
        
        Args:
            underlying_price: Current underlying stock price
            strike_price: Option strike price
            time_to_expiration: Time to expiration in years
            implied_vol: Implied volatility as decimal
            option_type: 'c' for call, 'p' for put
            
        Returns:
            Delta value or None if calculation fails
        """
        try:
            # Validate inputs
            if underlying_price <= 0 or strike_price <= 0:
                return None
            
            if time_to_expiration <= 0:
                return None
            
            if implied_vol <= 0 or implied_vol > 5.0:
                return None
            
            if option_type not in ['c', 'p']:
                return None
            
            # Calculate delta using py_vollib
            from py_vollib.black_scholes.greeks.analytical import delta
            
            delta_value = delta(
                flag=option_type,
                S=underlying_price,
                K=strike_price,
                t=time_to_expiration,
                r=self.risk_free_rate,
                sigma=implied_vol
            )
            
            return delta_value
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate delta: {e}",
                              error=str(e), underlying_price=underlying_price,
                              strike_price=strike_price, implied_vol=implied_vol)
            return None
    
    def process_options_with_iv_batch(
        self,
        options: List[OptionData],
        underlying_price: float,
        expiration_date: str
    ) -> List[OptionData]:
        """
        Process list of options and calculate implied volatility and delta.
        Optimized batch processing version.
        
        Args:
            options: List of OptionData objects
            underlying_price: Current underlying stock price
            expiration_date: Expiration date string (YYYY-MM-DD)
            
        Returns:
            List of OptionData objects with calculated IV and delta
        """
        if not options:
            return []
        
        time_to_exp = calculate_time_to_expiration(expiration_date)
        processed_options = []
        
        # Group options by type for batch processing
        calls = [opt for opt in options if opt.option_type == 'c']
        puts = [opt for opt in options if opt.option_type == 'p']
        
        # Process calls
        for option in calls:
            # Calculate implied volatility based on last price
            iv = self.calculate_implied_volatility(
                option_price=option.last_price,
                underlying_price=underlying_price,
                strike_price=option.strike,
                time_to_expiration=time_to_exp,
                option_type=option.option_type
            )
            
            # Skip options where IV calculation failed
            if iv is None:
                continue
            
            # Calculate delta
            delta_value = self.calculate_delta(
                underlying_price=underlying_price,
                strike_price=option.strike,
                time_to_expiration=time_to_exp,
                implied_vol=iv,
                option_type=option.option_type
            )
            
            # Calculate mid price
            mid_price = None
            if option.bid is not None and option.ask is not None:
                mid_price = calculate_mid_price(option.bid, option.ask)
            
            # Calculate IVs based on bid, mid, and ask prices
            iv_bid = None
            iv_mid = None
            iv_ask = None
            
            if option.bid is not None and option.bid > 0:
                iv_bid = self.calculate_implied_volatility(
                    option_price=option.bid,
                    underlying_price=underlying_price,
                    strike_price=option.strike,
                    time_to_expiration=time_to_exp,
                    option_type=option.option_type
                )
            
            if mid_price is not None and mid_price > 0:
                iv_mid = self.calculate_implied_volatility(
                    option_price=mid_price,
                    underlying_price=underlying_price,
                    strike_price=option.strike,
                    time_to_expiration=time_to_exp,
                    option_type=option.option_type
                )
            
            if option.ask is not None and option.ask > 0:
                iv_ask = self.calculate_implied_volatility(
                    option_price=option.ask,
                    underlying_price=underlying_price,
                    strike_price=option.strike,
                    time_to_expiration=time_to_exp,
                    option_type=option.option_type
                )
            
            # Create new OptionData with calculated values
            processed_option = OptionData(
                strike=option.strike,
                last_price=option.last_price,
                implied_volatility=iv,  # This will be used as impliedVolatilityYF
                delta=delta_value,
                option_type=option.option_type,
                contract_symbol=option.contract_symbol,
                last_trade_date=option.last_trade_date,
                bid=option.bid,
                ask=option.ask,
                mid_price=mid_price,
                volume=option.volume,
                open_interest=option.open_interest,
                moneyness=option.moneyness,
                implied_volatility_bid=iv_bid,
                implied_volatility_mid=iv_mid,
                implied_volatility_ask=iv_ask
            )
            
            processed_options.append(processed_option)
        
        # Process puts (same logic as calls)
        for option in puts:
            # Calculate implied volatility based on last price
            iv = self.calculate_implied_volatility(
                option_price=option.last_price,
                underlying_price=underlying_price,
                strike_price=option.strike,
                time_to_expiration=time_to_exp,
                option_type=option.option_type
            )
            
            # Skip options where IV calculation failed
            if iv is None:
                continue
            
            # Calculate delta
            delta_value = self.calculate_delta(
                underlying_price=underlying_price,
                strike_price=option.strike,
                time_to_expiration=time_to_exp,
                implied_vol=iv,
                option_type=option.option_type
            )
            
            # Calculate mid price
            mid_price = None
            if option.bid is not None and option.ask is not None:
                mid_price = calculate_mid_price(option.bid, option.ask)
            
            # Calculate IVs based on bid, mid, and ask prices
            iv_bid = None
            iv_mid = None
            iv_ask = None
            
            if option.bid is not None and option.bid > 0:
                iv_bid = self.calculate_implied_volatility(
                    option_price=option.bid,
                    underlying_price=underlying_price,
                    strike_price=option.strike,
                    time_to_expiration=time_to_exp,
                    option_type=option.option_type
                )
            
            if mid_price is not None and mid_price > 0:
                iv_mid = self.calculate_implied_volatility(
                    option_price=mid_price,
                    underlying_price=underlying_price,
                    strike_price=option.strike,
                    time_to_expiration=time_to_exp,
                    option_type=option.option_type
                )
            
            if option.ask is not None and option.ask > 0:
                iv_ask = self.calculate_implied_volatility(
                    option_price=option.ask,
                    underlying_price=underlying_price,
                    strike_price=option.strike,
                    time_to_expiration=time_to_exp,
                    option_type=option.option_type
                )
            
            # Create new OptionData with calculated values
            processed_option = OptionData(
                strike=option.strike,
                last_price=option.last_price,
                implied_volatility=iv,  # This will be used as impliedVolatilityYF
                delta=delta_value,
                option_type=option.option_type,
                contract_symbol=option.contract_symbol,
                last_trade_date=option.last_trade_date,
                bid=option.bid,
                ask=option.ask,
                mid_price=mid_price,
                volume=option.volume,
                open_interest=option.open_interest,
                moneyness=option.moneyness,
                implied_volatility_bid=iv_bid,
                implied_volatility_mid=iv_mid,
                implied_volatility_ask=iv_ask
            )
            
            processed_options.append(processed_option)
        
        return processed_options