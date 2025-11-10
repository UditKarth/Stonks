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

def display_news_sentiment(news_data):
    """Display news and sentiment analysis section."""
    st.header("📰 News & Sentiment Analysis")
    
    if not news_data or 'feed' not in news_data:
        st.warning("News and sentiment data not available.")
        return
    
    feed = news_data.get('feed', [])
    if not feed:
        st.info("No recent news articles found.")
        return
    
    # Calculate overall sentiment
    sentiment_scores = []
    for article in feed[:20]:  # Analyze first 20 articles
        ticker_sentiment = article.get('ticker_sentiment', [])
        if ticker_sentiment:
            for ts in ticker_sentiment:
                relevance_score = float(ts.get('relevance_score', 0))
                if relevance_score > 0.5:  # Only count relevant articles
                    sentiment_score = float(ts.get('ticker_sentiment_score', 0))
                    sentiment_scores.append(sentiment_score)
    
    if sentiment_scores:
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        overall_sentiment = "Bullish" if avg_sentiment > 0.15 else "Bearish" if avg_sentiment < -0.15 else "Neutral"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall Sentiment", overall_sentiment)
        with col2:
            st.metric("Average Sentiment Score", f"{avg_sentiment:.3f}")
        with col3:
            st.metric("Relevant Articles", len(sentiment_scores))
    
    # Display recent news articles
    st.subheader("Recent News Articles")
    
    for article in feed[:10]:  # Show top 10 articles
        with st.expander(f"📄 {article.get('title', 'No Title')[:80]}..."):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Source:** {article.get('source', 'Unknown')}")
                st.write(f"**Published:** {article.get('time_published', 'Unknown')}")
            with col2:
                # Get sentiment for this article
                ticker_sentiment = article.get('ticker_sentiment', [])
                if ticker_sentiment:
                    for ts in ticker_sentiment:
                        sentiment_label = ts.get('ticker_sentiment_label', 'Neutral')
                        sentiment_score = float(ts.get('ticker_sentiment_score', 0))
                        st.write(f"**Sentiment:** {sentiment_label} ({sentiment_score:.3f})")
            
            st.write(f"**Summary:** {article.get('summary', 'No summary available')}")
            if article.get('url'):
                st.markdown(f"[Read Full Article]({article['url']})")

def display_insider_transactions(insider_data):
    """Display insider transactions section."""
    st.header("👥 Insider Transactions")
    
    if not insider_data or 'transactions' not in insider_data:
        st.warning("Insider transaction data not available.")
        return
    
    transactions = insider_data.get('transactions', [])
    if not transactions:
        st.info("No recent insider transactions found.")
        return
    
    # Calculate buy/sell ratio
    buys = [t for t in transactions if t.get('transaction_type', '').upper() in ['BUY', 'PURCHASE']]
    sells = [t for t in transactions if t.get('transaction_type', '').upper() in ['SELL', 'SALE']]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(transactions))
    with col2:
        st.metric("Buys", len(buys))
    with col3:
        st.metric("Sells", len(sells))
    
    if buys or sells:
        buy_sell_ratio = len(buys) / len(sells) if sells else float('inf')
        st.metric("Buy/Sell Ratio", f"{buy_sell_ratio:.2f}" if buy_sell_ratio != float('inf') else "N/A")
    
    # Display transactions table
    st.subheader("Recent Insider Transactions")
    
    transaction_data = []
    for trans in transactions[:20]:  # Show last 20 transactions
        transaction_data.append({
            'Date': trans.get('transaction_date', 'N/A'),
            'Insider': trans.get('name', 'N/A'),
            'Title': trans.get('position', 'N/A'),
            'Type': trans.get('transaction_type', 'N/A'),
            'Shares': trans.get('shares', 'N/A'),
            'Price': format_currency(trans.get('price', 0)),
            'Value': format_currency(trans.get('value', 0))
        })
    
    if transaction_data:
        df = pd.DataFrame(transaction_data)
        st.dataframe(df, use_container_width=True)

