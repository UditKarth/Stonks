"""
yfinance options data fetcher with intelligent caching.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import logging
from cache_manager import cache_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptionsDataFetcher:
    """Fetches real-time options data using yfinance with intelligent caching."""
    
    def __init__(self):
        """Initialize the options data fetcher."""
        self.cache_manager = cache_manager
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
    
    def _retry_on_failure(self, func, *args, **kwargs):
        """
        Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises exception after all retries
        """
        for attempt in range(self.retry_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    logger.error(f"All retry attempts failed for {func.__name__}: {str(e)}")
                    raise e
                else:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
    
    def get_options_chain(self, ticker: str, expiration_date: str = None) -> Dict:
        """
        Get complete options chain for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            expiration_date (str): Specific expiration date (YYYY-MM-DD) or None for all
            
        Returns:
            Dict: Options chain data with calls and puts
        """
        # Check cache first
        cached_data = self.cache_manager.get_options_chain(ticker, expiration_date)
        if cached_data is not None:
            logger.info(f"Using cached options chain for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching options chain for {ticker}")
            
            # Create yfinance ticker object
            stock = yf.Ticker(ticker)
            
            # Get options expiration dates
            expirations = stock.options
            if not expirations:
                raise ValueError(f"No options data available for {ticker}")
            
            # Filter by specific expiration if provided
            if expiration_date:
                if expiration_date not in expirations:
                    # Find closest expiration date
                    exp_date_obj = datetime.strptime(expiration_date, '%Y-%m-%d')
                    closest_exp = min(expirations, 
                                   key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - exp_date_obj).days))
                    logger.warning(f"Requested expiration {expiration_date} not found, using closest: {closest_exp}")
                    expiration_date = closest_exp
                expirations = [expiration_date]
            
            # Get options chain for the first (or specified) expiration
            target_expiration = expirations[0]
            options_chain = stock.option_chain(target_expiration)
            
            # Process calls data
            calls_data = self._process_options_data(options_chain.calls, 'call')
            
            # Process puts data
            puts_data = self._process_options_data(options_chain.puts, 'put')
            
            # Combine data
            options_data = {
                'ticker': ticker,
                'expiration': target_expiration,
                'available_expirations': expirations,
                'calls': calls_data,
                'puts': puts_data,
                'data_source': 'yfinance',
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the data
            self.cache_manager.set_options_chain(ticker, options_data, expiration_date)
            
            logger.info(f"Successfully fetched options chain for {ticker}")
            return options_data
            
        except Exception as e:
            logger.error(f"Error fetching options chain for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch options data for {ticker}: {str(e)}")
    
    def _process_options_data(self, options_df: pd.DataFrame, option_type: str) -> Dict:
        """
        Process raw options data from yfinance.
        
        Args:
            options_df (pd.DataFrame): Raw options data
            option_type (str): 'call' or 'put'
            
        Returns:
            Dict: Processed options data
        """
        if options_df.empty:
            return {
                'strikes': [],
                'bids': [],
                'asks': [],
                'lastPrices': [],
                'volumes': [],
                'openInterests': [],
                'impliedVolatilities': [],
                'contracts': []
            }
        
        # Clean and process the data
        processed_data = {
            'strikes': options_df['strike'].tolist(),
            'bids': options_df['bid'].fillna(0).tolist(),
            'asks': options_df['ask'].fillna(0).tolist(),
            'lastPrices': options_df['lastPrice'].fillna(0).tolist(),
            'volumes': options_df['volume'].fillna(0).astype(int).tolist(),
            'openInterests': options_df['openInterest'].fillna(0).astype(int).tolist(),
            'impliedVolatilities': options_df['impliedVolatility'].fillna(0).tolist(),
            'contracts': options_df['contractSymbol'].tolist()
        }
        
        return processed_data
    
    def get_option_quote(self, ticker: str, strike: float, expiration: str, option_type: str) -> Dict:
        """
        Get specific option quote.
        
        Args:
            ticker (str): Stock ticker symbol
            strike (float): Strike price
            expiration (str): Expiration date
            option_type (str): 'call' or 'put'
            
        Returns:
            Dict: Option quote data
        """
        # Check cache first
        cached_data = self.cache_manager.get_option_quote(ticker, strike, expiration, option_type)
        if cached_data is not None:
            return cached_data
        
        try:
            # Get full options chain
            options_chain = self.get_options_chain(ticker, expiration)
            
            # Find the specific option
            option_data = self._find_option_in_chain(options_chain, strike, option_type)
            
            if option_data is None:
                raise ValueError(f"Option not found: {ticker} {strike} {expiration} {option_type}")
            
            # Cache the specific option quote
            self.cache_manager.set_option_quote(ticker, strike, expiration, option_type, option_data)
            
            return option_data
            
        except Exception as e:
            logger.error(f"Error fetching option quote: {str(e)}")
            raise Exception(f"Failed to fetch option quote: {str(e)}")
    
    def _find_option_in_chain(self, options_chain: Dict, strike: float, option_type: str) -> Optional[Dict]:
        """
        Find specific option in options chain.
        
        Args:
            options_chain (Dict): Options chain data
            strike (float): Strike price
            option_type (str): 'call' or 'put'
            
        Returns:
            Dict or None: Option data if found
        """
        try:
            options_data = options_chain[option_type + 's']  # 'calls' or 'puts'
            
            # Find the closest strike price
            strikes = np.array(options_data['strikes'])
            closest_idx = np.argmin(np.abs(strikes - strike))
            
            # Check if the strike is close enough (within $0.50)
            if abs(strikes[closest_idx] - strike) > 0.50:
                return None
            
            # Return the option data
            return {
                'strike': strikes[closest_idx],
                'bid': options_data['bids'][closest_idx],
                'ask': options_data['asks'][closest_idx],
                'lastPrice': options_data['lastPrices'][closest_idx],
                'volume': options_data['volumes'][closest_idx],
                'openInterest': options_data['openInterests'][closest_idx],
                'impliedVolatility': options_data['impliedVolatilities'][closest_idx],
                'contractSymbol': options_data['contracts'][closest_idx],
                'optionType': option_type,
                'expiration': options_chain['expiration']
            }
            
        except Exception as e:
            logger.error(f"Error finding option in chain: {str(e)}")
            return None
    
    def get_available_expirations(self, ticker: str) -> List[str]:
        """
        Get available expiration dates for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            List[str]: Available expiration dates
        """
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            
            if not expirations:
                raise ValueError(f"No options data available for {ticker}")
            
            # Sort by date
            expirations.sort()
            return expirations
            
        except Exception as e:
            logger.error(f"Error fetching expirations for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch expiration dates for {ticker}: {str(e)}")
    
    def get_strike_range(self, ticker: str, expiration: str = None, 
                        moneyness_range: Tuple[float, float] = (0.8, 1.2)) -> List[float]:
        """
        Get available strike prices within a moneyness range.
        
        Args:
            ticker (str): Stock ticker symbol
            expiration (str): Expiration date
            moneyness_range (Tuple): (min_moneyness, max_moneyness) relative to current price
            
        Returns:
            List[float]: Available strike prices
        """
        try:
            # Get current stock price
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            
            # Get options chain
            options_chain = self.get_options_chain(ticker, expiration)
            
            # Get all strikes
            all_strikes = set()
            all_strikes.update(options_chain['calls']['strikes'])
            all_strikes.update(options_chain['puts']['strikes'])
            
            # Filter by moneyness range
            min_strike = current_price * moneyness_range[0]
            max_strike = current_price * moneyness_range[1]
            
            filtered_strikes = [s for s in all_strikes if min_strike <= s <= max_strike]
            filtered_strikes.sort()
            
            return filtered_strikes
            
        except Exception as e:
            logger.error(f"Error getting strike range for {ticker}: {str(e)}")
            raise Exception(f"Failed to get strike range for {ticker}: {str(e)}")
    
    def validate_ticker_has_options(self, ticker: str) -> bool:
        """
        Check if a ticker has options data available.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            bool: True if options data is available
        """
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            return len(expirations) > 0
        except:
            return False
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics
        """
        return self.cache_manager.get_cache_stats()
    
    def clear_cache(self, cache_type: str = None) -> None:
        """
        Clear cache data.
        
        Args:
            cache_type (str): Specific cache to clear
        """
        self.cache_manager.clear_cache(cache_type)
        logger.info(f"Cache cleared: {cache_type or 'all'}")
    
    def get_data_quality_info(self, ticker: str) -> Dict:
        """
        Get data quality information for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Dict: Data quality metrics
        """
        try:
            options_chain = self.get_options_chain(ticker)
            
            # Calculate data quality metrics
            calls_data = options_chain['calls']
            puts_data = options_chain['puts']
            
            total_options = len(calls_data['strikes']) + len(puts_data['strikes'])
            options_with_bid_ask = sum(1 for bid, ask in zip(calls_data['bids'] + puts_data['bids'], 
                                                           calls_data['asks'] + puts_data['asks']) 
                                     if bid > 0 and ask > 0)
            
            data_quality = {
                'total_options': total_options,
                'options_with_quotes': options_with_bid_ask,
                'quote_coverage': options_with_bid_ask / total_options if total_options > 0 else 0,
                'data_source': 'yfinance',
                'last_updated': options_chain['timestamp'],
                'expiration': options_chain['expiration']
            }
            
            return data_quality
            
        except Exception as e:
            logger.error(f"Error getting data quality info for {ticker}: {str(e)}")
            return {
                'total_options': 0,
                'options_with_quotes': 0,
                'quote_coverage': 0,
                'data_source': 'error',
                'last_updated': datetime.now().isoformat(),
                'expiration': None
            }
