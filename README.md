# 📈 Options Strategy Analyzer

A comprehensive Streamlit application for analyzing various options trading strategies using real-time market data from Alpha Vantage and advanced mathematical models.

## 🚀 Features

- **Real-time Market Data**: Fetch current stock prices and historical volatility from Alpha Vantage API
- **Black-Scholes Pricing**: European options pricing using the Black-Scholes model
- **Complete Greeks Analysis**: Delta, Gamma, Theta, Vega, and Rho calculations
- **Implied Volatility**: Calculate implied volatility from market prices
- **Multiple Strategies**: Support for 8 different options strategies
- **Interactive Visualizations**: Beautiful payoff diagrams with Plotly
- **Strategy Analysis**: Max profit/loss, break-even points, and risk metrics

## 📋 Supported Strategies

### Single Leg Strategies
- **Long Call**: Buy call options
- **Short Call**: Sell call options
- **Long Put**: Buy put options
- **Short Put**: Sell put options

### Spread Strategies
- **Bull Call Spread**: Long call + Short call (higher strike)
- **Bear Put Spread**: Long put + Short put (lower strike)

### Complex Strategies
- **Iron Condor**: Four-leg strategy with put and call spreads
- **Long Straddle**: Long call + Long put (same strike)

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Get Alpha Vantage API Key**:
   - Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - Sign up for a free API key
   - Copy your API key

4. **Configure Environment**:
   - Open the `.env` file
   - Replace `your_api_key_here` with your actual Alpha Vantage API key:
   ```
   ALPHA_VANTAGE_KEY=your_actual_api_key_here
   ```

## 🚀 Running the Application

1. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

## 📖 How to Use

### Step 1: Fetch Market Data
1. Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
2. Click "Fetch Market Data" to get current price and volatility
3. Verify the data is displayed correctly

### Step 2: Select Strategy
1. Choose your options strategy from the dropdown
2. Set the risk-free rate (default: 5%)

### Step 3: Enter Option Details
1. Set the expiration date
2. Enter strike prices and premiums for your strategy
3. Specify the number of contracts

### Step 4: Analyze
1. Click "Analyze Strategy" to run the analysis
2. Review the results:
   - Key metrics (max profit/loss, break-even points)
   - Greeks analysis
   - Interactive payoff diagram
   - Strategy summary table

## 📁 Project Structure

```
Stonks/
├── .env                    # Environment variables (API key)
├── requirements.txt        # Python dependencies
├── config.py              # Configuration module
├── data_fetcher.py        # Alpha Vantage API integration
├── core_models.py         # Black-Scholes pricing and Greeks
├── strategies.py          # Options strategy framework
├── plotting.py            # Visualization functions
├── app.py                 # Main Streamlit application
└── README.md              # This file
```

## 🔧 Technical Details

### Mathematical Models
- **Black-Scholes Model**: European options pricing
- **Greeks Calculations**: All five Greeks with proper formulas
- **Implied Volatility**: Newton's method with fallback to bisection
- **Historical Volatility**: Annualized from daily returns

### Data Sources
- **Alpha Vantage API**: Real-time stock quotes and historical data
- **Manual Input**: Option-specific data (strikes, premiums, expiration)

### Visualization
- **Plotly**: Interactive charts with hover information
- **Payoff Diagrams**: Clear visualization of profit/loss scenarios
- **Break-even Points**: Marked on charts for easy reference

## ⚠️ Important Notes

1. **API Limits**: Alpha Vantage free tier has rate limits (5 calls per minute)
2. **Data Accuracy**: Option data must be entered manually as Alpha Vantage doesn't provide option chains
3. **Model Assumptions**: Black-Scholes model assumes European options and constant volatility
4. **Risk Management**: This tool is for educational purposes - always consult financial professionals

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**:
   - Ensure your `.env` file contains a valid Alpha Vantage API key
   - Check that the key is not expired or rate-limited

2. **Invalid Ticker**:
   - Verify the ticker symbol exists and is correctly formatted
   - Some international tickers may not be supported

3. **Strategy Validation Errors**:
   - Check that strike prices are in the correct order for spreads
   - Ensure all required parameters are provided

4. **Mathematical Errors**:
   - Verify that time to expiration is positive
   - Check that volatility and interest rates are reasonable values

## 📚 Educational Resources

- [Options Trading Basics](https://www.investopedia.com/options/)
- [Black-Scholes Model](https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model)
- [Options Greeks](https://www.investopedia.com/trading/options-greeks/)
- [Alpha Vantage Documentation](https://www.alphavantage.co/documentation/)

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this application.

## 📄 License

This project is for educational purposes. Please ensure compliance with your local financial regulations when using this tool.

---

**Disclaimer**: This application is for educational and analytical purposes only. It is not intended as financial advice. Always consult with qualified financial professionals before making investment decisions.
