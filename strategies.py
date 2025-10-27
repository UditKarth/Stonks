"""
Options strategy framework with object-oriented design.
"""
import numpy as np
from abc import ABC, abstractmethod
from core_models import (
    black_scholes_price, calculate_all_greeks, 
    time_to_expiration, implied_volatility
)

class OptionLeg:
    """Represents a single option leg in a strategy."""
    
    def __init__(self, option_type, position, strike, premium, expiration, quantity=1):
        """
        Initialize an option leg.
        
        Args:
            option_type (str): 'call' or 'put'
            position (str): 'long' or 'short'
            strike (float): Strike price
            premium (float): Option premium paid/received
            expiration (str): Expiration date 'YYYY-MM-DD'
            quantity (int): Number of contracts
        """
        self.option_type = option_type.lower()
        self.position = position.lower()
        self.strike = strike
        self.premium = premium
        self.expiration = expiration
        self.quantity = quantity
        
        # Validate inputs
        if self.option_type not in ['call', 'put']:
            raise ValueError("Option type must be 'call' or 'put'")
        if self.position not in ['long', 'short']:
            raise ValueError("Position must be 'long' or 'short'")
    
    def payoff_at_expiration(self, stock_price):
        """
        Calculate payoff at expiration.
        
        Args:
            stock_price (float): Stock price at expiration
            
        Returns:
            float: Payoff for this leg
        """
        if self.option_type == 'call':
            intrinsic_value = max(stock_price - self.strike, 0)
        else:  # put
            intrinsic_value = max(self.strike - stock_price, 0)
        
        if self.position == 'long':
            return self.quantity * (intrinsic_value - self.premium)
        else:  # short
            return self.quantity * (self.premium - intrinsic_value)
    
    def calculate_greeks(self, S, T, r, sigma):
        """
        Calculate Greeks for this leg.
        
        Args:
            S (float): Current stock price
            T (float): Time to expiration
            r (float): Risk-free rate
            sigma (float): Volatility
            
        Returns:
            dict: Greeks for this leg
        """
        greeks = calculate_all_greeks(S, self.strike, T, r, sigma, self.option_type)
        
        # Adjust for position and quantity
        multiplier = self.quantity if self.position == 'long' else -self.quantity
        
        return {
            'delta': greeks['delta'] * multiplier,
            'gamma': greeks['gamma'] * multiplier,
            'theta': greeks['theta'] * multiplier,
            'vega': greeks['vega'] * multiplier,
            'rho': greeks['rho'] * multiplier
        }

class Strategy(ABC):
    """Abstract base class for options strategies."""
    
    def __init__(self, name, legs):
        """
        Initialize a strategy.
        
        Args:
            name (str): Strategy name
            legs (list): List of OptionLeg objects
        """
        self.name = name
        self.legs = legs
        self.validate_strategy()
    
    def validate_strategy(self):
        """Validate that the strategy has the correct number and types of legs."""
        pass  # Override in subclasses
    
    def total_premium(self):
        """Calculate total premium paid/received."""
        total = 0
        for leg in self.legs:
            if leg.position == 'long':
                total -= leg.premium * leg.quantity
            else:
                total += leg.premium * leg.quantity
        return total
    
    def payoff_at_expiration(self, stock_price):
        """
        Calculate total payoff at expiration.
        
        Args:
            stock_price (float): Stock price at expiration
            
        Returns:
            float: Total payoff
        """
        return sum(leg.payoff_at_expiration(stock_price) for leg in self.legs)
    
    def calculate_greeks(self, S, T, r, sigma):
        """
        Calculate total Greeks for the strategy.
        
        Args:
            S (float): Current stock price
            T (float): Time to expiration
            r (float): Risk-free rate
            sigma (float): Volatility
            
        Returns:
            dict: Total Greeks
        """
        total_greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
        
        for leg in self.legs:
            leg_greeks = leg.calculate_greeks(S, T, r, sigma)
            for greek in total_greeks:
                total_greeks[greek] += leg_greeks[greek]
        
        return total_greeks
    
    @abstractmethod
    def max_profit(self):
        """Calculate maximum profit."""
        pass
    
    @abstractmethod
    def max_loss(self):
        """Calculate maximum loss."""
        pass
    
    @abstractmethod
    def break_even_points(self):
        """Calculate break-even points."""
        pass

