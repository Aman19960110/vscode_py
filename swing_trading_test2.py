import backtrader as bt
import yfinance as yf

class Strategy(bt.Strategy):
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('rsi_period', 2),
        ('rsi_threshold', 20),
    )

    def __init__(self):
        self.data15 = self.datas[0]  # Assign data feeds correctly
        self.data5 = self.datas[1]

        # Correct MACD initialization
        self.macd = bt.indicators.MACD(self.data15.close, 
                                       period_me1=self.params.fast_period, 
                                       period_me2=self.params.slow_period, 
                                       period_signal=self.params.signal_period)

        # Correct RSI initialization
        self.rsi = bt.indicators.RSI(self.data5.close, period=self.params.rsi_period)

        self.order = None

    def next(self):
        if self.order:
            return

        # FIX: Compute MACD Histogram manually
        macd_hist = self.macd.macd[0] - self.macd.signal[0]

        if macd_hist > (self.macd.macd[-1] - self.macd.signal[-1]) and \
           (self.macd.macd[-1] - self.macd.signal[-1]) > (self.macd.macd[-2] - self.macd.signal[-2]):
            
            if self.rsi[0] > self.params.rsi_threshold and self.data5.close[0] > self.data5.high[-1]:
                self.order = self.buy()
                self.stop_price = self.data5.low[-1]

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.order = None

    def stop(self):
        if self.position:
            self.close()

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(Strategy)

    # FIX: Set auto_adjust=False to avoid tuple issue
    data_5 = yf.download('EURUSD=X', start='2025-02-01', end='2025-02-28', interval='5m', auto_adjust=False,multi_level_index=False)

    # Print first few rows to debug
    print(data_5.head())

    # FIX: Correct PandasData usage
    data15 = bt.feeds.PandasData(dataname=data_5, timeframe=bt.TimeFrame.Minutes, compression=15)
    data5 = bt.feeds.PandasData(dataname=data_5, timeframe=bt.TimeFrame.Minutes, compression=5)

    cerebro.adddata(data15)
    cerebro.adddata(data5)

    cerebro.run()
    cerebro.plot()
