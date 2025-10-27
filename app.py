"""
Main Streamlit application for Options Strategy Analyzer.
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import our custom modules
import config
from data_fetcher import DataFetcher
from strategies import create_strategy
from core_models import (
    time_to_expiration, implied_volatility, 
    calculate_option_price_advanced, compare_pricing_models,
    get_model_recommendations, calculate_strategy_price_advanced
)
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

def get_options_data_for_strategy(fetcher, ticker, strategy_type, expiration_date):
    """
    Get options data for a specific strategy.
    
    Args:
        fetcher: DataFetcher instance
        ticker: Stock ticker
        strategy_type: Type of strategy
        expiration_date: Expiration date
        
    Returns:
        Dict: Options data for the strategy
    """
    try:
        # Get options chain
        options_chain = fetcher.get_options_chain(ticker, expiration_date.strftime('%Y-%m-%d'))
        
        # Get available strikes
        available_strikes = fetcher.get_strike_range(ticker, expiration_date.strftime('%Y-%m-%d'))
        
        # Get current price for moneyness calculations
        current_price = st.session_state.current_price
        
        # Filter strikes around current price (within 20% range)
        relevant_strikes = [s for s in available_strikes if 0.8 * current_price <= s <= 1.2 * current_price]
        
        # Get option quotes for relevant strikes
        option_quotes = {}
        
        for strike in relevant_strikes[:10]:  # Limit to 10 strikes for performance
            try:
                call_quote = fetcher.get_option_quote(ticker, strike, expiration_date.strftime('%Y-%m-%d'), 'call')
                put_quote = fetcher.get_option_quote(ticker, strike, expiration_date.strftime('%Y-%m-%d'), 'put')
                
                option_quotes[strike] = {
                    'call': call_quote,
                    'put': put_quote
                }
            except:
                continue
        
        return {
            'options_chain': options_chain,
            'available_strikes': relevant_strikes,
            'option_quotes': option_quotes,
            'current_price': current_price
        }
        
    except Exception as e:
        st.error(f"Error fetching options data: {str(e)}")
        return None

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
                    
                    # Check if ticker has options data
                    has_options = fetcher.validate_ticker_has_options(ticker)
                    
                    st.session_state.data_fetched = True
                    st.session_state.current_price = current_price
                    st.session_state.volatility = volatility
                    st.session_state.ticker = ticker
                    st.session_state.has_options = has_options
                    
                    if has_options:
                        st.success(f"✅ Data fetched successfully! Options data available.")
                    else:
                        st.warning(f"⚠️ Data fetched successfully, but no options data available for {ticker}. Manual input required.")
                    
                except Exception as e:
                    st.error(f"❌ Error fetching data: {str(e)}")
                    st.stop()
        
        # Display fetched data
        if st.session_state.data_fetched:
            st.markdown("### 📈 Market Data")
            st.metric("Current Price", f"${st.session_state.current_price:.2f}")
            st.metric("Historical Volatility", f"{st.session_state.volatility:.1%}")
            
            # Display options data availability
            if st.session_state.has_options:
                st.markdown("### 📊 Options Data")
                st.success("✅ Real-time options data available")
                
                # Cache stats
                cache_stats = fetcher.get_cache_stats()
                st.caption(f"Cache: {cache_stats['total_cached_items']} items")
                
                # Clear cache button
                if st.button("🗑️ Clear Cache"):
                    fetcher.clear_cache()
                    st.success("Cache cleared!")
                    st.rerun()
            else:
                st.markdown("### 📊 Options Data")
                st.warning("⚠️ Manual input required")
            
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
        
        # Pricing model selection
        st.header("🧮 Pricing Model")
        pricing_model = st.selectbox(
            "Select Pricing Model",
            [
                "Black-Scholes",
                "Binomial Tree (American)",
                "Monte Carlo",
                "Heston Model",
                "Jump Diffusion",
                "Model Comparison"
            ],
            help="Choose the pricing model for options analysis"
        )
        
        # Advanced model parameters
        if pricing_model == "Heston Model":
            st.subheader("Heston Parameters")
            col1, col2 = st.columns(2)
            
            with col1:
                kappa = st.number_input("Mean Reversion Speed (κ)", value=2.0, step=0.1)
                theta = st.number_input("Long-term Volatility (θ)", value=0.04, step=0.01)
                sigma_v = st.number_input("Vol of Vol (σᵥ)", value=0.3, step=0.01)
            
            with col2:
                rho = st.number_input("Correlation (ρ)", value=-0.7, step=0.1, min_value=-1.0, max_value=1.0)
                v0 = st.number_input("Initial Volatility (v₀)", value=0.04, step=0.01)
        
        elif pricing_model == "Jump Diffusion":
            st.subheader("Jump Diffusion Parameters")
            col1, col2 = st.columns(2)
            
            with col1:
                lambda_jump = st.number_input("Jump Intensity (λ)", value=0.1, step=0.01)
                mu_jump = st.number_input("Mean Jump Size (μ)", value=-0.1, step=0.01)
            
            with col2:
                sigma_jump = st.number_input("Jump Volatility (σ)", value=0.1, step=0.01)
        
        elif pricing_model == "Binomial Tree (American)":
            st.subheader("Binomial Tree Parameters")
            n_steps = st.number_input("Number of Steps", value=100, min_value=50, max_value=500)
            american = st.checkbox("American Exercise", value=True)
        
        elif pricing_model == "Monte Carlo":
            st.subheader("Monte Carlo Parameters")
            col1, col2 = st.columns(2)
            
            with col1:
                n_simulations = st.number_input("Simulations", value=10000, min_value=1000, max_value=50000)
                n_steps = st.number_input("Time Steps", value=100, min_value=50, max_value=500)
            
            with col2:
                barrier_option = st.checkbox("Barrier Option")
                if barrier_option:
                    barrier = st.number_input("Barrier Level", value=100.0)
                    barrier_type = st.selectbox("Barrier Type", 
                                              ["down_and_out", "up_and_out", "down_and_in", "up_and_in"])
        
        # Data input mode selection
        if st.session_state.data_fetched and st.session_state.has_options:
            st.header("📊 Data Input Mode")
            data_mode = st.radio(
                "Choose data source:",
                ["Real-time Options Data", "Manual Input"],
                help="Select whether to use real-time options data or manual input"
            )
            st.session_state.data_mode = data_mode
        else:
            st.session_state.data_mode = "Manual Input"
    
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
        if st.session_state.data_mode == "Real-time Options Data" and st.session_state.has_options:
            # Use real options data
            with st.spinner("Fetching options data..."):
                fetcher = DataFetcher()
                options_data = get_options_data_for_strategy(fetcher, st.session_state.ticker, selected_strategy, expiration_date)
            
            if options_data:
                st.subheader("📊 Real-time Options Data")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Strike price selector
                    available_strikes = options_data['available_strikes']
                    if available_strikes:
                        strike_idx = st.selectbox(
                            "Select Strike Price",
                            range(len(available_strikes)),
                            format_func=lambda x: f"${available_strikes[x]:.2f}",
                            help="Choose from available strike prices"
                        )
                        strike = available_strikes[strike_idx]
                    else:
                        strike = st.number_input(
                            "Strike Price",
                            min_value=0.01,
                            value=st.session_state.current_price,
                            step=0.01,
                            format="%.2f"
                        )
                
                with col2:
                    # Premium from real data
                    option_type = 'call' if 'Call' in selected_strategy else 'put'
                    if strike in options_data['option_quotes']:
                        real_premium = options_data['option_quotes'][strike][option_type]['lastPrice']
                        premium = st.number_input(
                            "Premium",
                            min_value=0.01,
                            value=max(real_premium, 0.01),
                            step=0.01,
                            format="%.2f",
                            help=f"Real-time price: ${real_premium:.2f}"
                        )
                        
                        # Show additional data
                        quote_data = options_data['option_quotes'][strike][option_type]
                        st.caption(f"Bid: ${quote_data['bid']:.2f} | Ask: ${quote_data['ask']:.2f}")
                        st.caption(f"Volume: {quote_data['volume']} | OI: {quote_data['openInterest']}")
                    else:
                        premium = st.number_input(
                            "Premium",
                            min_value=0.01,
                            value=1.0,
                            step=0.01,
                            format="%.2f"
                        )
            else:
                st.error("Failed to fetch options data. Falling back to manual input.")
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
        else:
            # Manual input
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
    
    # Model recommendations
    if st.session_state.data_fetched:
        st.subheader("🎯 Model Recommendations")
        try:
            recommendations = get_model_recommendations(
                st.session_state.current_price, 
                strategy_params.get('strike', st.session_state.current_price),
                T, risk_free_rate, st.session_state.volatility, 
                'call' if 'Call' in selected_strategy else 'put'
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Recommended Model**: {recommendations['primary']}")
                st.caption(f"Reason: {recommendations['reason']}")
            
            with col2:
                if 'high_vol' in recommendations:
                    st.warning(f"**High Volatility**: {recommendations['high_vol']}")
                    st.caption(f"Reason: {recommendations['high_vol_reason']}")
                
                if 'extreme_moneyness' in recommendations:
                    st.warning(f"**Extreme Moneyness**: {recommendations['extreme_moneyness']}")
                    st.caption(f"Reason: {recommendations['extreme_moneyness_reason']}")
        
        except Exception as e:
            st.caption(f"Model recommendations unavailable: {str(e)}")
    
    # Data quality information
    if st.session_state.data_fetched and st.session_state.has_options:
        st.subheader("📊 Data Quality")
        fetcher = DataFetcher()
        quality_info = fetcher.get_data_quality_info(st.session_state.ticker)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Options", quality_info['total_options'])
        
        with col2:
            st.metric("Options with Quotes", quality_info['options_with_quotes'])
        
        with col3:
            st.metric("Quote Coverage", f"{quality_info['quote_coverage']:.1%}")
        
        st.caption(f"Data Source: {quality_info['data_source']} | Last Updated: {quality_info['last_updated']}")
    
    # Analyze button
    if st.button("🔍 Analyze Strategy", type="primary"):
        try:
            # Create strategy object
            strategy = create_strategy(selected_strategy, **strategy_params)
            
            # Prepare model parameters
            model_params = {}
            model_name = pricing_model.lower().replace(' ', '_').replace('(', '').replace(')', '')
            
            if pricing_model == "Heston Model":
                model_params = {
                    'kappa': kappa, 'theta': theta, 'sigma_v': sigma_v, 
                    'rho': rho, 'v0': v0
                }
                model_name = 'heston'
            elif pricing_model == "Jump Diffusion":
                model_params = {
                    'lambda_jump': lambda_jump, 'mu_jump': mu_jump, 
                    'sigma_jump': sigma_jump
                }
                model_name = 'jump_diffusion'
            elif pricing_model == "Binomial Tree (American)":
                model_params = {
                    'n_steps': n_steps, 'american': american
                }
                model_name = 'binomial_tree'
            elif pricing_model == "Monte Carlo":
                model_params = {
                    'n_simulations': n_simulations, 'n_steps': n_steps
                }
                if barrier_option:
                    model_params.update({
                        'barrier': barrier, 'barrier_type': barrier_type
                    })
                model_name = 'monte_carlo'
            elif pricing_model == "Black-Scholes":
                model_name = 'black_scholes'
            
            # Calculate strategy pricing
            if pricing_model == "Model Comparison":
                # Compare all models
                st.header("📊 Model Comparison Results")
                
                # Get comparison results for each leg
                comparison_results = {}
                for i, leg in enumerate(strategy.legs):
                    leg_comparison = compare_pricing_models(
                        st.session_state.current_price, leg.strike, T, 
                        risk_free_rate, st.session_state.volatility, 
                        leg.option_type, **model_params
                    )
                    comparison_results[f"Leg {i+1}: {leg.position} {leg.option_type} {leg.strike}"] = leg_comparison
                
                # Display comparison results
                for leg_name, results in comparison_results.items():
                    st.subheader(f"{leg_name}")
                    
                    # Create comparison table
                    comparison_data = []
                    for model_name, result in results.items():
                        if 'error' not in result:
                            comparison_data.append({
                                'Model': model_name,
                                'Price': f"${result['price']:.4f}",
                                'Delta': f"{result.get('delta', 'N/A')}",
                                'Gamma': f"{result.get('gamma', 'N/A')}",
                                'Theta': f"{result.get('theta', 'N/A')}",
                                'Vega': f"{result.get('vega', 'N/A')}",
                                'Rho': f"{result.get('rho', 'N/A')}"
                            })
                    
                    if comparison_data:
                        comparison_df = pd.DataFrame(comparison_data)
                        st.dataframe(comparison_df, use_container_width=True)
                    else:
                        st.error("No valid pricing results available")
                
                # Calculate Greeks using Black-Scholes for consistency
                greeks = strategy.calculate_greeks(
                    st.session_state.current_price, T, risk_free_rate, st.session_state.volatility
                )
                
            else:
                # Single model analysis
                st.header("📊 Analysis Results")
                
                # Calculate strategy pricing with selected model
                pricing_result = calculate_strategy_price_advanced(
                    strategy, st.session_state.current_price, T, 
                    risk_free_rate, st.session_state.volatility, 
                    model_name, **model_params
                )
                
                # Display pricing results
                st.subheader(f"🧮 {pricing_model} Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Model Price", f"${pricing_result['total_price']:.4f}")
                
                with col2:
                    st.metric("Model Used", pricing_result['model'].title())
                
                with col3:
                    st.metric("Strategy", pricing_result['strategy'])
                
                # Display leg-by-leg pricing
                if len(pricing_result['leg_prices']) > 1:
                    st.subheader("📋 Leg-by-Leg Pricing")
                    leg_data = []
                    for leg_info in pricing_result['leg_prices']:
                        leg_data.append({
                            'Leg': leg_info['leg'],
                            'Price': f"${leg_info['price']:.4f}",
                            'Contribution': f"${leg_info['total_contribution']:.4f}",
                            'Model': leg_info['model']
                        })
                    
                    leg_df = pd.DataFrame(leg_data)
                    st.dataframe(leg_df, use_container_width=True)
                
                # Calculate Greeks using Black-Scholes for consistency
                greeks = strategy.calculate_greeks(
                    st.session_state.current_price, T, risk_free_rate, st.session_state.volatility
                )
            
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
