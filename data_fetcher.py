"""
Data fetching module for Alpha Vantage API integration and yfinance options data.
"""
import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
import config
from options_data_fetcher import OptionsDataFetcher
from cache_manager import cache_manager

class DataFetcher:
    """Class to handle data fetching from Alpha Vantage API and yfinance options data."""
    
    def __init__(self):
        """Initialize the data fetcher with API key and options fetcher."""
        self.api_key = config.ALPHA_VANTAGE_KEY
        self.ts = TimeSeries(key=self.api_key, output_format='pandas')
        self.options_fetcher = OptionsDataFetcher()
        self.cache_manager = cache_manager
    
    def get_stock_quote(self, ticker):
        """
        Get current stock price for a given ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            float: Current stock price
        """
        # Check cache first
        cached_price = self.cache_manager.get_stock_quote(ticker)
        if cached_price is not None:
            return cached_price
        
        try:
            # Get real-time quote
            data, meta_data = self.ts.get_quote_endpoint(symbol=ticker)
            current_price = float(data['05. price'].iloc[0])
            
            # Cache the price
            self.cache_manager.set_stock_quote(ticker, current_price)
            
            return current_price
        except Exception as e:
            raise Exception(f"Error fetching stock quote for {ticker}: {str(e)}")
    
    def get_historical_volatility(self, ticker, period='1y'):
        """
        Calculate annualized historical volatility from historical data.
        
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
        
        try:
            # Map period to Alpha Vantage output size
            output_size_map = {
                '1y': 'full',
                '6mo': 'compact',
                '3mo': 'compact'
            }
            
            output_size = output_size_map.get(period, 'compact')
            
            # Get daily historical data
            data, meta_data = self.ts.get_daily_adjusted(
                symbol=ticker, 
                outputsize=output_size
            )
            
            # Calculate daily returns
            data['daily_return'] = data['5. adjusted close'].pct_change()
            
            # Calculate volatility (annualized)
            daily_volatility = data['daily_return'].std()
            annualized_volatility = daily_volatility * np.sqrt(252)  # 252 trading days per year
            
            # Cache the volatility
            self.cache_manager.set_volatility(ticker, annualized_volatility)
            
            return annualized_volatility
            
        except Exception as e:
            raise Exception(f"Error calculating volatility for {ticker}: {str(e)}")
    
    def get_historical_data(self, ticker, period='1y'):
        """
        Get historical stock data for additional analysis.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period for historical data
            
        Returns:
            pandas.DataFrame: Historical stock data
        """
        try:
            output_size_map = {
                '1y': 'full',
                '6mo': 'compact',
                '3mo': 'compact'
            }
            
            output_size = output_size_map.get(period, 'compact')
            
            data, meta_data = self.ts.get_daily_adjusted(
                symbol=ticker, 
                outputsize=output_size
            )
            
            return data
            
        except Exception as e:
            raise Exception(f"Error fetching historical data for {ticker}: {str(e)}")
    
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
