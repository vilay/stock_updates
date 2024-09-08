import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

class Models:
    @staticmethod
    def train_slr(symbol, train_data, test_data):
        train_prev_close = train_data['close'].shift(1)
        train_daily_returns = (train_data['close'] - train_prev_close) / train_prev_close
        train_data['pred'] = train_daily_returns.shift(-1)
        train_data = train_data.dropna()

        X_train = train_data[['cmma_20']]
        y_train = train_data[['pred']]
        model = LinearRegression()
        model.fit(X_train, y_train)

        test_prev_close = test_data['close'].shift(1)
        test_daily_returns = (test_data['close'] - test_prev_close) / test_prev_close
        test_data['pred'] = test_daily_returns.shift(-1)
        test_data = test_data.dropna()

        X_test = test_data[['cmma_20']]
        y_test = test_data[['pred']]
        y_pred = model.predict(X_test)

        r2 = r2_score(y_test, np.squeeze(y_pred))
        print(symbol, f'R^2={r2}')

        return model, ['cmma_20']