# Single Leg Strategies
class LongCall(Strategy):
    """Long Call strategy."""
    
    def __init__(self, strike, premium, expiration, quantity=1):
        leg = OptionLeg('call', 'long', strike, premium, expiration, quantity)
        super().__init__('Long Call', [leg])
    
    def max_profit(self):
        return float('inf')  # Unlimited upside
    
    def max_loss(self):
        return -self.total_premium()
    
    def break_even_points(self):
        return [self.legs[0].strike + self.legs[0].premium]

class ShortCall(Strategy):
    """Short Call strategy."""
    
    def __init__(self, strike, premium, expiration, quantity=1):
        leg = OptionLeg('call', 'short', strike, premium, expiration, quantity)
        super().__init__('Short Call', [leg])
    
    def max_profit(self):
        return self.total_premium()
    
    def max_loss(self):
        return float('inf')  # Unlimited downside
    
    def break_even_points(self):
        return [self.legs[0].strike + self.legs[0].premium]

class LongPut(Strategy):
    """Long Put strategy."""
    
    def __init__(self, strike, premium, expiration, quantity=1):
        leg = OptionLeg('put', 'long', strike, premium, expiration, quantity)
        super().__init__('Long Put', [leg])
    
    def max_profit(self):
        return self.legs[0].strike - self.legs[0].premium
    
    def max_loss(self):
        return -self.total_premium()
    
    def break_even_points(self):
        return [self.legs[0].strike - self.legs[0].premium]

class ShortPut(Strategy):
    """Short Put strategy."""
    
    def __init__(self, strike, premium, expiration, quantity=1):
        leg = OptionLeg('put', 'short', strike, premium, expiration, quantity)
        super().__init__('Short Put', [leg])
    
    def max_profit(self):
        return self.total_premium()
    
    def max_loss(self):
        return self.legs[0].strike - self.legs[0].premium
    
    def break_even_points(self):
        return [self.legs[0].strike - self.legs[0].premium]

# Spread Strategies
class BullCallSpread(Strategy):
    """Bull Call Spread strategy."""
    
    def __init__(self, long_strike, short_strike, long_premium, short_premium, expiration, quantity=1):
        long_leg = OptionLeg('call', 'long', long_strike, long_premium, expiration, quantity)
        short_leg = OptionLeg('call', 'short', short_strike, short_premium, expiration, quantity)
        super().__init__('Bull Call Spread', [long_leg, short_leg])
    
    def validate_strategy(self):
        if len(self.legs) != 2:
            raise ValueError("Bull Call Spread must have exactly 2 legs")
        if self.legs[0].strike >= self.legs[1].strike:
            raise ValueError("Long strike must be lower than short strike")
    
    def max_profit(self):
        return (self.legs[1].strike - self.legs[0].strike) + self.total_premium()
    
    def max_loss(self):
        return -self.total_premium()
    
    def break_even_points(self):
        return [self.legs[0].strike + self.total_premium()]

class BearPutSpread(Strategy):
    """Bear Put Spread strategy."""
    
    def __init__(self, long_strike, short_strike, long_premium, short_premium, expiration, quantity=1):
        long_leg = OptionLeg('put', 'long', long_strike, long_premium, expiration, quantity)
        short_leg = OptionLeg('put', 'short', short_strike, short_premium, expiration, quantity)
        super().__init__('Bear Put Spread', [long_leg, short_leg])
    
    def validate_strategy(self):
        if len(self.legs) != 2:
            raise ValueError("Bear Put Spread must have exactly 2 legs")
        if self.legs[0].strike <= self.legs[1].strike:
            raise ValueError("Long strike must be higher than short strike")
    
    def max_profit(self):
        return (self.legs[0].strike - self.legs[1].strike) + self.total_premium()
    
    def max_loss(self):
        return -self.total_premium()
    
    def break_even_points(self):
        return [self.legs[0].strike - self.total_premium()]

