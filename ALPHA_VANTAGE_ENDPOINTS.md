# Alpha Vantage API Endpoints Reference

This document outlines which Alpha Vantage API endpoints are available on the **free tier** versus those that require a **premium subscription**.

## 📊 Free Tier Endpoints

The following endpoints are available with a free Alpha Vantage API key:

### Time Series Data (Free)

#### ✅ TIME_SERIES_DAILY
- **Description**: Raw (as-traded) daily OHLCV time series covering 20+ years
- **Data**: Daily open, high, low, close, volume
- **Limitations**: End-of-day data (updated at market close)
- **Use Case**: Historical price data, volatility calculations
- **Example**: `function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo`

#### ✅ TIME_SERIES_WEEKLY
- **Description**: Weekly time series (last trading day of each week)
- **Data**: Weekly OHLCV data covering 20+ years
- **Limitations**: End-of-day data
- **Use Case**: Long-term trend analysis

#### ✅ TIME_SERIES_WEEKLY_ADJUSTED
- **Description**: Weekly adjusted time series with dividend/split adjustments
- **Data**: Weekly OHLCV + adjusted close + dividend data
- **Limitations**: End-of-day data
- **Use Case**: Adjusted historical analysis

#### ✅ TIME_SERIES_MONTHLY
- **Description**: Monthly time series (last trading day of each month)
- **Data**: Monthly OHLCV data covering 20+ years
- **Limitations**: End-of-day data
- **Use Case**: Very long-term analysis

#### ✅ TIME_SERIES_INTRADAY (End-of-Day)
- **Description**: Intraday OHLCV time series (1min, 5min, 15min, 30min, 60min intervals)
- **Data**: Current and 20+ years of historical intraday data
- **Limitations**: 
  - **Free**: End-of-day data only (updated at market close)
  - **Premium**: Realtime or 15-minute delayed data
- **Use Case**: Intraday analysis, historical intraday patterns
- **Note**: Realtime/15-minute delayed data requires premium subscription

### Options Data (Free)

#### ✅ HISTORICAL_OPTIONS
- **Description**: Full historical options chain for a specific symbol and date
- **Data**: Options chain with strikes, prices, Greeks (delta, gamma, theta, vega, rho), implied volatility
- **Coverage**: 15+ years of history (since 2008-01-01)
- **Limitations**: Historical data only (previous trading sessions)
- **Use Case**: Backtesting, historical options analysis
- **Example**: `function=HISTORICAL_OPTIONS&symbol=IBM&date=2017-11-15&apikey=demo`

### Market Intelligence (Free)

#### ✅ SYMBOL_SEARCH
- **Description**: Search for stock symbols and market information
- **Data**: Best-matching symbols with match scores
- **Use Case**: Auto-complete ticker search, symbol lookup

#### ✅ NEWS_SENTIMENT
- **Description**: Live and historical market news & sentiment data
- **Data**: News articles with sentiment scores from premier news outlets
- **Coverage**: Stocks, cryptocurrencies, forex, fiscal policy, M&A, IPOs, etc.
- **Use Case**: Sentiment analysis, news-driven trading strategies

#### ✅ EARNINGS_CALL_TRANSCRIPT
- **Description**: Earnings call transcripts with LLM-based sentiment signals
- **Coverage**: 15+ years of history (since 2010Q1)
- **Use Case**: Fundamental analysis, sentiment analysis

#### ✅ TOP_GAINERS_LOSERS
- **Description**: Top 20 gainers, losers, and most actively traded tickers (US Market)
- **Limitations**: 
  - **Free**: End-of-day data (updated at market close)
  - **Premium**: Realtime or 15-minute delayed data
- **Use Case**: Market overview, identifying trending stocks

#### ✅ INSIDER_TRANSACTIONS
- **Description**: Latest and historical insider transactions
- **Data**: Transactions by founders, executives, board members
- **Use Case**: Insider trading analysis, corporate governance

### Advanced Analytics (Free)

#### ✅ ANALYTICS_FIXED_WINDOW
- **Description**: Advanced analytics metrics over a fixed time window
- **Metrics**: Mean, median, variance, stddev, cumulative return, max drawdown, histogram, autocorrelation, covariance, correlation
- **Limitations**: Free API keys can specify up to 5 symbols per request
- **Use Case**: Statistical analysis, risk metrics, correlation analysis

