"""
Report generator module for creating comprehensive stock analysis reports.
Supports multiple export formats including LLM-optimized formats.
"""
import json
from typing import Dict, Optional
from datetime import datetime
from data_aggregator import DataAggregator
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates comprehensive stock analysis reports in multiple formats."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.data_aggregator = DataAggregator()
    
    def generate_comprehensive_report(self, ticker: str) -> Dict:
        """
        Generate a comprehensive stock analysis report.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict: Comprehensive report data
        """
        logger.info(f"Generating comprehensive report for {ticker}")
        
        # Aggregate all data
        aggregated_data = self.data_aggregator.aggregate_stock_data(ticker)
        
        # Calculate financial metrics
        financial_metrics = self.data_aggregator.calculate_financial_metrics(aggregated_data)
        
        # Build comprehensive report
        report = {
            'metadata': aggregated_data.get('metadata', {}),
            'company_overview': aggregated_data.get('overview', {}),
            'financial_statements': aggregated_data.get('financial_statements', {}),
            'earnings': aggregated_data.get('earnings', {}),
            'market_data': aggregated_data.get('market_data', {}),
            'corporate_actions': aggregated_data.get('corporate_actions', {}),
            'financial_metrics': financial_metrics,
            'summary': self._generate_summary(aggregated_data, financial_metrics)
        }
        
        return report
    
    def export_to_json(self, report: Dict, filename: Optional[str] = None) -> str:
        """
        Export report to JSON format (LLM-optimized).
        
        Args:
            report: Report data dictionary
            filename: Optional filename (if None, auto-generates)
            
        Returns:
            str: JSON string
        """
        if filename is None:
            ticker = report.get('metadata', {}).get('ticker', 'UNKNOWN')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"stock_report_{ticker}_{timestamp}.json"
        
        json_str = json.dumps(report, indent=2, default=str)
        
        # Save to file
        with open(filename, 'w') as f:
            f.write(json_str)
        
        logger.info(f"Report exported to {filename}")
        return json_str
    
    def export_to_structured_text(self, report: Dict, filename: Optional[str] = None) -> str:
        """
        Export report to structured text format (LLM-optimized).
        
        Args:
            report: Report data dictionary
            filename: Optional filename (if None, auto-generates)
            
        Returns:
            str: Structured text string
        """
        ticker = report.get('metadata', {}).get('ticker', 'UNKNOWN')
        analysis_date = report.get('metadata', {}).get('analysis_date', datetime.now().isoformat())
        
        text_lines = []
        text_lines.append("=" * 80)
        text_lines.append("STOCK DUE DILIGENCE REPORT")
        text_lines.append("=" * 80)
        text_lines.append(f"Ticker: {ticker}")
        text_lines.append(f"Analysis Date: {analysis_date}")
        text_lines.append("")
        
        # Company Overview
        overview = report.get('company_overview', {})
        if overview:
            text_lines.append("=== COMPANY OVERVIEW ===")
            text_lines.append(f"Name: {overview.get('Name', 'N/A')}")
            text_lines.append(f"Sector: {overview.get('Sector', 'N/A')}")
            text_lines.append(f"Industry: {overview.get('Industry', 'N/A')}")
            text_lines.append(f"Description: {overview.get('Description', 'N/A')[:200]}...")
            text_lines.append("")
        
        # Financial Metrics
        metrics = report.get('financial_metrics', {})
        if metrics:
            text_lines.append("=== FINANCIAL HIGHLIGHTS ===")
            if metrics.get('revenue_ttm'):
                text_lines.append(f"Revenue (TTM): ${metrics['revenue_ttm']:,.0f}")
            if metrics.get('net_income_ttm'):
                text_lines.append(f"Net Income (TTM): ${metrics['net_income_ttm']:,.0f}")
            if metrics.get('free_cash_flow_ttm'):
                text_lines.append(f"Free Cash Flow (TTM): ${metrics['free_cash_flow_ttm']:,.0f}")
            if metrics.get('market_cap'):
                text_lines.append(f"Market Cap: ${metrics['market_cap']:,.0f}")
            if metrics.get('pe_ratio'):
                text_lines.append(f"P/E Ratio: {metrics['pe_ratio']:.2f}")
            if metrics.get('dividend_yield'):
                text_lines.append(f"Dividend Yield: {metrics['dividend_yield']:.2%}")
            text_lines.append("")
        
        # Earnings
        earnings = report.get('earnings', {})
        earnings_history = earnings.get('history', {})
        if earnings_history:
            text_lines.append("=== EARNINGS ANALYSIS ===")
            quarterly_earnings = earnings_history.get('quarterlyEarnings', [])
            if quarterly_earnings:
                latest = quarterly_earnings[0]
                text_lines.append(f"Last Quarter EPS: ${latest.get('reportedEPS', 'N/A')}")
                text_lines.append(f"Estimate: ${latest.get('estimatedEPS', 'N/A')}")
                surprise = latest.get('surprise', 'N/A')
                if surprise != 'N/A':
                    text_lines.append(f"Surprise: {surprise}")
            text_lines.append("")
        
        # Market Data
        market_data = report.get('market_data', {})
        if market_data:
            text_lines.append("=== MARKET DATA ===")
            if market_data.get('current_price'):
                text_lines.append(f"Current Price: ${market_data['current_price']:.2f}")
            if market_data.get('volatility'):
                text_lines.append(f"Historical Volatility: {market_data['volatility']:.2%}")
            text_lines.append("")
        
        # Summary
        summary = report.get('summary', {})
        if summary:
            text_lines.append("=== EXECUTIVE SUMMARY ===")
            if summary.get('key_metrics'):
                text_lines.append("Key Metrics:")
                for metric, value in summary['key_metrics'].items():
                    text_lines.append(f"  - {metric}: {value}")
            text_lines.append("")
        
        text_lines.append("=" * 80)
        
        text_str = "\n".join(text_lines)
        
        # Save to file
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"stock_report_{ticker}_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(text_str)
        
        logger.info(f"Structured text report exported to {filename}")
        return text_str
    
    def _generate_summary(self, aggregated_data: Dict, financial_metrics: Dict) -> Dict:
        """
        Generate executive summary from aggregated data and metrics.
        
        Args:
            aggregated_data: Aggregated stock data
            financial_metrics: Calculated financial metrics
            
        Returns:
            Dict: Summary dictionary
        """
        summary = {
            'key_metrics': {},
            'valuation_summary': None,
            'financial_health': None
        }
        
        # Extract key metrics
        if financial_metrics.get('market_cap'):
            summary['key_metrics']['Market Cap'] = f"${financial_metrics['market_cap']:,.0f}"
        if financial_metrics.get('pe_ratio'):
            summary['key_metrics']['P/E Ratio'] = f"{financial_metrics['pe_ratio']:.2f}"
        if financial_metrics.get('revenue_ttm'):
            summary['key_metrics']['Revenue (TTM)'] = f"${financial_metrics['revenue_ttm']:,.0f}"
        if financial_metrics.get('net_income_ttm'):
            summary['key_metrics']['Net Income (TTM)'] = f"${financial_metrics['net_income_ttm']:,.0f}"
        if financial_metrics.get('free_cash_flow_ttm'):
            summary['key_metrics']['Free Cash Flow (TTM)'] = f"${financial_metrics['free_cash_flow_ttm']:,.0f}"
        
        # Valuation summary
        pe_ratio = financial_metrics.get('pe_ratio')
        if pe_ratio:
            if pe_ratio < 15:
                summary['valuation_summary'] = "Undervalued (Low P/E)"
            elif pe_ratio < 25:
                summary['valuation_summary'] = "Fairly Valued"
            else:
                summary['valuation_summary'] = "Potentially Overvalued (High P/E)"
        
        # Financial health
        current_ratio = financial_metrics.get('current_ratio')
        debt_to_equity = financial_metrics.get('debt_to_equity')
        
        health_factors = []
        if current_ratio:
            if current_ratio > 2:
                health_factors.append("Strong liquidity")
            elif current_ratio > 1:
                health_factors.append("Adequate liquidity")
            else:
                health_factors.append("Weak liquidity")
        
        if debt_to_equity:
            if debt_to_equity < 0.5:
                health_factors.append("Low debt")
            elif debt_to_equity < 1:
                health_factors.append("Moderate debt")
            else:
                health_factors.append("High debt")
        
        if health_factors:
            summary['financial_health'] = ", ".join(health_factors)
        
        return summary

