import datetime
import pybroker
from pybroker import Strategy, StrategyConfig, YFinance
from indicators import Indicators
from models import Models

class MyStrategy:
    def __init__(self, symbol, exchange, initial_cash=500_000):
        self.symbol = symbol
        self.exchange = exchange
        self.data_source = YFinance()
        self.initial_cash = initial_cash
        self.strategy_config = StrategyConfig(bootstrap_sample_size=100)
        self.buy_sell_points = []

        pybroker.enable_data_source_cache('my_strategy')

    def get_data(self):
        df = self.data_source.query(
            symbols=[f"{self.symbol}.{self.exchange}"],
            start_date='1900-01-01',
            end_date=datetime.date.today().strftime('%Y-%m-%d'),
            _timeframe='1d'
        )
        return df

    def run_strategy(self):
        cmma_20 = pybroker.indicator('cmma_20', Indicators.cmma, lookback=20)
        model_slr = pybroker.model('slr', Models.train_slr, indicators=[cmma_20])

        strategy = Strategy(
            self.data_source,
            start_date='1900-01-01',
            end_date=datetime.date.today().strftime('%Y-%m-%d'),
            config=self.strategy_config
        )
        strategy.add_execution(self.hold_long, [f'{self.symbol}.{self.exchange}'], models=model_slr)
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
        self.print_buy_sell_points()

    def hold_long(self, ctx):
        if not ctx.long_pos():
            if ctx.preds('slr')[-1] > 0:
                ctx.buy_shares = 100
                self.buy_sell_points.append((ctx._curr_date, 'BUY', ctx.close[-1], 100))
        else:
            if ctx.preds('slr')[-1] < 0:
                ctx.sell_shares = 100
                self.buy_sell_points.append((ctx._curr_date, 'SELL', ctx.close[-1], 100))

    def print_buy_sell_points(self):
        for point in self.buy_sell_points:
            print(f"Date: {point[0]}, Action: {point[1]}, Price: {point[2]}, Shares: {point[3]}")

# Usage
if __name__ == "__main__":
    # my_strategy = MyStrategy(symbol='PGEL', exchange='NS')
    my_strategy = MyStrategy(symbol='CMSINFO', exchange='NS')
    my_strategy.run_strategy()
