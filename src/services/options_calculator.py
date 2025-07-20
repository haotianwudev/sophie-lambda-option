"""
Options calculator for implied volatility and Greeks calculations.
"""
from typing import Optional, List
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta

from ..models.option_data import OptionData
from ..utils.time_utils import calculate_time_to_expiration
from ..utils.logging_utils import StructuredLogger


class OptionsCalculator:
    """Calculator for options implied volatility and Greeks."""
    
    def __init__(self, risk_free_rate: float = 0.03, logger: Optional[StructuredLogger] = None):
        """
        Initialize options calculator.
        
        Args:
            risk_free_rate: Risk-free interest rate (default 3%)
            logger: Optional structured logger instance
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logger or StructuredLogger(__name__)
    
    def calculate_implied_volatility(
        self,
        option_price: float,
        underlying_price: float,
        strike_price: float,
        time_to_expiration: float,
        option_type: str
    ) -> Optional[float]:
        """
        Calculate implied volatility using Black-Scholes model.
        
        Args:
            option_price: Current option price
            underlying_price: Current underlying stock price
            strike_price: Option strike price
            time_to_expiration: Time to expiration in years
            option_type: 'c' for call, 'p' for put
            
        Returns:
            Implied volatility as decimal (e.g., 0.20 for 20%) or None if calculation fails
        """
        try:
            # Validate inputs
            if option_price <= 0 or underlying_price <= 0 or strike_price <= 0:
                self.logger.warning(f"Invalid price inputs: option={option_price}, underlying={underlying_price}, strike={strike_price}",
                                  option_price=option_price, underlying_price=underlying_price, strike_price=strike_price)
                return None
            
            if time_to_expiration <= 0:
                self.logger.warning(f"Invalid time to expiration: {time_to_expiration}",
                                  time_to_expiration=time_to_expiration)
                return None
            
            if option_type not in ['c', 'p']:
                self.logger.warning(f"Invalid option type: {option_type}",
                                  option_type=option_type)
                return None
            
            # Calculate implied volatility using py_vollib
            iv = implied_volatility(
                price=option_price,
                S=underlying_price,
                K=strike_price,
                t=time_to_expiration,
                r=self.risk_free_rate,
                flag=option_type
            )
            
            # Validate result
            if iv is None or iv <= 0 or iv > 5.0:  # Cap at 500% volatility
                self.logger.warning(f"Invalid IV result: {iv}", iv_result=iv)
                return None
            
            return iv
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate implied volatility: {e}", 
                              error=str(e), option_price=option_price, 
                              underlying_price=underlying_price, strike_price=strike_price)
            return None
    
    def calculate_delta(
        self,
        underlying_price: float,
        strike_price: float,
        time_to_expiration: float,
        implied_vol: float,
        option_type: str
    ) -> Optional[float]:
        """
        Calculate option delta using Black-Scholes model.
        
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
                self.logger.warning(f"Invalid price inputs: underlying={underlying_price}, strike={strike_price}",
                                  underlying_price=underlying_price, strike_price=strike_price)
                return None
            
            if time_to_expiration <= 0:
                self.logger.warning(f"Invalid time to expiration: {time_to_expiration}",
                                  time_to_expiration=time_to_expiration)
                return None
            
            if implied_vol <= 0 or implied_vol > 5.0:
                self.logger.warning(f"Invalid implied volatility: {implied_vol}",
                                  implied_vol=implied_vol)
                return None
            
            if option_type not in ['c', 'p']:
                self.logger.warning(f"Invalid option type: {option_type}",
                                  option_type=option_type)
                return None
            
            # Calculate delta using py_vollib
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
    
    def process_options_with_iv(
        self,
        options: List[OptionData],
        underlying_price: float,
        expiration_date: str
    ) -> List[OptionData]:
        """
        Process list of options and calculate implied volatility and delta.
        Calculates IV based on bid, mid, and ask prices.
        Filters out options where calculations fail.
        
        Args:
            options: List of OptionData objects
            underlying_price: Current underlying stock price
            expiration_date: Expiration date string (YYYY-MM-DD)
            
        Returns:
            List of OptionData objects with calculated IV and delta (filtered)
        """
        from ..utils.calculation_utils import calculate_mid_price, calculate_implied_volatilities
        
        processed_options = []
        time_to_exp = calculate_time_to_expiration(expiration_date)
        
        for option in options:
            # Calculate implied volatility based on last price (original method)
            iv = self.calculate_implied_volatility(
                option_price=option.last_price,
                underlying_price=underlying_price,
                strike_price=option.strike,
                time_to_expiration=time_to_exp,
                option_type=option.option_type
            )
            
            # Skip options where IV calculation failed
            if iv is None:
                self.logger.debug(f"Skipping option with strike {option.strike} due to IV calculation failure",
                                strike=option.strike, option_type=option.option_type)
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
            
            # Create option dictionary for IV calculations
            option_dict = {
                'strike': option.strike,
                'bid': option.bid,
                'ask': option.ask,
                'impliedVolatility': iv  # Use the calculated IV as the YF IV
            }
            
            # Calculate IVs based on bid, mid, and ask prices
            iv_results = calculate_implied_volatilities(
                option=option_dict,
                current_price=underlying_price,
                time_to_expiration=time_to_exp,
                risk_free_rate=self.risk_free_rate,
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
                implied_volatility_bid=iv_results.get('impliedVolatilityBid'),
                implied_volatility_mid=iv_results.get('impliedVolatilityMid'),
                implied_volatility_ask=iv_results.get('impliedVolatilityAsk')
            )
            
            processed_options.append(processed_option)
        
        return processed_options