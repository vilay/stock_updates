from pybroker import Strategy, StrategyConfig, YFinance
import pybroker
import datetime
import numpy as np
import pandas as pd
from numba import njit
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Enable data source cache
pybroker.enable_data_source_cache('my_strategy')
# config = StrategyConfig(initial_cash=500_000)
yfinance = YFinance()

def get_data(symbol, exchange):
    # Fetch data from inception (start date) to the current date
    df = yfinance.query(
        symbols=[f"{symbol}.{exchange}"], 
        start_date='1900-01-01',  # A very early date to ensure you get all available data
        end_date=datetime.date.today().strftime('%Y-%m-%d'), 
        _timeframe='1d'  # Adjust timeframe if needed
    )
    return df

def cmma(bar_data, lookback):

    @njit  # Enable Numba JIT.
    def vec_cmma(values):
        # Initialize the result array.
        n = len(values)
        out = np.array([np.nan for _ in range(n)])

        # For all bars starting at lookback:
        for i in range(lookback, n):
            # Calculate the moving average for the lookback.
            ma = 0
            for j in range(i - lookback, i):
                ma += values[j]
            ma /= lookback
            # Subtract the moving average from value.
            out[i] = values[i] - ma
        return out

    # Calculate for close prices.
    return vec_cmma(bar_data.close)

cmma_20 = pybroker.indicator('cmma_20', cmma, lookback=20)

def train_slr(symbol, train_data, test_data):
    # Train
    # Previous day close prices.
    train_prev_close = train_data['close'].shift(1)
    # Calculate daily returns.
    train_daily_returns = (train_data['close'] - train_prev_close) / train_prev_close
    # Predict next day's return.
    train_data['pred'] = train_daily_returns.shift(-1)
    train_data = train_data.dropna()
    # Train the LinearRegession model to predict the next day's return
    # given the 20-day CMMA.
    X_train = train_data[['cmma_20']]
    y_train = train_data[['pred']]
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Test
    test_prev_close = test_data['close'].shift(1)
    test_daily_returns = (test_data['close'] - test_prev_close) / test_prev_close
    test_data['pred'] = test_daily_returns.shift(-1)
    test_data = test_data.dropna()
    X_test = test_data[['cmma_20']]
    y_test = test_data[['pred']]
    # Make predictions from test data.
    y_pred = model.predict(X_test)
    # Print goodness of fit.
    r2 = r2_score(y_test, np.squeeze(y_pred))
    print(symbol, f'R^2={r2}')

    # Return the trained model and columns to use as input data.
    return model, ['cmma_20']

model_slr = pybroker.model('slr', train_slr, indicators=[cmma_20])
config = StrategyConfig(bootstrap_sample_size=100)
strategy = Strategy(YFinance(), start_date='1900-01-01', end_date=datetime.date.today().strftime('%Y-%m-%d'), config=config)
strategy.add_execution(None, ['PGEL.NS'], models=model_slr)
strategy.backtest(train_size=0.5)


buy_sell_points = []  # List to store buy/sell points

def hold_long(ctx):
    if not ctx.long_pos():
        if ctx.preds('slr')[-1] > 0:
            ctx.buy_shares = 100
            buy_sell_points.append((ctx._curr_date, 'BUY', ctx.close[-1], 100))
    else:
        if ctx.preds('slr')[-1] < 0:
            ctx.sell_shares = 100
            buy_sell_points.append((ctx._curr_date, 'SELL', ctx.close[-1], 100))

strategy.clear_executions()
strategy.add_execution(hold_long, ['PGEL.NS'], models=model_slr)

result = strategy.walkforward(
    warmup=20,
    windows=3,
    train_size=0.5,
    lookahead=1,
    calc_bootstrap=True
)

print(result.metrics_df)
print(result.bootstrap.conf_intervals)
print(result.bootstrap.drawdown_conf)

# Print all buy and sell points
for point in buy_sell_points:
    print(f"Date: {point[0]}, Action: {point[1]}, Price: {point[2]}, Shares: {point[3]}")