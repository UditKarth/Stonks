"""
Intelligent caching system for options data.
"""
import time
from typing import Any, Optional, Dict
from cachetools import TTLCache
import threading

class CacheManager:
    """Intelligent caching manager for options data with TTL support."""
    
    def __init__(self):
        """Initialize cache manager with different TTL settings."""
        # Cache for options chains (5 minutes TTL)
        self.options_chain_cache = TTLCache(maxsize=100, ttl=300)
        
        # Cache for individual option quotes (1 minute TTL)
        self.option_quote_cache = TTLCache(maxsize=500, ttl=60)
        
        # Cache for stock quotes (2 minutes TTL)
        self.stock_quote_cache = TTLCache(maxsize=200, ttl=120)
        
        # Cache for volatility data (10 minutes TTL)
        self.volatility_cache = TTLCache(maxsize=100, ttl=600)
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
    
    def get_options_chain(self, ticker: str, expiration_date: str = None) -> Optional[Dict]:
        """
        Get cached options chain data.
        
        Args:
            ticker (str): Stock ticker symbol
            expiration_date (str): Expiration date (optional)
            
        Returns:
            Dict or None: Cached options chain data
        """
        cache_key = f"{ticker}_{expiration_date}" if expiration_date else ticker
        
        with self._lock:
            return self.options_chain_cache.get(cache_key)
    
    def set_options_chain(self, ticker: str, data: Dict, expiration_date: str = None) -> None:
        """
        Cache options chain data.
        
        Args:
            ticker (str): Stock ticker symbol
            data (Dict): Options chain data
            expiration_date (str): Expiration date (optional)
        """
        cache_key = f"{ticker}_{expiration_date}" if expiration_date else ticker
        
        with self._lock:
            self.options_chain_cache[cache_key] = data
    
    def get_option_quote(self, ticker: str, strike: float, expiration: str, option_type: str) -> Optional[Dict]:
        """
        Get cached option quote data.
        
        Args:
            ticker (str): Stock ticker symbol
            strike (float): Strike price
            expiration (str): Expiration date
            option_type (str): 'call' or 'put'
            
        Returns:
            Dict or None: Cached option quote data
        """
        cache_key = f"{ticker}_{strike}_{expiration}_{option_type}"
        
        with self._lock:
            return self.option_quote_cache.get(cache_key)
    
    def set_option_quote(self, ticker: str, strike: float, expiration: str, option_type: str, data: Dict) -> None:
        """
        Cache option quote data.
        
        Args:
            ticker (str): Stock ticker symbol
            strike (float): Strike price
            expiration (str): Expiration date
            option_type (str): 'call' or 'put'
            data (Dict): Option quote data
        """
        cache_key = f"{ticker}_{strike}_{expiration}_{option_type}"
        
        with self._lock:
            self.option_quote_cache[cache_key] = data
    
    def get_stock_quote(self, ticker: str) -> Optional[float]:
        """
        Get cached stock quote.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            float or None: Cached stock price
        """
        with self._lock:
            return self.stock_quote_cache.get(ticker)
    
    def set_stock_quote(self, ticker: str, price: float) -> None:
        """
        Cache stock quote.
        
        Args:
            ticker (str): Stock ticker symbol
            price (float): Stock price
        """
        with self._lock:
            self.stock_quote_cache[ticker] = price
    
    def get_volatility(self, ticker: str) -> Optional[float]:
        """
        Get cached volatility data.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            float or None: Cached volatility
        """
        with self._lock:
            return self.volatility_cache.get(ticker)
    
    def set_volatility(self, ticker: str, volatility: float) -> None:
        """
        Cache volatility data.
        
        Args:
            ticker (str): Stock ticker symbol
            volatility (float): Volatility value
        """
        with self._lock:
            self.volatility_cache[ticker] = volatility
    
    def clear_cache(self, cache_type: str = None) -> None:
        """
        Clear cache data.
        
        Args:
            cache_type (str): Specific cache to clear ('options', 'quotes', 'volatility', 'all')
        """
        with self._lock:
            if cache_type is None or cache_type == 'all':
                self.options_chain_cache.clear()
                self.option_quote_cache.clear()
                self.stock_quote_cache.clear()
                self.volatility_cache.clear()
            elif cache_type == 'options':
                self.options_chain_cache.clear()
                self.option_quote_cache.clear()
            elif cache_type == 'quotes':
                self.stock_quote_cache.clear()
            elif cache_type == 'volatility':
                self.volatility_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics including hit rates and sizes
        """
        with self._lock:
            return {
                'options_chain_cache_size': len(self.options_chain_cache),
                'option_quote_cache_size': len(self.option_quote_cache),
                'stock_quote_cache_size': len(self.stock_quote_cache),
                'volatility_cache_size': len(self.volatility_cache),
                'total_cached_items': (
                    len(self.options_chain_cache) + 
                    len(self.option_quote_cache) + 
                    len(self.stock_quote_cache) + 
                    len(self.volatility_cache)
                )
            }
    
    def is_cache_valid(self, ticker: str, cache_type: str = 'options') -> bool:
        """
        Check if cache data is still valid.
        
        Args:
            ticker (str): Stock ticker symbol
            cache_type (str): Type of cache to check
            
        Returns:
            bool: True if cache is valid and not expired
        """
        with self._lock:
            if cache_type == 'options':
                return ticker in self.options_chain_cache
            elif cache_type == 'quotes':
                return ticker in self.stock_quote_cache
            elif cache_type == 'volatility':
                return ticker in self.volatility_cache
            return False

# Global cache manager instance
cache_manager = CacheManager()