def display_dividends(dividends_data):
    """Display dividend analysis section."""
    st.header("💰 Dividend Analysis")
    
    if not dividends_data or 'dividends' not in dividends_data:
        st.warning("Dividend data not available.")
        return
    
    dividends = dividends_data.get('dividends', [])
    if not dividends:
        st.info("No dividend history available.")
        return
    
    # Calculate dividend metrics
    if dividends:
        latest_dividend = dividends[0] if dividends else None
        dividend_amounts = [float(d.get('dividend', 0)) for d in dividends if d.get('dividend')]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if latest_dividend:
                st.metric("Latest Dividend", format_currency(latest_dividend.get('dividend', 0)))
                st.caption(f"Date: {latest_dividend.get('date', 'N/A')}")
        with col2:
            if dividend_amounts:
                avg_dividend = sum(dividend_amounts) / len(dividend_amounts)
                st.metric("Average Dividend", format_currency(avg_dividend))
        with col3:
            if dividend_amounts:
                st.metric("Total Dividends (Period)", len(dividends))
    
    # Display dividend history
    st.subheader("Dividend History")
    
    dividend_list = []
    for div in dividends[:20]:  # Show last 20 dividends
        dividend_list.append({
            'Date': div.get('date', 'N/A'),
            'Dividend': format_currency(div.get('dividend', 0))
        })
    
    if dividend_list:
        df = pd.DataFrame(dividend_list)
        st.dataframe(df, use_container_width=True)
        
        # Create dividend timeline chart
        if len(dividend_list) > 1:
            dividend_df = pd.DataFrame(dividend_list)
            dividend_df['Date'] = pd.to_datetime(dividend_df['Date'], errors='coerce')
            dividend_df = dividend_df.sort_values('Date')
            dividend_df['Dividend'] = dividend_df['Dividend'].str.replace('$', '').str.replace(',', '').astype(float, errors='ignore')
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dividend_df['Date'],
                y=dividend_df['Dividend'],
                mode='lines+markers',
                name='Dividend',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.update_layout(
                title="Dividend History Timeline",
                xaxis_title="Date",
                yaxis_title="Dividend Amount ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

def display_splits(splits_data):
    """Display stock split history section."""
    st.header("📊 Stock Split History")
    
    if not splits_data or 'splits' not in splits_data:
        st.warning("Stock split data not available.")
        return
    
    splits = splits_data.get('splits', [])
    if not splits:
        st.info("No stock split history available.")
        return
    
    # Display split history
    st.subheader("Split History")
    
    split_list = []
    for split in splits[:20]:  # Show last 20 splits
        split_list.append({
            'Date': split.get('date', 'N/A'),
            'Split Ratio': split.get('split', 'N/A')
        })
    
    if split_list:
        df = pd.DataFrame(split_list)
        st.dataframe(df, use_container_width=True)

def main():
    """Main function for fundamental analysis page."""
    st.set_page_config(
        page_title="Stock Due Diligence - Fundamental Analysis",
        page_icon="📊",
        layout="wide"
    )
    
    # Custom CSS for better styling - light text on dark backgrounds
    st.markdown("""
    <style>
        /* Main content area - use light text for dark backgrounds */
        .main .block-container {
            color: #fafafa;
        }
        /* Headings - light text */
        h1, h2, h3, h4, h5, h6 {
            color: #fafafa !important;
        }
        /* Paragraphs and text - light text */
        p, li, span {
            color: #fafafa !important;
        }
        /* Streamlit text elements */
        .stMarkdown, .stText {
            color: #fafafa !important;
        }
        /* Dataframes - ensure text is visible */
        .dataframe {
            color: #fafafa !important;
        }
        /* Ensure styled divs with dark backgrounds have light text */
        div[style*="background-color"] {
            color: #fafafa !important;
        }
        div[style*="background-color"] h3,
        div[style*="background-color"] p,
        div[style*="background-color"] li,
        div[style*="background-color"] strong {
            color: #fafafa !important;
        }
        /* Override for light backgrounds - use dark text */
        div[style*="background-color: #fff"],
        div[style*="background-color: #f0f2f6"],
        div[style*="background-color: #e8f5e9"],
        div[style*="background-color: #fff3cd"] {
            color: #262730 !important;
        }
        div[style*="background-color: #fff"] h3,
        div[style*="background-color: #fff"] p,
        div[style*="background-color: #f0f2f6"] h3,
        div[style*="background-color: #f0f2f6"] p,
        div[style*="background-color: #e8f5e9"] h3,
        div[style*="background-color: #e8f5e9"] p,
        div[style*="background-color: #fff3cd"] h3,
        div[style*="background-color: #fff3cd"] p {
            color: #262730 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 Stock Due Diligence - Fundamental Analysis")
    st.markdown("Comprehensive fundamental analysis for stock due diligence")
    
    # Sidebar for ticker input
    with st.sidebar:
        # Navigation section with radio buttons
        st.header("🧭 Navigation")
        
        # Page selection using radio buttons
        selected_page = st.radio(
            "Select Page:",
            ["📊 Options Analysis", "📈 Fundamental Analysis"],
            index=1,
            label_visibility="collapsed"
        )
        
        # Navigate based on selection
        if selected_page == "📊 Options Analysis":
            st.switch_page("app")
        
        # Visual indicator
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem; background-color: #1f77b4; border-radius: 0.5rem; color: white; margin-top: 0.5rem;">
            <strong>Current: Fundamental Analysis</strong>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
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
            
            st.success(f"✅ Successfully fetched fundamental data for {ticker}")
            
        except Exception as e:
            st.error(f"❌ Error fetching fundamental data for {ticker}: {str(e)}")
            st.stop()
    
    # Fetch Phase 2 data (News, Insider Transactions)
    news_data = None
    insider_data = None
    
    with st.spinner(f"Fetching market intelligence data for {ticker}..."):
        try:
            news_data = fundamental_fetcher.get_news_sentiment(ticker, limit=50)
            st.success("✅ News & sentiment data fetched")
        except Exception as e:
            st.warning(f"⚠️ Could not fetch news data: {str(e)}")
        
        try:
            insider_data = fundamental_fetcher.get_insider_transactions(ticker)
            st.success("✅ Insider transactions data fetched")
        except Exception as e:
            st.warning(f"⚠️ Could not fetch insider transactions: {str(e)}")
    
    # Display sections
    overview = fundamental_data.get('overview')
    income_statement = fundamental_data.get('income_statement')
    balance_sheet = fundamental_data.get('balance_sheet')
    cash_flow = fundamental_data.get('cash_flow')
    earnings = fundamental_data.get('earnings')
    earnings_estimates = fundamental_data.get('earnings_estimates')
    dividends = fundamental_data.get('dividends')
    splits = fundamental_data.get('splits')
    
    # Company Overview
    display_company_overview(overview)
    
    st.divider()
    
    # Financial Statements
    display_financial_statements(income_statement, balance_sheet, cash_flow)
    
    st.divider()
    
    # Earnings
    display_earnings(earnings, earnings_estimates)
    
    st.divider()
    
    # Phase 2: Market Intelligence & Sentiment
    if news_data:
        display_news_sentiment(news_data)
        st.divider()
    
    if insider_data:
        display_insider_transactions(insider_data)
        st.divider()
    
    # Corporate Actions
    if dividends:
        display_dividends(dividends)
        st.divider()
    
    if splits:
        display_splits(splits)
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

