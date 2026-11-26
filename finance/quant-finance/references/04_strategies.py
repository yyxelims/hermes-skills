"""
=== 经典量化策略类型 ===

四大策略类型:
  1. 趋势跟踪 (Trend Following): 顺势而为
  2. 均值回归 (Mean Reversion): 逆向交易
  3. 因子策略 (Factor Investing): 多因子选股
  4. 机器学习策略 (ML-based): 用模型预测收益
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats as sp_stats
import warnings
warnings.filterwarnings('ignore')

# 向量化回测函数
def vectorized_backtest(prices, signal, initial_capital=100000, commission=0.001, slippage=0.001):
    df = pd.DataFrame({'price': prices, 'signal': signal}).dropna()
    df['asset_return'] = df['price'].pct_change()
    df['position'] = df['signal'].shift(1).fillna(0)
    df['trade'] = df['position'].diff().abs()
    df['trade_cost'] = df['trade'] * (commission + slippage)
    df['strategy_return'] = df['position'] * df['asset_return'] - df['trade_cost']
    df['equity_curve'] = (1 + df['strategy_return']).cumprod() * initial_capital
    returns = df['strategy_return'].dropna()
    if len(returns) < 2:
        return None
    total_return = (df['equity_curve'].iloc[-1] / initial_capital) - 1
    annual_return = returns.mean() * 252
    annual_vol = returns.std() * np.sqrt(252)
    sharpe = (annual_return - 0.03) / annual_vol if annual_vol > 0 else 0
    cumulative = df['equity_curve'] / df['equity_curve'].iloc[0]
    max_dd = (cumulative / cumulative.cummax() - 1).min()
    win_rate = (returns > 0).mean()
    return {'total_return': total_return, 'annual_return': annual_return,
            'sharpe': sharpe, 'max_drawdown': max_dd, 'win_rate': win_rate}

# 加载数据
print("=" * 60)
print("加载数据: AAPL + TSLA (2022-2025)")
print("=" * 60)
data = yf.download(['AAPL', 'TSLA'], start='2022-01-01', end='2025-12-31', progress=False)
close = data['Close']
aapl = close['AAPL'].dropna()
tsla = close['TSLA'].dropna()

# ============================================================
# 趋势跟踪
# ============================================================
print("\n" + "=" * 60)
print("1. 趋势跟踪")
print("=" * 60)

# 双均线
print("\n双均线 (20/50) - AAPL:")
sma_20 = aapl.rolling(20).mean()
sma_50 = aapl.rolling(50).mean()
signal_ma = (sma_20 > sma_50).astype(int)
r = vectorized_backtest(aapl, signal_ma)
bh = (aapl.iloc[-1] / aapl.iloc[0] - 1)
if r: print(f"  收益: {r['total_return']:.2%} | 夏普: {r['sharpe']:.2f} | 回撤: {r['max_drawdown']:.2%} | 基准: {bh:.2%}")

# 动量
print("\n动量 (60日) - AAPL:")
momentum = aapl.pct_change(60)
signal_mom = (momentum > 0).astype(int)
r = vectorized_backtest(aapl, signal_mom)
if r: print(f"  收益: {r['total_return']:.2%} | 夏普: {r['sharpe']:.2f} | 回撤: {r['max_drawdown']:.2%} | 基准: {bh:.2%}")

# Donchian 通道
print("\nDonchian通道 (20日) - AAPL:")
w = 20
high_n = aapl.rolling(w).max()
low_n = aapl.rolling(w).min()
signal_dc = pd.Series(0, index=aapl.index)
signal_dc[aapl > high_n.shift(1)] = 1
signal_dc[aapl < low_n.shift(1)] = 0
signal_dc = signal_dc.replace(0, np.nan).ffill().fillna(0)
r = vectorized_backtest(aapl, signal_dc)
if r: print(f"  收益: {r['total_return']:.2%} | 夏普: {r['sharpe']:.2f} | 回撤: {r['max_drawdown']:.2%} | 基准: {bh:.2%}")

# ============================================================
# 均值回归
# ============================================================
print("\n" + "=" * 60)
print("2. 均值回归")
print("=" * 60)

# 布林带
print("\n布林带 (20,2) - TSLA:")
sma = tsla.rolling(20).mean()
std = tsla.rolling(20).std()
upper, lower = sma + 2*std, sma - 2*std
signal_bb = pd.Series(np.nan, index=tsla.index)
signal_bb[tsla < lower] = 1
signal_bb[tsla > upper] = 0
signal_bb = signal_bb.ffill().fillna(0)
r = vectorized_backtest(tsla, signal_bb)
bh_tsla = (tsla.iloc[-1] / tsla.iloc[0] - 1)
if r: print(f"  收益: {r['total_return']:.2%} | 夏普: {r['sharpe']:.2f} | 回撤: {r['max_drawdown']:.2%} | 基准: {bh_tsla:.2%}")

# RSI
print("\nRSI (14, 30/70) - TSLA:")
def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

rsi = calc_rsi(tsla, 14)
signal_rsi = pd.Series(np.nan, index=tsla.index)
signal_rsi[rsi < 30] = 1
signal_rsi[rsi > 70] = 0
signal_rsi = signal_rsi.ffill().fillna(0)
r = vectorized_backtest(tsla, signal_rsi)
if r: print(f"  收益: {r['total_return']:.2%} | 夏普: {r['sharpe']:.2f} | 回撤: {r['max_drawdown']:.2%} | 基准: {bh_tsla:.2%}")

# ============================================================
# 因子策略
# ============================================================
print("\n" + "=" * 60)
print("3. 因子策略 (模拟)")
print("=" * 60)

np.random.seed(42)
n_stocks, n_days = 50, 252
dates = pd.date_range('2024-01-01', periods=n_days, freq='B')
stocks = [f'STOCK_{i:02d}' for i in range(n_stocks)]

value_factor = pd.DataFrame(np.random.randn(n_days, n_stocks), index=dates, columns=stocks)
momentum_factor = pd.DataFrame(np.random.randn(n_days, n_stocks), index=dates, columns=stocks)
quality_factor = pd.DataFrame(np.random.randn(n_days, n_stocks), index=dates, columns=stocks)
future_returns = pd.DataFrame(np.random.randn(n_days, n_stocks)*0.02, index=dates, columns=stocks)

# IC 分析
for name, factor in [('价值', value_factor), ('动量', momentum_factor), ('质量', quality_factor)]:
    ics = [sp_stats.spearmanr(factor.iloc[t], future_returns.iloc[t])[0] for t in range(n_days)]
    ic_mean = np.mean(ics)
    ic_ir = ic_mean / np.std(ics) if np.std(ics) > 0 else 0
    print(f"  {name}因子: 平均IC={ic_mean:.4f}, IC_IR={ic_ir:.4f}")

# 多因子合成
scores = (value_factor + momentum_factor + quality_factor) / 3
holdings = pd.DataFrame(0, index=scores.index, columns=scores.columns)
for i in range(len(scores)):
    top = scores.iloc[i].nlargest(10).index
    holdings.iloc[i][top] = 0.1
portfolio_returns = (holdings * future_returns).sum(axis=1)
cumulative = (1 + portfolio_returns).cumprod()
print(f"\n  等权多因子: 收益={cumulative.iloc[-1]-1:.2%}")

# ============================================================
# ML 策略
# ============================================================
print("\n" + "=" * 60)
print("4. ML策略 (RandomForest)")
print("=" * 60)

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# 特征工程
aapl_vol = yf.download('AAPL', start='2022-01-01', end='2025-12-31', progress=False)
if isinstance(aapl_vol.columns, pd.MultiIndex):
    vol = aapl_vol['Volume'].squeeze()
else:
    vol = aapl_vol['Volume']

feat = pd.DataFrame(index=aapl.index)
feat['ret_1d'] = aapl.pct_change(1)
feat['ret_5d'] = aapl.pct_change(5)
feat['ret_20d'] = aapl.pct_change(20)
feat['vol_20d'] = feat['ret_1d'].rolling(20).std()
feat['sma_5'] = aapl / aapl.rolling(5).mean() - 1
feat['sma_20'] = aapl / aapl.rolling(20).mean() - 1
feat['volume_ratio'] = vol / vol.rolling(20).mean() - 1
feat['target'] = feat['ret_1d'].shift(-1)
feat = feat.dropna()

split = int(len(feat) * 0.7)
train, test = feat.iloc[:split], feat.iloc[split:]
feature_cols = [c for c in feat.columns if c != 'target']
X_train, y_train = train[feature_cols], train['target']
X_test, y_test = test[feature_cols], test['target']

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

model = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
model.fit(X_train_s, y_train)
pred = model.predict(X_test_s)

signal_ml = pd.Series(0, index=aapl.index)
signal_ml.loc[test.index] = (pred > 0).astype(int)
r = vectorized_backtest(aapl, signal_ml)
test_bh = (aapl.loc[test.index].iloc[-1] / aapl.loc[test.index].iloc[0] - 1)
if r: print(f"  测试集: 收益={r['total_return']:.2%} | 夏普={r['sharpe']:.2f} | 基准={test_bh:.2%}")

# 特征重要性
imp = pd.DataFrame({'feature': feature_cols, 'importance': model.feature_importances_}).sort_values('importance', ascending=False)
print("\n  特征重要性 Top 3:")
for _, row in imp.head(3).iterrows():
    print(f"    {row['feature']:<15} {row['importance']:.4f}")

print("\n策略学习完成！")
