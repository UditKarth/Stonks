"""
Data aggregation module for combining data from multiple sources.
Creates unified data models for comprehensive stock analysis.
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from fundamental_data_fetcher import FundamentalDataFetcher
from data_fetcher import DataFetcher
import logging

logger = logging.getLogger(__name__)

class DataAggregator:
    """Aggregates data from multiple sources into unified data models."""
    
    def __init__(self):
        """Initialize the data aggregator."""
        self.fundamental_fetcher = FundamentalDataFetcher()
        self.market_fetcher = DataFetcher()
    
    def aggregate_stock_data(self, ticker: str) -> Dict:
        """
        Aggregate all available data for a stock ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Comprehensive aggregated data dictionary
        """
        logger.info(f"Aggregating all data for {ticker}")
        
        aggregated_data = {
            'metadata': {
                'ticker': ticker,
                'analysis_date': datetime.now().isoformat(),
                'data_sources': {
                    'alpha_vantage': True,
                    'yfinance': True
                }
            },
            'overview': None,
            'financial_statements': {
                'income_statement': None,
                'balance_sheet': None,
                'cash_flow': None
            },
            'earnings': {
                'history': None,
                'estimates': None
            },
            'market_data': {
                'current_price': None,
                'volatility': None,
                'shares_outstanding': None
            },
            'corporate_actions': {
                'dividends': None,
                'splits': None
            },
            'market_intelligence': {
                'news_sentiment': None,
                'insider_transactions': None
            }
        }
        
        # Fetch fundamental data
        try:
            fundamental_data = self.fundamental_fetcher.get_all_fundamental_data(ticker)
            aggregated_data['overview'] = fundamental_data.get('overview')
            aggregated_data['financial_statements']['income_statement'] = fundamental_data.get('income_statement')
            aggregated_data['financial_statements']['balance_sheet'] = fundamental_data.get('balance_sheet')
            aggregated_data['financial_statements']['cash_flow'] = fundamental_data.get('cash_flow')
            aggregated_data['earnings']['history'] = fundamental_data.get('earnings')
            aggregated_data['earnings']['estimates'] = fundamental_data.get('earnings_estimates')
            aggregated_data['corporate_actions']['dividends'] = fundamental_data.get('dividends')
            aggregated_data['corporate_actions']['splits'] = fundamental_data.get('splits')
            
            # Get shares outstanding
            shares_data = fundamental_data.get('shares_outstanding')
            if shares_data:
                aggregated_data['market_data']['shares_outstanding'] = shares_data
        except Exception as e:
            logger.warning(f"Error fetching fundamental data for {ticker}: {str(e)}")
        
        # Fetch market data
        try:
            current_price = self.market_fetcher.get_stock_quote(ticker)
            aggregated_data['market_data']['current_price'] = current_price
        except Exception as e:
            logger.warning(f"Error fetching stock quote for {ticker}: {str(e)}")
        
        try:
            volatility = self.market_fetcher.get_historical_volatility(ticker)
            aggregated_data['market_data']['volatility'] = volatility
        except Exception as e:
            logger.warning(f"Error fetching volatility for {ticker}: {str(e)}")
        
        # Fetch Phase 2: Market Intelligence data
        try:
            news_sentiment = self.fundamental_fetcher.get_news_sentiment(ticker, limit=50)
            aggregated_data['market_intelligence']['news_sentiment'] = news_sentiment
        except Exception as e:
            logger.warning(f"Error fetching news sentiment for {ticker}: {str(e)}")
        
        try:
            insider_transactions = self.fundamental_fetcher.get_insider_transactions(ticker)
            aggregated_data['market_intelligence']['insider_transactions'] = insider_transactions
        except Exception as e:
            logger.warning(f"Error fetching insider transactions for {ticker}: {str(e)}")
        
        return aggregated_data
    
    def calculate_financial_metrics(self, aggregated_data: Dict) -> Dict:
        """
        Calculate derived financial metrics from aggregated data.
        
        Args:
            aggregated_data: Aggregated stock data dictionary
            
        Returns:
            Dict: Calculated financial metrics
        """
        metrics = {}
        
        overview = aggregated_data.get('overview')
        income_statement = aggregated_data.get('financial_statements', {}).get('income_statement')
        balance_sheet = aggregated_data.get('financial_statements', {}).get('balance_sheet')
        cash_flow = aggregated_data.get('financial_statements', {}).get('cash_flow')
        current_price = aggregated_data.get('market_data', {}).get('current_price')
        
        # Extract key metrics from overview if available
        if overview:
            metrics['market_cap'] = self._safe_float(overview.get('MarketCapitalization'))
            metrics['enterprise_value'] = self._safe_float(overview.get('EnterpriseValue'))
            metrics['pe_ratio'] = self._safe_float(overview.get('PERatio'))
            metrics['peg_ratio'] = self._safe_float(overview.get('PEGRatio'))
            metrics['price_to_book'] = self._safe_float(overview.get('PriceToBookRatio'))
            metrics['ev_to_ebitda'] = self._safe_float(overview.get('EVToRevenue'))
            metrics['dividend_yield'] = self._safe_float(overview.get('DividendYield'))
            metrics['payout_ratio'] = self._safe_float(overview.get('PayoutRatio'))
            metrics['profit_margin'] = self._safe_float(overview.get('ProfitMargin'))
            metrics['operating_margin'] = self._safe_float(overview.get('OperatingMargin'))
            metrics['roe'] = self._safe_float(overview.get('ReturnOnEquityTTM'))
            metrics['roa'] = self._safe_float(overview.get('ReturnOnAssetsTTM'))
            metrics['beta'] = self._safe_float(overview.get('Beta'))
            metrics['52_week_high'] = self._safe_float(overview.get('52WeekHigh'))
            metrics['52_week_low'] = self._safe_float(overview.get('52WeekLow'))
        
        # Calculate additional metrics from financial statements
        if income_statement and income_statement.get('annualReports'):
            annual_reports = income_statement['annualReports']
            if annual_reports:
                latest = annual_reports[0]
                revenue = self._safe_float(latest.get('totalRevenue'))
                net_income = self._safe_float(latest.get('netIncome'))
                gross_profit = self._safe_float(latest.get('grossProfit'))
                operating_income = self._safe_float(latest.get('operatingIncome'))
                
                if revenue and revenue > 0:
                    metrics['revenue_ttm'] = revenue
                    if net_income:
                        metrics['net_income_ttm'] = net_income
                        metrics['net_margin'] = net_income / revenue
                    if gross_profit:
                        metrics['gross_profit_ttm'] = gross_profit
                        metrics['gross_margin'] = gross_profit / revenue
                    if operating_income:
                        metrics['operating_income_ttm'] = operating_income
                        metrics['operating_margin_calc'] = operating_income / revenue
        
        if balance_sheet and balance_sheet.get('annualReports'):
            annual_reports = balance_sheet['annualReports']
            if annual_reports:
                latest = annual_reports[0]
                total_assets = self._safe_float(latest.get('totalAssets'))
                total_liabilities = self._safe_float(latest.get('totalLiabilities'))
                total_equity = self._safe_float(latest.get('totalShareholderEquity'))
                current_assets = self._safe_float(latest.get('totalCurrentAssets'))
                current_liabilities = self._safe_float(latest.get('totalCurrentLiabilities'))
                
                if total_assets:
                    metrics['total_assets'] = total_assets
                if total_liabilities and total_equity:
                    metrics['total_liabilities'] = total_liabilities
                    metrics['total_equity'] = total_equity
                    metrics['debt_to_equity'] = total_liabilities / total_equity if total_equity > 0 else None
                if current_assets and current_liabilities:
                    metrics['current_ratio'] = current_assets / current_liabilities if current_liabilities > 0 else None
        
        if cash_flow and cash_flow.get('annualReports'):
            annual_reports = cash_flow['annualReports']
            if annual_reports:
                latest = annual_reports[0]
                operating_cash_flow = self._safe_float(latest.get('operatingCashflow'))
                capital_expenditures = self._safe_float(latest.get('capitalExpenditures'))
                
                if operating_cash_flow:
                    metrics['operating_cash_flow_ttm'] = operating_cash_flow
                    if capital_expenditures:
                        metrics['free_cash_flow_ttm'] = operating_cash_flow - capital_expenditures
                        if current_price and metrics.get('market_cap'):
                            fcf_yield = (metrics['free_cash_flow_ttm'] / metrics['market_cap']) * 100 if metrics['market_cap'] > 0 else None
                            metrics['fcf_yield'] = fcf_yield
        
        return metrics
    
    def _safe_float(self, value: Optional[str]) -> Optional[float]:
        """Safely convert string to float, handling None and invalid values."""
        if value is None or value == 'None' or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

