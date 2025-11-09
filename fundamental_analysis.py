"""
Fundamental Analysis page for Streamlit app.
Provides comprehensive stock due diligence analysis.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fundamental_data_fetcher import FundamentalDataFetcher
from data_aggregator import DataAggregator
from report_generator import ReportGenerator
from datetime import datetime
import json

def format_currency(value):
    """Format value as currency."""
    if value is None or value == 'None' or value == '':
        return 'N/A'
    try:
        return f"${float(value):,.0f}"
    except (ValueError, TypeError):
        return str(value)

def format_percentage(value):
    """Format value as percentage."""
    if value is None or value == 'None' or value == '':
        return 'N/A'
    try:
        return f"{float(value):.2%}"
    except (ValueError, TypeError):
        return str(value)

def format_number(value):
    """Format value as number."""
    if value is None or value == 'None' or value == '':
        return 'N/A'
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)

def display_company_overview(overview):
    """Display company overview section."""
    st.header("📊 Company Overview")
    
    if not overview:
        st.warning("Company overview data not available.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Company Information")
        st.write(f"**Name:** {overview.get('Name', 'N/A')}")
        st.write(f"**Sector:** {overview.get('Sector', 'N/A')}")
        st.write(f"**Industry:** {overview.get('Industry', 'N/A')}")
        st.write(f"**Exchange:** {overview.get('Exchange', 'N/A')}")
        st.write(f"**Currency:** {overview.get('Currency', 'N/A')}")
    
    with col2:
        st.subheader("Key Metrics")
        st.metric("Market Cap", format_currency(overview.get('MarketCapitalization')))
        st.metric("P/E Ratio", format_number(overview.get('PERatio')))
        st.metric("PEG Ratio", format_number(overview.get('PEGRatio')))
        st.metric("Price to Book", format_number(overview.get('PriceToBookRatio')))
        st.metric("EV/EBITDA", format_number(overview.get('EVToEBITDA')))
    
    with col3:
        st.subheader("Financial Ratios")
        st.metric("Dividend Yield", format_percentage(overview.get('DividendYield')))
        st.metric("Payout Ratio", format_percentage(overview.get('PayoutRatio')))
        st.metric("Profit Margin", format_percentage(overview.get('ProfitMargin')))
        st.metric("Operating Margin", format_percentage(overview.get('OperatingMarginTTM')))
        st.metric("ROE", format_percentage(overview.get('ReturnOnEquityTTM')))
    
    # Description
    if overview.get('Description'):
        st.subheader("Company Description")
        st.write(overview.get('Description'))
    
    # Additional metrics
    st.subheader("Additional Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Beta", format_number(overview.get('Beta')))
        st.metric("52 Week High", format_currency(overview.get('52WeekHigh')))
        st.metric("52 Week Low", format_currency(overview.get('52WeekLow')))
    
    with col2:
        st.metric("50 Day MA", format_currency(overview.get('50DayMovingAverage')))
        st.metric("200 Day MA", format_currency(overview.get('200DayMovingAverage')))
        st.metric("Shares Outstanding", format_currency(overview.get('SharesOutstanding')))
    
    with col3:
        st.metric("Dividend Per Share", format_currency(overview.get('DividendPerShare')))
        st.metric("Dividend Date", overview.get('DividendDate', 'N/A'))
        st.metric("Ex-Dividend Date", overview.get('ExDividendDate', 'N/A'))
    
    with col4:
        st.metric("EPS", format_number(overview.get('EPS')))
        st.metric("Revenue Per Share", format_number(overview.get('RevenuePerShareTTM')))
        st.metric("Book Value", format_currency(overview.get('BookValue')))

def display_financial_statements(income_statement, balance_sheet, cash_flow):
    """Display financial statements section."""
    st.header("📈 Financial Statements")
    
    tab1, tab2, tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
    
    with tab1:
        st.subheader("Income Statement")
        if income_statement and income_statement.get('annualReports'):
            annual_reports = income_statement['annualReports']
            if annual_reports:
                df = pd.DataFrame(annual_reports)
                # Select key columns
                key_columns = ['fiscalDateEnding', 'totalRevenue', 'grossProfit', 
                              'operatingIncome', 'netIncome', 'totalOperatingExpense',
                              'costOfRevenue', 'ebitda', 'eps']
                available_columns = [col for col in key_columns if col in df.columns]
                if available_columns:
                    display_df = df[available_columns].copy()
                    # Format currency columns
                    currency_cols = ['totalRevenue', 'grossProfit', 'operatingIncome', 
                                   'netIncome', 'totalOperatingExpense', 'costOfRevenue', 'ebitda']
                    for col in currency_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: format_currency(x) if x else 'N/A')
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Create revenue trend chart
                    if 'fiscalDateEnding' in df.columns and 'totalRevenue' in df.columns:
                        revenue_df = df[['fiscalDateEnding', 'totalRevenue']].copy()
                        revenue_df['fiscalDateEnding'] = pd.to_datetime(revenue_df['fiscalDateEnding'])
                        revenue_df = revenue_df.sort_values('fiscalDateEnding')
                        revenue_df['totalRevenue'] = pd.to_numeric(revenue_df['totalRevenue'], errors='coerce')
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=revenue_df['fiscalDateEnding'],
                            y=revenue_df['totalRevenue'],
                            mode='lines+markers',
                            name='Revenue',
                            line=dict(color='#1f77b4', width=2)
                        ))
                        fig.update_layout(
                            title="Revenue Trend (Annual)",
                            xaxis_title="Year",
                            yaxis_title="Revenue ($)",
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Income statement data not available.")
    
    with tab2:
        st.subheader("Balance Sheet")
        if balance_sheet and balance_sheet.get('annualReports'):
            annual_reports = balance_sheet['annualReports']
            if annual_reports:
                df = pd.DataFrame(annual_reports)
                key_columns = ['fiscalDateEnding', 'totalAssets', 'totalLiabilities',
                              'totalShareholderEquity', 'totalCurrentAssets', 
                              'totalCurrentLiabilities', 'cashAndCashEquivalentsAtCarryingValue']
                available_columns = [col for col in key_columns if col in df.columns]
                if available_columns:
                    display_df = df[available_columns].copy()
                    # Format currency columns
                    currency_cols = ['totalAssets', 'totalLiabilities', 'totalShareholderEquity',
                                    'totalCurrentAssets', 'totalCurrentLiabilities', 
                                    'cashAndCashEquivalentsAtCarryingValue']
                    for col in currency_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: format_currency(x) if x else 'N/A')
                    st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Balance sheet data not available.")
    
    with tab3:
        st.subheader("Cash Flow Statement")
        if cash_flow and cash_flow.get('annualReports'):
            annual_reports = cash_flow['annualReports']
            if annual_reports:
                df = pd.DataFrame(annual_reports)
                key_columns = ['fiscalDateEnding', 'operatingCashflow', 'capitalExpenditures',
                              'freeCashFlow', 'cashflowFromInvestment', 'cashflowFromFinancing']
                available_columns = [col for col in key_columns if col in df.columns]
                if available_columns:
                    display_df = df[available_columns].copy()
                    # Format currency columns
                    currency_cols = ['operatingCashflow', 'capitalExpenditures', 'freeCashFlow',
                                    'cashflowFromInvestment', 'cashflowFromFinancing']
                    for col in currency_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: format_currency(x) if x else 'N/A')
                    st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Cash flow data not available.")

def display_earnings(earnings, earnings_estimates):
    """Display earnings section."""
    st.header("💰 Earnings Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Earnings History")
        if earnings and earnings.get('quarterlyEarnings'):
            quarterly_earnings = earnings['quarterlyEarnings']
            if quarterly_earnings:
                df = pd.DataFrame(quarterly_earnings[:8])  # Show last 8 quarters
                if 'fiscalDateEnding' in df.columns and 'reportedEPS' in df.columns:
                    display_df = df[['fiscalDateEnding', 'reportedEPS', 'estimatedEPS', 'surprise', 'surprisePercentage']].copy()
                    display_df['reportedEPS'] = display_df['reportedEPS'].apply(lambda x: format_number(x) if x else 'N/A')
                    display_df['estimatedEPS'] = display_df['estimatedEPS'].apply(lambda x: format_number(x) if x else 'N/A')
                    display_df['surprisePercentage'] = display_df['surprisePercentage'].apply(lambda x: format_percentage(x) if x else 'N/A')
                    st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Earnings history not available.")
    
    with col2:
        st.subheader("Earnings Estimates")
        if earnings_estimates and earnings_estimates.get('quarterlyEstimates'):
            quarterly_estimates = earnings_estimates['quarterlyEstimates']
            if quarterly_estimates:
                df = pd.DataFrame(quarterly_estimates[:4])  # Show next 4 quarters
                if 'fiscalDateEnding' in df.columns:
                    display_df = df[['fiscalDateEnding', 'estimatedEPS', 'estimatedRevenue']].copy()
                    display_df['estimatedEPS'] = display_df['estimatedEPS'].apply(lambda x: format_number(x) if x else 'N/A')
                    display_df['estimatedRevenue'] = display_df['estimatedRevenue'].apply(lambda x: format_currency(x) if x else 'N/A')
                    st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Earnings estimates not available.")

def main():
    """Main function for fundamental analysis page."""
    st.set_page_config(
        page_title="Stock Due Diligence - Fundamental Analysis",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Stock Due Diligence - Fundamental Analysis")
    st.markdown("Comprehensive fundamental analysis for stock due diligence")
    
    # Sidebar for ticker input
    with st.sidebar:
        st.header("📈 Stock Selection")
        ticker = st.text_input(
            "Stock Ticker Symbol",
            value="AAPL",
            help="Enter the stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
        ).upper()
        
        if st.button("🔍 Analyze Stock", type="primary"):
            st.session_state.ticker = ticker
            st.session_state.analysis_ready = True
    
    # Check if analysis is ready
    if not st.session_state.get('analysis_ready', False):
        st.info("👈 Enter a stock ticker in the sidebar and click 'Analyze Stock' to begin.")
        return
    
    ticker = st.session_state.get('ticker', 'AAPL')
    
    # Initialize fetchers
    fundamental_fetcher = FundamentalDataFetcher()
    data_aggregator = DataAggregator()
    report_generator = ReportGenerator()
    
    # Fetch data with progress
    with st.spinner(f"Fetching fundamental data for {ticker}... This may take a minute due to API rate limits."):
        try:
            # Get all fundamental data
            fundamental_data = fundamental_fetcher.get_all_fundamental_data(ticker)
            
            # Aggregate data
            aggregated_data = data_aggregator.aggregate_stock_data(ticker)
            
            # Calculate metrics
            financial_metrics = data_aggregator.calculate_financial_metrics(aggregated_data)
            
            st.success(f"✅ Successfully fetched data for {ticker}")
            
        except Exception as e:
            st.error(f"❌ Error fetching data for {ticker}: {str(e)}")
            st.stop()
    
    # Display sections
    overview = fundamental_data.get('overview')
    income_statement = fundamental_data.get('income_statement')
    balance_sheet = fundamental_data.get('balance_sheet')
    cash_flow = fundamental_data.get('cash_flow')
    earnings = fundamental_data.get('earnings')
    earnings_estimates = fundamental_data.get('earnings_estimates')
    
    # Company Overview
    display_company_overview(overview)
    
    st.divider()
    
    # Financial Statements
    display_financial_statements(income_statement, balance_sheet, cash_flow)
    
    st.divider()
    
    # Earnings
    display_earnings(earnings, earnings_estimates)
    
    st.divider()
    
    # Export Section
    st.header("📥 Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export JSON Report", use_container_width=True):
            try:
                report = report_generator.generate_comprehensive_report(ticker)
                json_str = report_generator.export_to_json(report)
                st.success("✅ JSON report exported successfully!")
                st.download_button(
                    label="⬇️ Download JSON Report",
                    data=json_str,
                    file_name=f"stock_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
    
    with col2:
        if st.button("📝 Export Structured Text Report", use_container_width=True):
            try:
                report = report_generator.generate_comprehensive_report(ticker)
                text_str = report_generator.export_to_structured_text(report)
                st.success("✅ Structured text report exported successfully!")
                st.download_button(
                    label="⬇️ Download Text Report",
                    data=text_str,
                    file_name=f"stock_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")

if __name__ == "__main__":
    main()

