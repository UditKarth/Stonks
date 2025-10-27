"""
Advanced options pricing models beyond Black-Scholes.
"""
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import minimize_scalar
import warnings
warnings.filterwarnings('ignore')

# Import Black-Scholes function from core_models
try:
    from core_models import black_scholes_price
except ImportError:
    # Fallback if core_models is not available
    def black_scholes_price(S, K, T, r, sigma, option_type='call'):
        if T <= 0:
            return max(S - K, 0) if option_type == 'call' else max(K - S, 0)
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if option_type == 'call':
            return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

class AdvancedPricingModels:
    """Advanced options pricing models for various option types and market conditions."""
    
    def __init__(self):
        """Initialize the advanced pricing models."""
        self.default_steps = 100
        self.default_simulations = 10000
    
    def binomial_tree_price(self, S, K, T, r, sigma, option_type='call', 
                          n_steps=None, dividend_yield=0, american=True):
        """
        Binomial Tree pricing model for American and European options.
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free interest rate (annual)
            sigma (float): Volatility (annual)
            option_type (str): 'call' or 'put'
            n_steps (int): Number of time steps (default: calculated)
            dividend_yield (float): Dividend yield (annual)
            american (bool): True for American options, False for European
            
        Returns:
            dict: Pricing results with Greeks
        """
        if T <= 0:
            # At expiration
            if option_type == 'call':
                intrinsic_value = max(S - K, 0)
            else:
                intrinsic_value = max(K - S, 0)
            return {
                'price': intrinsic_value,
                'delta': 1.0 if intrinsic_value > 0 else 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0,
                'model': 'binomial_tree'
            }
        
        # Calculate optimal number of steps if not provided
        if n_steps is None:
            n_steps = max(50, int(T * 252))  # At least 50 steps, or daily steps
        
        # Calculate tree parameters
        dt = T / n_steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp((r - dividend_yield) * dt) - d) / (u - d)
        
        # Ensure probability is valid
        p = max(0, min(1, p))
        
        # Initialize stock price tree
        stock_prices = np.zeros((n_steps + 1, n_steps + 1))
        for i in range(n_steps + 1):
            for j in range(i + 1):
                stock_prices[j, i] = S * (u ** (i - j)) * (d ** j)
        
        # Initialize option value tree
        option_values = np.zeros((n_steps + 1, n_steps + 1))
        
        # Calculate terminal values
        for j in range(n_steps + 1):
            if option_type == 'call':
                option_values[j, n_steps] = max(stock_prices[j, n_steps] - K, 0)
            else:
                option_values[j, n_steps] = max(K - stock_prices[j, n_steps], 0)
        
        # Backward induction
        for i in range(n_steps - 1, -1, -1):
            for j in range(i + 1):
                # Expected value
                expected_value = np.exp(-r * dt) * (p * option_values[j, i + 1] + 
                                                  (1 - p) * option_values[j + 1, i + 1])
                
                if american:
                    # American option: check for early exercise
                    if option_type == 'call':
                        intrinsic_value = max(stock_prices[j, i] - K, 0)
                    else:
                        intrinsic_value = max(K - stock_prices[j, i], 0)
                    
                    option_values[j, i] = max(expected_value, intrinsic_value)
                else:
                    # European option
                    option_values[j, i] = expected_value
        
        # Calculate Greeks using finite differences
        price = option_values[0, 0]
        
        # Delta: sensitivity to stock price
        delta = (option_values[0, 1] - option_values[1, 1]) / (stock_prices[0, 1] - stock_prices[1, 1])
        
        # Gamma: second derivative with respect to stock price
        gamma = ((option_values[0, 1] - option_values[1, 1]) / (stock_prices[0, 1] - stock_prices[1, 1]) -
                (option_values[1, 1] - option_values[2, 1]) / (stock_prices[1, 1] - stock_prices[2, 1])) / \
               ((stock_prices[0, 1] - stock_prices[2, 1]) / 2)
        
        # Theta: sensitivity to time
        theta = (option_values[0, 1] - option_values[0, 0]) / dt / 365  # Per day
        
        # Vega: sensitivity to volatility (using small change in sigma)
        sigma_up = sigma * 1.01
        price_up = self.binomial_tree_price(S, K, T, r, sigma_up, option_type, n_steps, dividend_yield, american)['price']
        vega = (price_up - price) / (sigma_up - sigma) / 100  # Per 1% change
        
        # Rho: sensitivity to interest rate
        r_up = r + 0.01
        price_up = self.binomial_tree_price(S, K, T, r_up, sigma, option_type, n_steps, dividend_yield, american)['price']
        rho = (price_up - price) / 100  # Per 1% change
        
        return {
            'price': price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho,
            'model': 'binomial_tree',
            'steps': n_steps,
            'american': american
        }
    
    def monte_carlo_price(self, S, K, T, r, sigma, option_type='call', 
                         n_simulations=None, n_steps=None, dividend_yield=0,
                         barrier=None, barrier_type='down_and_out'):
        """
        Monte Carlo simulation for European and exotic options.
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free interest rate (annual)
            sigma (float): Volatility (annual)
            option_type (str): 'call' or 'put'
            n_simulations (int): Number of Monte Carlo simulations
            n_steps (int): Number of time steps per simulation
            dividend_yield (float): Dividend yield (annual)
            barrier (float): Barrier level for barrier options
            barrier_type (str): 'down_and_out', 'up_and_out', 'down_and_in', 'up_and_in'
            
        Returns:
            dict: Pricing results with confidence intervals
        """
        if T <= 0:
            if option_type == 'call':
                intrinsic_value = max(S - K, 0)
            else:
                intrinsic_value = max(K - S, 0)
            return {
                'price': intrinsic_value,
                'confidence_interval': (intrinsic_value, intrinsic_value),
                'model': 'monte_carlo'
            }
        
        if n_simulations is None:
            n_simulations = self.default_simulations
        if n_steps is None:
            n_steps = max(50, int(T * 252))
        
        dt = T / n_steps
        discount_factor = np.exp(-r * T)
        
        # Generate random numbers
        np.random.seed(42)  # For reproducibility
        random_numbers = np.random.normal(0, 1, (n_simulations, n_steps))
        
        # Simulate stock price paths
        stock_paths = np.zeros((n_simulations, n_steps + 1))
        stock_paths[:, 0] = S
        
        for i in range(n_steps):
            stock_paths[:, i + 1] = stock_paths[:, i] * np.exp(
                (r - dividend_yield - 0.5 * sigma**2) * dt + 
                sigma * np.sqrt(dt) * random_numbers[:, i]
            )
        
        # Calculate payoffs
        if barrier is None:
            # Vanilla European option
            if option_type == 'call':
                payoffs = np.maximum(stock_paths[:, -1] - K, 0)
            else:
                payoffs = np.maximum(K - stock_paths[:, -1], 0)
        else:
            # Barrier option
            payoffs = self._calculate_barrier_payoffs(
                stock_paths, K, barrier, barrier_type, option_type
            )
        
        # Discount payoffs
        discounted_payoffs = payoffs * discount_factor
        
        # Calculate statistics
        price = np.mean(discounted_payoffs)
        std_error = np.std(discounted_payoffs) / np.sqrt(n_simulations)
        confidence_interval = (
            price - 1.96 * std_error,
            price + 1.96 * std_error
        )
        
        # Calculate Greeks using finite differences
        delta = self._calculate_monte_carlo_greek(
            S * 1.01, K, T, r, sigma, option_type, n_simulations, n_steps, dividend_yield, barrier, barrier_type
        ) - price
        delta /= S * 0.01
        
        vega = self._calculate_monte_carlo_greek(
            S, K, T, r, sigma * 1.01, option_type, n_simulations, n_steps, dividend_yield, barrier, barrier_type
        ) - price
        vega /= sigma * 0.01 / 100  # Per 1% change
        
        return {
            'price': price,
            'confidence_interval': confidence_interval,
            'standard_error': std_error,
            'delta': delta,
            'vega': vega,
            'model': 'monte_carlo',
            'simulations': n_simulations,
            'steps': n_steps
        }
    
    def _calculate_barrier_payoffs(self, stock_paths, K, barrier, barrier_type, option_type):
        """Calculate payoffs for barrier options."""
        payoffs = np.zeros(len(stock_paths))
        
        for i, path in enumerate(stock_paths):
            if barrier_type == 'down_and_out':
                if np.min(path) <= barrier:
                    payoffs[i] = 0
                else:
                    if option_type == 'call':
                        payoffs[i] = max(path[-1] - K, 0)
                    else:
                        payoffs[i] = max(K - path[-1], 0)
            
            elif barrier_type == 'up_and_out':
                if np.max(path) >= barrier:
                    payoffs[i] = 0
                else:
                    if option_type == 'call':
                        payoffs[i] = max(path[-1] - K, 0)
                    else:
                        payoffs[i] = max(K - path[-1], 0)
            
            elif barrier_type == 'down_and_in':
                if np.min(path) <= barrier:
                    if option_type == 'call':
                        payoffs[i] = max(path[-1] - K, 0)
                    else:
                        payoffs[i] = max(K - path[-1], 0)
                else:
                    payoffs[i] = 0
            
            elif barrier_type == 'up_and_in':
                if np.max(path) >= barrier:
                    if option_type == 'call':
                        payoffs[i] = max(path[-1] - K, 0)
                    else:
                        payoffs[i] = max(K - path[-1], 0)
                else:
                    payoffs[i] = 0
        
        return payoffs
    
    def _calculate_monte_carlo_greek(self, S, K, T, r, sigma, option_type, n_simulations, n_steps, dividend_yield, barrier, barrier_type):
        """Helper method to calculate Greeks using Monte Carlo."""
        dt = T / n_steps
        discount_factor = np.exp(-r * T)
        
        np.random.seed(42)
        random_numbers = np.random.normal(0, 1, (n_simulations, n_steps))
        
        stock_paths = np.zeros((n_simulations, n_steps + 1))
        stock_paths[:, 0] = S
        
        for i in range(n_steps):
            stock_paths[:, i + 1] = stock_paths[:, i] * np.exp(
                (r - dividend_yield - 0.5 * sigma**2) * dt + 
                sigma * np.sqrt(dt) * random_numbers[:, i]
            )
        
        if barrier is None:
            if option_type == 'call':
                payoffs = np.maximum(stock_paths[:, -1] - K, 0)
            else:
                payoffs = np.maximum(K - stock_paths[:, -1], 0)
        else:
            payoffs = self._calculate_barrier_payoffs(
                stock_paths, K, barrier, barrier_type, option_type
            )
        
        return np.mean(payoffs * discount_factor)
    
    def heston_model_price(self, S, K, T, r, kappa, theta, sigma_v, rho, v0, option_type='call'):
        """
        Heston stochastic volatility model for options pricing.
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free interest rate (annual)
            kappa (float): Mean reversion speed
            theta (float): Long-term volatility
            sigma_v (float): Volatility of volatility
            rho (float): Correlation between stock and volatility
            v0 (float): Initial volatility
            option_type (str): 'call' or 'put'
            
        Returns:
            dict: Pricing results
        """
        if T <= 0:
            if option_type == 'call':
                intrinsic_value = max(S - K, 0)
            else:
                intrinsic_value = max(K - S, 0)
            return {
                'price': intrinsic_value,
                'model': 'heston'
            }
        
        # Heston model implementation using characteristic function
        def characteristic_function(u, T, S, K, r, kappa, theta, sigma_v, rho, v0):
            """Characteristic function for Heston model."""
            d = np.sqrt((rho * sigma_v * u * 1j - kappa)**2 - sigma_v**2 * (2 * u * 1j - u**2))
            g = (kappa - rho * sigma_v * u * 1j - d) / (kappa - rho * sigma_v * u * 1j + d)
            C = r * u * 1j * T + (kappa * theta / sigma_v**2) * ((kappa - rho * sigma_v * u * 1j - d) * T - 
                                                                2 * np.log((1 - g * np.exp(-d * T)) / (1 - g)))
            D = ((kappa - rho * sigma_v * u * 1j - d) / sigma_v**2) * ((1 - np.exp(-d * T)) / (1 - g * np.exp(-d * T)))
            
            return np.exp(C + D * v0)
        
        def integrand(u, T, S, K, r, kappa, theta, sigma_v, rho, v0):
            """Integrand for Heston option pricing formula."""
            cf = characteristic_function(u - 1j, T, S, K, r, kappa, theta, sigma_v, rho, v0)
            return np.real(np.exp(-1j * u * np.log(K)) * cf / (1j * u))
        
        # Numerical integration for option price
        from scipy.integrate import quad
        
        def integrand1(u):
            return integrand(u, T, S, K, r, kappa, theta, sigma_v, rho, v0)
        
        def integrand2(u):
            return integrand(u, T, S, K, r, kappa, theta, sigma_v, rho, v0) / (1j * u)
        
        # Calculate option price using Heston formula
        try:
            P1, _ = quad(integrand1, 0, np.inf, limit=1000)
            P2, _ = quad(integrand2, 0, np.inf, limit=1000)
            
            if option_type == 'call':
                price = S * (0.5 + P1 / np.pi) - K * np.exp(-r * T) * (0.5 + P2 / np.pi)
            else:
                price = K * np.exp(-r * T) * (0.5 - P2 / np.pi) - S * (0.5 - P1 / np.pi)
            
            # Ensure positive price
            price = max(price, 0)
            
        except:
            # Fallback to Black-Scholes if integration fails
            price = self._black_scholes_fallback(S, K, T, r, np.sqrt(theta), option_type)
        
        return {
            'price': price,
            'model': 'heston',
            'parameters': {
                'kappa': kappa,
                'theta': theta,
                'sigma_v': sigma_v,
                'rho': rho,
                'v0': v0
            }
        }
    
    def jump_diffusion_price(self, S, K, T, r, sigma, lambda_jump, mu_jump, sigma_jump, option_type='call'):
        """
        Merton's Jump Diffusion model for options pricing.
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free interest rate (annual)
            sigma (float): Volatility (annual)
            lambda_jump (float): Jump intensity
            mu_jump (float): Mean jump size
            sigma_jump (float): Jump volatility
            option_type (str): 'call' or 'put'
            
        Returns:
            dict: Pricing results
        """
        if T <= 0:
            if option_type == 'call':
                intrinsic_value = max(S - K, 0)
            else:
                intrinsic_value = max(K - S, 0)
            return {
                'price': intrinsic_value,
                'model': 'jump_diffusion'
            }
        
        # Merton's jump diffusion formula
        price = 0
        max_jumps = 20  # Truncate infinite sum
        
        for n in range(max_jumps):
            # Probability of n jumps
            prob_n_jumps = np.exp(-lambda_jump * T) * (lambda_jump * T)**n / np.math.factorial(n)
            
            # Adjusted parameters for n jumps
            sigma_n = np.sqrt(sigma**2 + n * sigma_jump**2 / T)
            r_n = r - lambda_jump * (np.exp(mu_jump + 0.5 * sigma_jump**2) - 1) + n * (mu_jump + 0.5 * sigma_jump**2) / T
            
            # Black-Scholes price with adjusted parameters
            bs_price = self._black_scholes_fallback(S, K, T, r_n, sigma_n, option_type)
            
            price += prob_n_jumps * bs_price
        
        return {
            'price': price,
            'model': 'jump_diffusion',
            'parameters': {
                'lambda_jump': lambda_jump,
                'mu_jump': mu_jump,
                'sigma_jump': sigma_jump
            }
        }
    
    def _black_scholes_fallback(self, S, K, T, r, sigma, option_type):
        """Fallback Black-Scholes calculation using core_models function."""
        return black_scholes_price(S, K, T, r, sigma, option_type)
    
    def compare_models(self, S, K, T, r, sigma, option_type='call', **kwargs):
        """
        Compare different pricing models for the same option.
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free interest rate (annual)
            sigma (float): Volatility (annual)
            option_type (str): 'call' or 'put'
            **kwargs: Additional parameters for specific models
            
        Returns:
            dict: Comparison of all models
        """
        results = {}
        
        # Black-Scholes (from core_models)
        try:
            from core_models import black_scholes_price
            bs_price = black_scholes_price(S, K, T, r, sigma, option_type)
            results['Black-Scholes'] = {
                'price': bs_price,
                'model': 'black_scholes'
            }
        except:
            pass
        
        # Binomial Tree
        try:
            binomial_result = self.binomial_tree_price(S, K, T, r, sigma, option_type, american=True)
            results['Binomial Tree (American)'] = binomial_result
        except Exception as e:
            results['Binomial Tree (American)'] = {'error': str(e)}
        
        # Monte Carlo
        try:
            mc_result = self.monte_carlo_price(S, K, T, r, sigma, option_type)
            results['Monte Carlo'] = mc_result
        except Exception as e:
            results['Monte Carlo'] = {'error': str(e)}
        
        # Heston Model (if parameters provided)
        if 'kappa' in kwargs and 'theta' in kwargs and 'sigma_v' in kwargs and 'rho' in kwargs and 'v0' in kwargs:
            try:
                heston_result = self.heston_model_price(
                    S, K, T, r, kwargs['kappa'], kwargs['theta'], 
                    kwargs['sigma_v'], kwargs['rho'], kwargs['v0'], option_type
                )
                results['Heston Model'] = heston_result
            except Exception as e:
                results['Heston Model'] = {'error': str(e)}
        
        # Jump Diffusion (if parameters provided)
        if 'lambda_jump' in kwargs and 'mu_jump' in kwargs and 'sigma_jump' in kwargs:
            try:
                jump_result = self.jump_diffusion_price(
                    S, K, T, r, sigma, kwargs['lambda_jump'], 
                    kwargs['mu_jump'], kwargs['sigma_jump'], option_type
                )
                results['Jump Diffusion'] = jump_result
            except Exception as e:
                results['Jump Diffusion'] = {'error': str(e)}
        
        return results
    
    def get_model_recommendations(self, S, K, T, r, sigma, option_type='call'):
        """
        Get recommendations for which pricing model to use based on option characteristics.
        
        Args:
            S (float): Current stock price
            K (float): Strike price
            T (float): Time to expiration (in years)
            r (float): Risk-free interest rate (annual)
            sigma (float): Volatility (annual)
            option_type (str): 'call' or 'put'
            
        Returns:
            dict: Model recommendations with explanations
        """
        recommendations = {}
        
        # Time to expiration analysis
        if T < 0.1:  # Less than 1 month
            recommendations['primary'] = 'Binomial Tree'
            recommendations['reason'] = 'Short-term options benefit from American exercise features'
        elif T > 2:  # More than 2 years
            recommendations['primary'] = 'Monte Carlo'
            recommendations['reason'] = 'Long-term options benefit from path-dependent analysis'
        else:
            recommendations['primary'] = 'Black-Scholes'
            recommendations['reason'] = 'Medium-term European options are well-suited for Black-Scholes'
        
        # Volatility analysis
        if sigma > 0.5:  # High volatility
            recommendations['high_vol'] = 'Heston Model'
            recommendations['high_vol_reason'] = 'High volatility environments benefit from stochastic volatility models'
        
        # Moneyness analysis
        moneyness = S / K
        if moneyness < 0.8 or moneyness > 1.2:  # Deep ITM or OTM
            recommendations['extreme_moneyness'] = 'Monte Carlo'
            recommendations['extreme_moneyness_reason'] = 'Extreme moneyness options benefit from simulation-based pricing'
        
        return recommendations
