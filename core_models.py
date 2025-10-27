"""
Core mathematical models for options pricing and Greeks calculations.
"""
import numpy as np
from scipy.stats import norm
from scipy.optimize import newton

def black_scholes_price(S, K, T, r, sigma, option_type='call'):
    """
    Calculate Black-Scholes option price.
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility (annual)
        option_type (str): 'call' or 'put'
        
    Returns:
        float: Option price
    """
    if T <= 0:
        # At expiration
        if option_type == 'call':
            return max(S - K, 0)
        else:
            return max(K - S, 0)
    
    # Calculate d1 and d2
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    return price

def delta(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option delta.
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility (annual)
        option_type (str): 'call' or 'put'
        
    Returns:
        float: Delta value
    """
    if T <= 0:
        # At expiration
        if option_type == 'call':
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    
    if option_type == 'call':
        return norm.cdf(d1)
    else:  # put
        return norm.cdf(d1) - 1

def gamma(S, K, T, r, sigma):
    """
    Calculate option gamma.
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility (annual)
        
    Returns:
        float: Gamma value
    """
    if T <= 0:
        return 0.0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))

def theta(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option theta (time decay).
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility (annual)
        option_type (str): 'call' or 'put'
        
    Returns:
        float: Theta value (per day)
    """
    if T <= 0:
        return 0.0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    term1 = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
    term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
    
    if option_type == 'call':
        theta = (term1 + term2) / 365  # Convert to per day
    else:  # put
        theta = (term1 - term2) / 365  # Convert to per day
    
    return theta

def vega(S, K, T, r, sigma):
    """
    Calculate option vega.
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility (annual)
        
    Returns:
        float: Vega value (per 1% change in volatility)
    """
    if T <= 0:
        return 0.0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change

def rho(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option rho.
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility (annual)
        option_type (str): 'call' or 'put'
        
    Returns:
        float: Rho value (per 1% change in interest rate)
    """
    if T <= 0:
        return 0.0
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        return K * T * np.exp(-r * T) * norm.cdf(d2) / 100  # Per 1% change
    else:  # put
        return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100  # Per 1% change

def implied_volatility(market_price, S, K, T, r, option_type='call'):
    """
    Calculate implied volatility using Newton's method.
    
    Args:
        market_price (float): Market price of the option
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        option_type (str): 'call' or 'put'
        
    Returns:
        float: Implied volatility
    """
    def objective(sigma):
        return black_scholes_price(S, K, T, r, sigma, option_type) - market_price
    
    def derivative(sigma):
        return vega(S, K, T, r, sigma) * 100  # Convert vega to per 1% change
    
    try:
        # Start with a reasonable initial guess
        initial_guess = 0.2  # 20% volatility
        
        # Use Newton's method to find implied volatility
        iv = newton(objective, initial_guess, fprime=derivative, maxiter=100)
        
        # Ensure positive volatility
        return max(iv, 0.001)
        
    except:
        # If Newton's method fails, try bisection
        try:
            from scipy.optimize import brentq
            iv = brentq(objective, 0.001, 2.0)  # Search between 0.1% and 200%
            return iv
        except:
            return 0.2  # Return default volatility if all methods fail

def calculate_all_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate all Greeks for an option.
    
    Args:
        S (float): Current stock price
        K (float): Strike price
        T (float): Time to expiration (in years)
        r (float): Risk-free interest rate (annual)
        sigma (float): Volatility (annual)
        option_type (str): 'call' or 'put'
        
    Returns:
        dict: Dictionary containing all Greeks
    """
    return {
        'delta': delta(S, K, T, r, sigma, option_type),
        'gamma': gamma(S, K, T, r, sigma),
        'theta': theta(S, K, T, r, sigma, option_type),
        'vega': vega(S, K, T, r, sigma),
        'rho': rho(S, K, T, r, sigma, option_type)
    }

def time_to_expiration(expiration_date):
    """
    Calculate time to expiration in years.
    
    Args:
        expiration_date (str): Expiration date in 'YYYY-MM-DD' format
        
    Returns:
        float: Time to expiration in years
    """
    from datetime import datetime
    
    try:
        exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
        current_date = datetime.now()
        time_diff = exp_date - current_date
        return max(time_diff.days / 365.25, 0)  # Convert to years, minimum 0
    except:
        return 0
