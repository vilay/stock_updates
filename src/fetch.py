import yfinance as yf

# Specify the stock ticker symbol
stock_symbol = "RELIANCE.NS"  # NSE symbol

# Fetch the stock data
stock_data = yf.Ticker(stock_symbol)

# Get the real-time stock price
current_price = stock_data.history(period="1d")['Close'].iloc[0]

print(f"The current price of {stock_symbol} is: ₹{current_price:.2f}")
