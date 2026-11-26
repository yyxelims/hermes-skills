"""
=== 回测框架学习 ===

两种回测方式:
  1. 向量化回测: 基于 pandas, 速度快, 适合简单策略快速验证
  2. 事件驱动回测 (Backtrader): 模拟真实交易流程, 支持复杂逻辑
"""

import numpy as np
import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 向量化回测
# ============================================================
print("=" * 60)
print("向量化回测 (Pandas 实现)")
print("=" * 60)

def vectorized_backtest(prices, signal, initial_capital=100000,
                         commission=0.001, slippage=0.001):
    """向量化回测引擎"""
    df = pd.DataFrame({'price': prices, 'signal': signal}).dropna()
    df['asset_return'] = df['price'].pct_change()
    df['position'] = df['signal'].shift(1).fillna(0)
    df['trade'] = df['position'].diff().abs()
    df['trade_cost'] = df['trade'] * (commission + slippage)
    df['strategy_return'] = df['position'] * df['asset_return'] - df['trade_cost']
    df['equity_curve'] = (1 + df['strategy_return']).cumprod() * initial_capital

    returns = df['strategy_return'].dropna()
    if len(returns) == 0:
        return None

    total_return = (df['equity_curve'].iloc[-1] / initial_capital) - 1
    annual_return = returns.mean() * 252
    annual_vol = returns.std() * np.sqrt(252)
    sharpe = (annual_return - 0.03) / annual_vol if annual_vol > 0 else 0

    cumulative = df['equity_curve'] / df['equity_curve'].iloc[0]
    running_max = np.maximum.accumulate(cumulative.values)
    drawdown = (cumulative.values - running_max) / running_max
    max_dd = drawdown.min()
    win_rate = (returns > 0).mean()

    return {
        'df': df,
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_vol': annual_vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
    }

# 双均线策略
print("\n双均线交叉策略 (AAPL)")
aapl = yf.download('AAPL', start='2023-01-01', end='2025-12-31', progress=False)
if isinstance(aapl.columns, pd.MultiIndex):
    aapl.columns = aapl.columns.droplevel(1)
prices = aapl['Close']

sma_short = prices.rolling(20).mean()
sma_long = prices.rolling(60).mean()
signal = (sma_short > sma_long).astype(int)

result = vectorized_backtest(prices, signal)
if result:
    print(f"  总收益率:     {result['total_return']:.2%}")
    print(f"  年化收益率:   {result['annual_return']:.2%}")
    print(f"  夏普比率:     {result['sharpe']:.2f}")
    print(f"  最大回撤:     {result['max_drawdown']:.2%}")
    print(f"  胜率:         {result['win_rate']:.2%}")
    bh = (prices.iloc[-1] / prices.iloc[0]) - 1
    print(f"  买入持有:     {bh:.2%}")

# 布林带均值回归
print("\n布林带均值回归策略 (GOOGL)")
googl = yf.download('GOOGL', start='2023-01-01', end='2025-12-31', progress=False)
if isinstance(googl.columns, pd.MultiIndex):
    googl.columns = googl.columns.droplevel(1)
prices_g = googl['Close']

sma = prices_g.rolling(20).mean()
std = prices_g.rolling(20).std()
upper, lower = sma + 2*std, sma - 2*std
signal_g = pd.Series(0, index=prices_g.index)
signal_g[prices_g < lower] = 1
signal_g[prices_g > upper] = 0
signal_g = signal_g.replace(0, np.nan).ffill().fillna(0)

result_g = vectorized_backtest(prices_g, signal_g)
if result_g:
    print(f"  总收益率:     {result_g['total_return']:.2%}")
    print(f"  夏普比率:     {result_g['sharpe']:.2f}")
    bh = (prices_g.iloc[-1] / prices_g.iloc[0]) - 1
    print(f"  买入持有:     {bh:.2%}")

# ============================================================
# Backtrader 事件驱动回测
# ============================================================
print("\n" + "=" * 60)
print("Backtrader 事件驱动回测")
print("=" * 60)

import backtrader as bt

class SmaCross(bt.Strategy):
    params = (('fast', 20), ('slow', 60))

    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.fast)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.slow)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        else:
            if self.crossover < 0:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None

cerebro = bt.Cerebro()
data = yf.download('AAPL', start='2023-01-01', end='2025-12-31', progress=False, auto_adjust=True)
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(1)
feed = bt.feeds.PandasData(dataname=data)
cerebro.adddata(feed)
cerebro.addstrategy(SmaCross)
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=0.001)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.03, annualize=True)
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

print(f"\n初始资金: ${cerebro.broker.getvalue():.2f}")
results = cerebro.run()
print(f"最终资金: ${cerebro.broker.getvalue():.2f}")

strat = results[0]
sharpe = strat.analyzers.sharpe.get_analysis()
dd = strat.analyzers.drawdown.get_analysis()
print(f"  夏普比率: {sharpe.get('sharperatio', 'N/A')}")
print(f"  最大回撤: {dd.max.drawdown:.2%}")

print("\n回测框架学习完成！")
