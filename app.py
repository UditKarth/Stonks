"""
Main Streamlit application for Options Strategy Analyzer.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Import our custom modules
import config
from data_fetcher import DataFetcher
from strategies import create_strategy
from core_models import time_to_expiration, implied_volatility
from plotting import plot_payoff_diagram, create_strategy_summary_table

# Page configuration
st.set_page_config(
    page_title="Options Strategy Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">📈 Options Strategy Analyzer</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'data_fetched' not in st.session_state:
        st.session_state.data_fetched = False
    if 'current_price' not in st.session_state:
        st.session_state.current_price = None
    if 'volatility' not in st.session_state:
        st.session_state.volatility = None
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("📊 Market Data")
        
        # Stock ticker input
        ticker = st.text_input(
            "Stock Ticker Symbol",
            value="AAPL",
            help="Enter the stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
        ).upper()
        
        # Fetch data button
        if st.button("📡 Fetch Market Data", type="primary"):
            with st.spinner("Fetching market data..."):
                try:
                    fetcher = DataFetcher()
                    
                    # Validate ticker
                    if not fetcher.validate_ticker(ticker):
                        st.error(f"❌ Invalid ticker symbol: {ticker}")
                        st.stop()
                    
                    # Fetch current price and volatility
                    current_price = fetcher.get_stock_quote(ticker)
                    volatility = fetcher.get_historical_volatility(ticker)
                    
                    st.session_state.data_fetched = True
                    st.session_state.current_price = current_price
                    st.session_state.volatility = volatility
                    st.session_state.ticker = ticker
                    
                    st.success(f"✅ Data fetched successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error fetching data: {str(e)}")
                    st.stop()
        
        # Display fetched data
        if st.session_state.data_fetched:
            st.markdown("### 📈 Market Data")
            st.metric("Current Price", f"${st.session_state.current_price:.2f}")
            st.metric("Historical Volatility", f"{st.session_state.volatility:.1%}")
            
            st.markdown("---")
        
        # Strategy selection
        st.header("🎯 Strategy Selection")
        
        strategy_options = [
            "Long Call",
            "Short Call", 
            "Long Put",
            "Short Put",
            "Bull Call Spread",
            "Bear Put Spread",
            "Iron Condor",
            "Long Straddle"
        ]
        
        selected_strategy = st.selectbox(
            "Choose Strategy",
            strategy_options,
            help="Select the options strategy to analyze"
        )
        
        # Risk-free rate
        st.header("💰 Market Parameters")
        risk_free_rate = st.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.1,
            help="Annual risk-free interest rate"
        ) / 100
    
    # Main content area
    if not st.session_state.data_fetched:
        st.markdown("""
        <div class="warning-box">
            <h3>🚀 Getting Started</h3>
            <p>1. Enter a stock ticker symbol in the sidebar</p>
            <p>2. Click "Fetch Market Data" to get current price and volatility</p>
            <p>3. Select your options strategy</p>
            <p>4. Enter option details below</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Strategy-specific inputs
    st.header(f"📋 {selected_strategy} Parameters")
    
    # Common inputs
    col1, col2 = st.columns(2)
    
    with col1:
        expiration_date = st.date_input(
            "Expiration Date",
            value=datetime.now() + timedelta(days=30),
            min_value=datetime.now(),
            help="Options expiration date"
        )
        
        quantity = st.number_input(
            "Number of Contracts",
            min_value=1,
            value=1,
            help="Number of option contracts"
        )
    
    with col2:
        # Calculate time to expiration
        T = time_to_expiration(expiration_date.strftime('%Y-%m-%d'))
        st.metric("Time to Expiration", f"{T:.3f} years")
        
        if T <= 0:
            st.error("⚠️ Expiration date must be in the future!")
            return
    
    # Strategy-specific inputs
    strategy_params = {}
    
    if selected_strategy in ["Long Call", "Short Call", "Long Put", "Short Put"]:
        # Single leg strategies
        col1, col2 = st.columns(2)
        
        with col1:
            strike = st.number_input(
                "Strike Price",
                min_value=0.01,
                value=st.session_state.current_price,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            premium = st.number_input(
                "Premium",
                min_value=0.01,
                value=1.0,
                step=0.01,
                format="%.2f"
            )
        
        strategy_params = {
            'strike': strike,
            'premium': premium,
            'expiration': expiration_date.strftime('%Y-%m-%d'),
            'quantity': quantity
        }
    
    elif selected_strategy == "Bull Call Spread":
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            long_strike = st.number_input(
                "Long Strike",
                min_value=0.01,
                value=st.session_state.current_price * 0.95,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            short_strike = st.number_input(
                "Short Strike",
                min_value=0.01,
                value=st.session_state.current_price * 1.05,
                step=0.01,
                format="%.2f"
            )
        
        with col3:
            long_premium = st.number_input(
                "Long Premium",
                min_value=0.01,
                value=2.0,
                step=0.01,
                format="%.2f"
            )
        
        with col4:
            short_premium = st.number_input(
                "Short Premium",
                min_value=0.01,
                value=1.0,
                step=0.01,
                format="%.2f"
            )
        
        strategy_params = {
            'long_strike': long_strike,
            'short_strike': short_strike,
            'long_premium': long_premium,
            'short_premium': short_premium,
            'expiration': expiration_date.strftime('%Y-%m-%d'),
            'quantity': quantity
        }
    
    elif selected_strategy == "Bear Put Spread":
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            long_strike = st.number_input(
                "Long Strike",
                min_value=0.01,
                value=st.session_state.current_price * 1.05,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            short_strike = st.number_input(
                "Short Strike",
                min_value=0.01,
                value=st.session_state.current_price * 0.95,
                step=0.01,
                format="%.2f"
            )
        
        with col3:
            long_premium = st.number_input(
                "Long Premium",
                min_value=0.01,
                value=2.0,
                step=0.01,
                format="%.2f"
            )
        
        with col4:
            short_premium = st.number_input(
                "Short Premium",
                min_value=0.01,
                value=1.0,
                step=0.01,
                format="%.2f"
            )
        
        strategy_params = {
            'long_strike': long_strike,
            'short_strike': short_strike,
            'long_premium': long_premium,
            'short_premium': short_premium,
            'expiration': expiration_date.strftime('%Y-%m-%d'),
            'quantity': quantity
        }
    
    elif selected_strategy == "Iron Condor":
        st.subheader("Iron Condor Legs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Put Spread**")
            put_short_strike = st.number_input(
                "Put Short Strike",
                min_value=0.01,
                value=st.session_state.current_price * 0.90,
                step=0.01,
                format="%.2f"
            )
            put_long_strike = st.number_input(
                "Put Long Strike",
                min_value=0.01,
                value=st.session_state.current_price * 0.85,
                step=0.01,
                format="%.2f"
            )
            put_short_premium = st.number_input(
                "Put Short Premium",
                min_value=0.01,
                value=1.5,
                step=0.01,
                format="%.2f"
            )
            put_long_premium = st.number_input(
                "Put Long Premium",
                min_value=0.01,
                value=0.5,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            st.markdown("**Call Spread**")
            call_short_strike = st.number_input(
                "Call Short Strike",
                min_value=0.01,
                value=st.session_state.current_price * 1.10,
                step=0.01,
                format="%.2f"
            )
            call_long_strike = st.number_input(
                "Call Long Strike",
                min_value=0.01,
                value=st.session_state.current_price * 1.15,
                step=0.01,
                format="%.2f"
            )
            call_short_premium = st.number_input(
                "Call Short Premium",
                min_value=0.01,
                value=1.5,
                step=0.01,
                format="%.2f"
            )
            call_long_premium = st.number_input(
                "Call Long Premium",
                min_value=0.01,
                value=0.5,
                step=0.01,
                format="%.2f"
            )
        
        strategy_params = {
            'put_short_strike': put_short_strike,
            'put_long_strike': put_long_strike,
            'call_short_strike': call_short_strike,
            'call_long_strike': call_long_strike,
            'put_short_premium': put_short_premium,
            'put_long_premium': put_long_premium,
            'call_short_premium': call_short_premium,
            'call_long_premium': call_long_premium,
            'expiration': expiration_date.strftime('%Y-%m-%d'),
            'quantity': quantity
        }
    
    elif selected_strategy == "Long Straddle":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strike = st.number_input(
                "Strike Price",
                min_value=0.01,
                value=st.session_state.current_price,
                step=0.01,
                format="%.2f"
            )
        
        with col2:
            call_premium = st.number_input(
                "Call Premium",
                min_value=0.01,
                value=2.0,
                step=0.01,
                format="%.2f"
            )
        
        with col3:
            put_premium = st.number_input(
                "Put Premium",
                min_value=0.01,
                value=2.0,
                step=0.01,
                format="%.2f"
            )
        
        strategy_params = {
            'strike': strike,
            'call_premium': call_premium,
            'put_premium': put_premium,
            'expiration': expiration_date.strftime('%Y-%m-%d'),
            'quantity': quantity
        }
    
    # Analyze button
    if st.button("🔍 Analyze Strategy", type="primary"):
        try:
            # Create strategy object
            strategy = create_strategy(selected_strategy, **strategy_params)
            
            # Calculate Greeks
            greeks = strategy.calculate_greeks(
                st.session_state.current_price,
                T,
                risk_free_rate,
                st.session_state.volatility
            )
            
            # Display results
            st.header("📊 Analysis Results")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Max Profit",
                    f"${strategy.max_profit():.2f}" if strategy.max_profit() != float('inf') else "Unlimited"
                )
            
            with col2:
                st.metric(
                    "Max Loss",
                    f"${strategy.max_loss():.2f}" if strategy.max_loss() != float('inf') else "Unlimited"
                )
            
            with col3:
                be_points = strategy.break_even_points()
                st.metric("Break-Even", f"${', $'.join([f'{be:.2f}' for be in be_points])}")
            
            with col4:
                st.metric("Net Premium", f"${strategy.total_premium():.2f}")
            
            # Greeks
            st.subheader("📈 Greeks")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Delta", f"{greeks['delta']:.4f}")
            with col2:
                st.metric("Gamma", f"{greeks['gamma']:.4f}")
            with col3:
                st.metric("Theta", f"{greeks['theta']:.4f}")
            with col4:
                st.metric("Vega", f"{greeks['vega']:.4f}")
            with col5:
                st.metric("Rho", f"{greeks['rho']:.4f}")
            
            # Payoff diagram
            st.subheader("📈 Payoff Diagram")
            
            # Determine price range for the plot
            strikes = [leg.strike for leg in strategy.legs]
            min_strike = min(strikes)
            max_strike = max(strikes)
            padding = (max_strike - min_strike) * 0.5
            price_range = (max(0, min_strike - padding), max_strike + padding)
            
            # Create and display payoff diagram
            fig = plot_payoff_diagram(
                strategy,
                price_range=price_range,
                current_price=st.session_state.current_price
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Strategy summary table
            st.subheader("📋 Strategy Summary")
            summary_fig = create_strategy_summary_table(
                strategy,
                st.session_state.current_price,
                greeks
            )
            st.plotly_chart(summary_fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error analyzing strategy: {str(e)}")
            st.error("Please check your input parameters and try again.")

if __name__ == "__main__":
    main()