# Complex Strategies
class IronCondor(Strategy):
    """Iron Condor strategy."""
    
    def __init__(self, put_short_strike, put_long_strike, call_short_strike, call_long_strike,
                 put_short_premium, put_long_premium, call_short_premium, call_long_premium,
                 expiration, quantity=1):
        legs = [
            OptionLeg('put', 'short', put_short_strike, put_short_premium, expiration, quantity),
            OptionLeg('put', 'long', put_long_strike, put_long_premium, expiration, quantity),
            OptionLeg('call', 'short', call_short_strike, call_short_premium, expiration, quantity),
            OptionLeg('call', 'long', call_long_strike, call_long_premium, expiration, quantity)
        ]
        super().__init__('Iron Condor', legs)
    
    def validate_strategy(self):
        if len(self.legs) != 4:
            raise ValueError("Iron Condor must have exactly 4 legs")
        # Validate strike order: put_long < put_short < call_short < call_long
        strikes = [leg.strike for leg in self.legs]
        if not (strikes[1] < strikes[0] < strikes[2] < strikes[3]):
            raise ValueError("Invalid strike order for Iron Condor")
    
    def max_profit(self):
        return self.total_premium()
    
    def max_loss(self):
        # Max loss is the difference between adjacent strikes minus net premium
        put_spread_width = self.legs[0].strike - self.legs[1].strike
        call_spread_width = self.legs[3].strike - self.legs[2].strike
        max_loss = max(put_spread_width, call_spread_width) - self.total_premium()
        return max_loss
    
    def break_even_points(self):
        # Two break-even points for Iron Condor
        net_premium = self.total_premium()
        return [
            self.legs[0].strike - net_premium,  # Lower break-even
            self.legs[2].strike + net_premium    # Upper break-even
        ]

class LongStraddle(Strategy):
    """Long Straddle strategy."""
    
    def __init__(self, strike, call_premium, put_premium, expiration, quantity=1):
        call_leg = OptionLeg('call', 'long', strike, call_premium, expiration, quantity)
        put_leg = OptionLeg('put', 'long', strike, put_premium, expiration, quantity)
        super().__init__('Long Straddle', [call_leg, put_leg])
    
    def validate_strategy(self):
        if len(self.legs) != 2:
            raise ValueError("Long Straddle must have exactly 2 legs")
        if self.legs[0].strike != self.legs[1].strike:
            raise ValueError("Both legs must have the same strike price")
    
    def max_profit(self):
        return float('inf')  # Unlimited upside in both directions
    
    def max_loss(self):
        return -self.total_premium()
    
    def break_even_points(self):
        total_premium = self.total_premium()
        strike = self.legs[0].strike
        return [strike - total_premium, strike + total_premium]

# Strategy factory function
def create_strategy(strategy_type, **kwargs):
    """
    Factory function to create strategy objects.
    
    Args:
        strategy_type (str): Type of strategy to create
        **kwargs: Strategy-specific parameters
        
    Returns:
        Strategy: Strategy object
    """
    strategy_map = {
        'Long Call': LongCall,
        'Short Call': ShortCall,
        'Long Put': LongPut,
        'Short Put': ShortPut,
        'Bull Call Spread': BullCallSpread,
        'Bear Put Spread': BearPutSpread,
        'Iron Condor': IronCondor,
        'Long Straddle': LongStraddle
    }
    
    if strategy_type not in strategy_map:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    return strategy_map[strategy_type](**kwargs)
