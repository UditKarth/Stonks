"""
Data fetching module for Alpha Vantage API (free tier) and yfinance integration.
Uses Alpha Vantage free endpoints first, falls back to yfinance for premium-gated features.
"""
import pandas as pd
import numpy as np
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import config
from options_data_fetcher import OptionsDataFetcher
from cache_manager import cache_manager
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    """Class to handle data fetching from Alpha Vantage free tier (primary) and yfinance (fallback)."""
    
    def __init__(self):
        """Initialize the data fetcher with API key and options fetcher."""
        self.api_key = config.ALPHA_VANTAGE_KEY
        try:
            self.ts = TimeSeries(key=self.api_key, output_format='pandas') if self.api_key else None
        except:
            self.ts = None
        self.options_fetcher = OptionsDataFetcher()
        self.cache_manager = cache_manager
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry function with exponential backoff for rate limiting.
        
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
                error_msg = str(e).lower()
                # Check if it's a rate limit error
                is_rate_limit = ('rate limit' in error_msg or 
                                'too many requests' in error_msg or
                                '429' in error_msg)
                
                if attempt == self.retry_attempts - 1:
                    logger.error(f"All retry attempts failed for {func.__name__}: {str(e)}")
                    raise e
                elif is_rate_limit:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limited on attempt {attempt + 1} for {func.__name__}, retrying in {delay}s")
                    time.sleep(delay)
                else:
                    # For non-rate-limit errors, don't retry
                    raise e
    
    def get_stock_quote(self, ticker):
        """
        Get current stock price for a given ticker using Alpha Vantage free tier (primary) or yfinance (fallback).
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            float: Current stock price
        """
        # Check cache first
        cached_price = self.cache_manager.get_stock_quote(ticker)
        if cached_price is not None:
            return cached_price
        
        # Try Alpha Vantage free tier first (GLOBAL_QUOTE endpoint)
        if self.ts:
            try:
                data, meta_data = self.ts.get_quote_endpoint(symbol=ticker)
                current_price = float(data['05. price'].iloc[0])
                # Cache the price
                self.cache_manager.set_stock_quote(ticker, current_price)
                return current_price
            except Exception as e:
                logger.warning(f"Alpha Vantage quote failed for {ticker}: {str(e)}")
        
        # Fallback to yfinance if Alpha Vantage fails
        try:
            def _fetch_yfinance_quote():
                stock = yf.Ticker(ticker)
                info = stock.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                if current_price:
                    return float(current_price)
                raise ValueError("No price data available")
            
            current_price = self._retry_with_backoff(_fetch_yfinance_quote)
            # Cache the price
            self.cache_manager.set_stock_quote(ticker, current_price)
            return current_price
        except Exception as e:
            raise Exception(f"Error fetching stock quote for {ticker}: Alpha Vantage failed, yfinance failed ({str(e)})")
    
    def get_historical_volatility(self, ticker, period='1y'):
        """
        Calculate annualized historical volatility from historical data.
        Uses Alpha Vantage free tier (TIME_SERIES_DAILY) first, falls back to yfinance.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period for historical data ('1y', '6mo', '3mo')
            
        Returns:
            float: Annualized volatility
        """
        # Check cache first
        cached_volatility = self.cache_manager.get_volatility(ticker)
        if cached_volatility is not None:
            return cached_volatility
        
        # Try Alpha Vantage free tier first (TIME_SERIES_DAILY - not the premium DAILY_ADJUSTED)
        if self.ts:
            try:
                # Map period to Alpha Vantage output size
                output_size_map = {
                    '1y': 'full',
                    '6mo': 'compact',
                    '3mo': 'compact'
                }
                
                output_size = output_size_map.get(period, 'compact')
                
                # Use TIME_SERIES_DAILY (free) instead of TIME_SERIES_DAILY_ADJUSTED (premium)
                data, meta_data = self.ts.get_daily(
                    symbol=ticker, 
                    outputsize=output_size
                )
                
                # Calculate daily returns using close price
                # Note: Using '4. close' for free tier (not adjusted)
                data['daily_return'] = data['4. close'].pct_change()
                
                # Calculate volatility (annualized)
                daily_volatility = data['daily_return'].std()
                annualized_volatility = daily_volatility * np.sqrt(252)  # 252 trading days per year
                
                # Cache the volatility
                self.cache_manager.set_volatility(ticker, annualized_volatility)
                
                logger.info(f"Successfully calculated volatility for {ticker} using Alpha Vantage free tier")
                return annualized_volatility
                
            except Exception as av_error:
                error_msg = str(av_error)
                # Check if it's a premium endpoint error
                if 'premium' in error_msg.lower():
                    logger.warning(f"Alpha Vantage premium endpoint error for {ticker}, falling back to yfinance")
                else:
                    logger.warning(f"Alpha Vantage failed for {ticker}: {error_msg}")
        
        # Fallback to yfinance if Alpha Vantage fails
        try:
            def _fetch_yfinance_volatility():
                stock = yf.Ticker(ticker)
                
                # Map period to yfinance period
                period_map = {
                    '1y': '1y',
                    '6mo': '6mo',
                    '3mo': '3mo'
                }
                yf_period = period_map.get(period, '1y')
                
                # Get historical data
                hist = stock.history(period=yf_period)
                
                if hist.empty:
                    raise ValueError("No historical data available")
                
                # Calculate daily returns
                hist['daily_return'] = hist['Close'].pct_change()
                
                # Calculate volatility (annualized)
                daily_volatility = hist['daily_return'].std()
                annualized_volatility = daily_volatility * np.sqrt(252)  # 252 trading days per year
                
                return annualized_volatility
            
            annualized_volatility = self._retry_with_backoff(_fetch_yfinance_volatility)
            
            # Cache the volatility
            self.cache_manager.set_volatility(ticker, annualized_volatility)
            
            logger.info(f"Successfully calculated volatility for {ticker} using yfinance")
            return annualized_volatility
            
        except Exception as e:
            raise Exception(f"Error calculating volatility for {ticker}: Alpha Vantage free tier failed, yfinance failed ({str(e)})")
    
    def get_historical_data(self, ticker, period='1y'):
        """
        Get historical stock data for additional analysis.
        Uses Alpha Vantage free tier (TIME_SERIES_DAILY) first, falls back to yfinance.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period for historical data
            
        Returns:
            pandas.DataFrame: Historical stock data
        """
        # Try Alpha Vantage free tier first
        if self.ts:
            try:
                output_size_map = {
                    '1y': 'full',
                    '6mo': 'compact',
                    '3mo': 'compact'
                }
                
                output_size = output_size_map.get(period, 'compact')
                
                # Use TIME_SERIES_DAILY (free) instead of TIME_SERIES_DAILY_ADJUSTED (premium)
                data, meta_data = self.ts.get_daily(
                    symbol=ticker, 
                    outputsize=output_size
                )
                
                return data
            except Exception as e:
                error_msg = str(e)
                if 'premium' in error_msg.lower():
                    logger.warning(f"Alpha Vantage premium endpoint error for {ticker}, falling back to yfinance")
                else:
                    logger.warning(f"Alpha Vantage failed for {ticker}: {error_msg}")
        
        # Fallback to yfinance
        try:
            def _fetch_yfinance_data():
                stock = yf.Ticker(ticker)
                
                # Map period to yfinance period
                period_map = {
                    '1y': '1y',
                    '6mo': '6mo',
                    '3mo': '3mo'
                }
                yf_period = period_map.get(period, '1y')
                
                hist = stock.history(period=yf_period)
                
                if hist.empty:
                    raise ValueError("No historical data available")
                
                return hist
            
            return self._retry_with_backoff(_fetch_yfinance_data)
            
        except Exception as e:
            raise Exception(f"Error fetching historical data for {ticker}: Alpha Vantage free tier failed, yfinance failed ({str(e)})")
    
    def validate_ticker(self, ticker):
        """
        Validate if a ticker exists by attempting to fetch its quote.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            bool: True if ticker is valid, False otherwise
        """
        try:
            self.get_stock_quote(ticker)
            return True
        except:
            return False
    
    # Options data methods using yfinance
    def get_options_chain(self, ticker, expiration_date=None):
        """
        Get complete options chain for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            expiration_date (str): Specific expiration date (YYYY-MM-DD) or None for all
            
        Returns:
            Dict: Options chain data with calls and puts
        """
        return self.options_fetcher.get_options_chain(ticker, expiration_date)
    
    def get_option_quote(self, ticker, strike, expiration, option_type):
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
        return self.options_fetcher.get_option_quote(ticker, strike, expiration, option_type)
    
    def get_available_expirations(self, ticker):
        """
        Get available expiration dates for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            List[str]: Available expiration dates
        """
        return self.options_fetcher.get_available_expirations(ticker)
    
    def get_strike_range(self, ticker, expiration=None, moneyness_range=(0.8, 1.2)):
        """
        Get available strike prices within a moneyness range.
        
        Args:
            ticker (str): Stock ticker symbol
            expiration (str): Expiration date
            moneyness_range (Tuple): (min_moneyness, max_moneyness) relative to current price
            
        Returns:
            List[float]: Available strike prices
        """
        return self.options_fetcher.get_strike_range(ticker, expiration, moneyness_range)
    
    def validate_ticker_has_options(self, ticker):
        """
        Check if a ticker has options data available.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            bool: True if options data is available
        """
        return self.options_fetcher.validate_ticker_has_options(ticker)
    
    def get_data_quality_info(self, ticker):
        """
        Get data quality information for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Dict: Data quality metrics
        """
        return self.options_fetcher.get_data_quality_info(ticker)
    
    def get_cache_stats(self):
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics
        """
        return self.options_fetcher.get_cache_stats()
    
    def clear_cache(self, cache_type=None):
        """
        Clear cache data.
        
        Args:
            cache_type (str): Specific cache to clear
        """
        self.options_fetcher.clear_cache(cache_type)
