"""
Fundamental data fetching module for Alpha Vantage API.
Handles company overview, financial statements, earnings, and other fundamental data.
"""
import requests
import pandas as pd
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from cache_manager import cache_manager
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundamentalDataFetcher:
    """Fetches fundamental data from Alpha Vantage API with intelligent caching."""
    
    def __init__(self):
        """Initialize the fundamental data fetcher."""
        self.api_key = config.ALPHA_VANTAGE_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.cache_manager = cache_manager
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds
        self.rate_limit_delay = 12  # seconds between API calls (5 calls/min = 12 sec/call)
        self.last_api_call_time = 0
    
    def _rate_limit_check(self):
        """Ensure we respect Alpha Vantage rate limits (5 calls/min for free tier)."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time
        
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_api_call_time = time.time()
    
    def _make_api_request(self, function: str, symbol: str, **kwargs) -> Dict:
        """
        Make API request to Alpha Vantage with rate limiting and error handling.
        
        Args:
            function: Alpha Vantage function name
            symbol: Stock ticker symbol
            **kwargs: Additional API parameters
            
        Returns:
            Dict: API response data
        """
        self._rate_limit_check()
        
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key
        }
        params.update(kwargs)
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    raise Exception(f"Alpha Vantage API Error: {data['Error Message']}")
                if 'Note' in data:
                    raise Exception(f"Alpha Vantage API Note: {data['Note']}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    logger.error(f"API request failed after {self.retry_attempts} attempts: {str(e)}")
                    raise Exception(f"Failed to fetch {function} for {symbol}: {str(e)}")
                else:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"API request failed, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
    
    def get_company_overview(self, ticker: str) -> Dict:
        """
        Get company overview including key metrics and financial ratios.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Company overview data
        """
        # Check cache first
        cache_key = f"overview_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached company overview for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching company overview for {ticker}")
            data = self._make_api_request('OVERVIEW', ticker)
            
            # Cache for 1 day (updated after earnings)
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched company overview for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching company overview for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch company overview for {ticker}: {str(e)}")
    
    def get_income_statement(self, ticker: str) -> Dict:
        """
        Get annual and quarterly income statements.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Income statement data with annual and quarterly reports
        """
        cache_key = f"income_statement_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached income statement for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching income statement for {ticker}")
            data = self._make_api_request('INCOME_STATEMENT', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched income statement for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch income statement for {ticker}: {str(e)}")
    
    def get_balance_sheet(self, ticker: str) -> Dict:
        """
        Get annual and quarterly balance sheets.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Balance sheet data with annual and quarterly reports
        """
        cache_key = f"balance_sheet_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached balance sheet for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching balance sheet for {ticker}")
            data = self._make_api_request('BALANCE_SHEET', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched balance sheet for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching balance sheet for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch balance sheet for {ticker}: {str(e)}")
    
    def get_cash_flow(self, ticker: str) -> Dict:
        """
        Get annual and quarterly cash flow statements.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Cash flow data with annual and quarterly reports
        """
        cache_key = f"cash_flow_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached cash flow for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching cash flow for {ticker}")
            data = self._make_api_request('CASH_FLOW', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched cash flow for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching cash flow for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch cash flow for {ticker}: {str(e)}")
    
    def get_earnings(self, ticker: str) -> Dict:
        """
        Get annual and quarterly earnings (EPS) with analyst estimates and surprises.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Earnings data with annual and quarterly reports
        """
        cache_key = f"earnings_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached earnings for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching earnings for {ticker}")
            data = self._make_api_request('EARNINGS', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched earnings for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching earnings for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch earnings for {ticker}: {str(e)}")
    
    def get_earnings_estimates(self, ticker: str) -> Dict:
        """
        Get annual and quarterly EPS and revenue estimates with analyst count and revisions.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Earnings estimates data
        """
        cache_key = f"earnings_estimates_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached earnings estimates for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching earnings estimates for {ticker}")
            data = self._make_api_request('EARNINGS_ESTIMATES', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched earnings estimates for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching earnings estimates for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch earnings estimates for {ticker}: {str(e)}")
    
    def get_shares_outstanding(self, ticker: str) -> Dict:
        """
        Get quarterly shares outstanding (diluted and basic).
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Shares outstanding data
        """
        cache_key = f"shares_outstanding_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached shares outstanding for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching shares outstanding for {ticker}")
            data = self._make_api_request('SHARES_OUTSTANDING', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched shares outstanding for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching shares outstanding for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch shares outstanding for {ticker}: {str(e)}")
    
    def get_dividends(self, ticker: str) -> Dict:
        """
        Get historical and future (declared) dividend distributions.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Dividend data
        """
        cache_key = f"dividends_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached dividends for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching dividends for {ticker}")
            data = self._make_api_request('DIVIDENDS', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched dividends for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching dividends for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch dividends for {ticker}: {str(e)}")
    
    def get_splits(self, ticker: str) -> Dict:
        """
        Get historical stock split events.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Stock split data
        """
        cache_key = f"splits_{ticker}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            logger.info(f"Using cached splits for {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching splits for {ticker}")
            data = self._make_api_request('SPLITS', ticker)
            
            # Cache for 1 day
            self.cache_manager.set(cache_key, data, ttl=86400)
            
            logger.info(f"Successfully fetched splits for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching splits for {ticker}: {str(e)}")
            raise Exception(f"Failed to fetch splits for {ticker}: {str(e)}")
    
    def get_all_fundamental_data(self, ticker: str) -> Dict:
        """
        Get all fundamental data for a ticker in one call (with caching).
        This method fetches all available fundamental data and returns a comprehensive dictionary.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Comprehensive fundamental data dictionary
        """
        logger.info(f"Fetching all fundamental data for {ticker}")
        
        fundamental_data = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'overview': None,
            'income_statement': None,
            'balance_sheet': None,
            'cash_flow': None,
            'earnings': None,
            'earnings_estimates': None,
            'shares_outstanding': None,
            'dividends': None,
            'splits': None
        }
        
        # Fetch all data (with error handling for each)
        try:
            fundamental_data['overview'] = self.get_company_overview(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch overview for {ticker}: {str(e)}")
        
        try:
            fundamental_data['income_statement'] = self.get_income_statement(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch income statement for {ticker}: {str(e)}")
        
        try:
            fundamental_data['balance_sheet'] = self.get_balance_sheet(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch balance sheet for {ticker}: {str(e)}")
        
        try:
            fundamental_data['cash_flow'] = self.get_cash_flow(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch cash flow for {ticker}: {str(e)}")
        
        try:
            fundamental_data['earnings'] = self.get_earnings(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch earnings for {ticker}: {str(e)}")
        
        try:
            fundamental_data['earnings_estimates'] = self.get_earnings_estimates(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch earnings estimates for {ticker}: {str(e)}")
        
        try:
            fundamental_data['shares_outstanding'] = self.get_shares_outstanding(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch shares outstanding for {ticker}: {str(e)}")
        
        try:
            fundamental_data['dividends'] = self.get_dividends(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch dividends for {ticker}: {str(e)}")
        
        try:
            fundamental_data['splits'] = self.get_splits(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch splits for {ticker}: {str(e)}")
        
        return fundamental_data

