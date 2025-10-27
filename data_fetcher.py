"""
Data fetching module for Alpha Vantage API integration.
"""
import pandas as pd
import numpy as np
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
import config

class DataFetcher:
    """Class to handle data fetching from Alpha Vantage API."""
    
    def __init__(self):
        """Initialize the data fetcher with API key."""
        self.api_key = config.ALPHA_VANTAGE_KEY
        self.ts = TimeSeries(key=self.api_key, output_format='pandas')
        self.fd = FundamentalData(key=self.api_key, output_format='pandas')
    
    def get_stock_quote(self, ticker):
        """
        Get current stock price for a given ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            float: Current stock price
        """
        try:
            # Get real-time quote
            data, meta_data = self.ts.get_quote_endpoint(symbol=ticker)
            current_price = float(data['05. price'].iloc[0])
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
