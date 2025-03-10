#importing lib
import backtrader as bt
import yfinance as yf

#step2 calling class bt.strategy
class goldancross(bt.Strategy):
    def __init__(self):
        #calcutate ema
        self.ema20 = bt.indicators.ExponentialMovingAverage(self.data.close,period=20)
        self.ema100= bt.indicators.ExponentialMovingAverage(self.data.close,period=100)

        self.order = None
        self.last_signal = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.ema20[0]>self.ema100[0] and self.ema20[-1]<=self.ema100[-1]:
                self.order = self.buy()
                self.last_signal = 'BUY'
        else:
            if self.ema20[0]<self.ema100[0] and self.ema20[-1]>=self.ema100[-1]:
                self.order = self.sell()
                self.last_signal = 'SELL'

    def notify_order(self,order):
        if order.status in [order.completed]:
            if order.isbuy():
                print(f'buy executed at {order.executed.price:.2f}')
            elif order.issell():
                print(f'sell executed at {order.executed.price:.2f}')
            self.order = None


def run_backtest(symbol='tatamotors.ns',start_date='2023-01-01',end_date='2025-02-28',cash=100000):
    cerebro =bt.Cerebro()
    df = yf.download(symbol,start=start_date,end=end_date,multi_level_index=False)
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(goldancross)
    cerebro.broker.setcash(cash)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # Print starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
    
    # Run the backtest
    results = cerebro.run()
    strategy = results[0]
    
    # Print results
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
    print(f'Total Return: {strategy.analyzers.returns.get_analysis()["rtot"]*100:.2f}%')
    #print(f'Sharpe Ratio: {strategy.analyzers.sharpe.get_analysis()["sharperatio"]:.2f}')
    print(f'Max Drawdown: {strategy.analyzers.drawdown.get_analysis()["max"]["drawdown"]:.2f}%')
    
    # Plot the results
    cerebro.plot()

if __name__ == '__main__':
    run_backtest()