#### ✅ ANALYTICS_SLIDING_WINDOW
- **Description**: Advanced analytics metrics over sliding time windows
- **Metrics**: Running mean, median, variance, stddev, cumulative return, covariance, correlation
- **Limitations**: 
  - Free API keys can specify up to 5 symbols per request
  - Free API keys can calculate 1 metric per request (premium: multiple metrics)
- **Use Case**: Moving averages, rolling volatility, time-series analysis

---

## 💎 Premium Endpoints

The following endpoints require a **premium subscription**:

### Time Series Data (Premium)

#### 🔒 TIME_SERIES_DAILY_ADJUSTED
- **Description**: Daily adjusted time series with split/dividend adjustments
- **Data**: Raw OHLCV + adjusted close values + historical split/dividend events
- **Why Premium**: Includes dividend and split adjustments automatically
- **Alternative**: Use `TIME_SERIES_DAILY` (free) and calculate adjustments manually, or use `TIME_SERIES_WEEKLY_ADJUSTED` (free)

#### 🔒 TIME_SERIES_INTRADAY (Realtime/15-minute delayed)
- **Description**: Realtime or 15-minute delayed intraday data
- **Data**: Live intraday OHLCV data during market hours
- **Why Premium**: Realtime market data is regulated by exchanges (FINRA, SEC)
- **Alternative**: Use end-of-day intraday data (free) or yfinance for realtime quotes

### Options Data (Premium)

#### 🔒 REALTIME_OPTIONS
- **Description**: Realtime US options data with full market coverage
- **Data**: Live options chain with strikes, prices, Greeks, implied volatility
- **Why Premium**: Realtime options data requires premium subscription
- **Alternative**: Use `HISTORICAL_OPTIONS` (free) for previous trading sessions, or yfinance for realtime options data

### Market Data (Premium)

#### 🔒 Realtime Bulk Quotes
- **Description**: Realtime quotes for multiple symbols in a single request
- **Why Premium**: Bulk realtime data requires premium subscription
- **Alternative**: Use individual quote endpoints or yfinance

#### 🔒 Realtime/15-minute delayed TOP_GAINERS_LOSERS
- **Description**: Live market movers data
- **Why Premium**: Realtime market data is regulated
- **Alternative**: Use end-of-day version (free)

---

## 🎯 Recommended Strategy for This Application

### Use Alpha Vantage Free Tier For:
1. **Historical Volatility Calculation**: Use `TIME_SERIES_DAILY` (free) instead of `TIME_SERIES_DAILY_ADJUSTED` (premium)
2. **Historical Options Data**: Use `HISTORICAL_OPTIONS` for backtesting and historical analysis
3. **Symbol Search**: Use `SYMBOL_SEARCH` for ticker lookup
4. **Market Intelligence**: Use `NEWS_SENTIMENT`, `EARNINGS_CALL_TRANSCRIPT`, `INSIDER_TRANSACTIONS`

### Use yfinance For:
1. **Realtime Stock Quotes**: yfinance provides free realtime quotes
2. **Realtime Options Data**: yfinance provides free realtime options chains
3. **Current Market Data**: When Alpha Vantage free tier only provides end-of-day data

### Fallback Strategy:
1. **Primary**: Try Alpha Vantage free tier endpoints first
2. **Secondary**: Fall back to yfinance if Alpha Vantage fails or rate-limited
3. **Error Handling**: Gracefully handle rate limits and premium endpoint errors

---

## 📝 Rate Limits

### Alpha Vantage Free Tier:
- **5 API calls per minute**
- **500 API calls per day**

### Best Practices:
- Implement caching to reduce API calls
- Use batch endpoints when available
- Respect rate limits with exponential backoff
- Cache frequently accessed data

---

## 🔗 Resources

- [Alpha Vantage API Documentation](https://www.alphavantage.co/documentation/)
- [Premium Plans](https://www.alphavantage.co/premium/)
- [Free API Key Registration](https://www.alphavantage.co/support/#api-key)

