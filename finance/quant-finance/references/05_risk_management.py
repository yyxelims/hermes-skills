"""
=== 风险管理与组合优化 ===

两大主题:
  1. 仓位管理: 每次交易下多少仓位？
  2. 组合优化: 多资产之间怎么分配资金？
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 凯利公式
# ============================================================
print("=" * 60)
print("1. 凯利公式 (Kelly Criterion)")
print("=" * 60)
print("  f* = (p * b - (1-p)) / b")
print("  f*: 最优仓位, p: 胜率, b: 盈亏比")

def kelly(win_rate, avg_win, avg_loss):
    b = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    f = (win_rate * b - (1 - win_rate)) / b if b != 0 else 0
    return max(0, f)

win_rate = 0.55
f = kelly(win_rate, 0.03, 0.02)
print(f"  示例: p={win_rate}, win=3%, loss=2% → f*={f:.1%} (实践中用 {f/4:.1%})")

# 蒙特卡洛模拟
np.random.seed(42)
def simulate(capital, f, n=500, p=0.55, win_m=1.02, loss_m=0.98):
    for _ in range(n):
        bet = capital * f
        capital = capital - bet + bet * (win_m if np.random.random() < p else loss_m)
    return capital

print(f"\n  仓位    最终资金 (100次平均)")
for f_test in [0.05, 0.10, 0.25, 0.50]:
    avg = np.mean([simulate(100000, f_test) for _ in range(100)])
    print(f"  {f_test:.0%}     ${avg:,.0f}")

# ============================================================
# 2. Markowitz
# ============================================================
print("\n" + "=" * 60)
print("2. Markowitz 均值-方差优化")
print("=" * 60)

tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'JPM']
data = yf.download(tickers, start='2023-01-01', end='2025-12-31', progress=False)
if isinstance(data.columns, pd.MultiIndex):
    close = data['Close']
else:
    close = data
returns = close.pct_change().dropna()
mu = returns.mean() * 252
Sigma = returns.cov() * 252

print("年化收益:", {t: f"{mu[t]:.1%}" for t in tickers})

def port_stats(w, mu, Sigma):
    ret = np.dot(w, mu)
    risk = np.sqrt(np.dot(w.T, np.dot(Sigma, w)))
    sharpe = (ret - 0.03) / risk if risk > 0 else 0
    return ret, risk, sharpe

# 有效前沿
print("\n有效前沿:")
for target in np.linspace(mu.min(), mu.max()*0.95, 5):
    n = len(tickers)
    w0 = np.ones(n) / n
    cons = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'eq', 'fun': lambda w: np.dot(w, mu.values) - target}]
    bnds = [(0, 1) for _ in range(n)]
    res = minimize(lambda w: np.sqrt(np.dot(w.T, np.dot(Sigma.values, w))),
                   w0, method='SLSQP', bounds=bnds, constraints=cons)
    if res.success:
        ret, risk, sharpe = port_stats(res.x, mu.values, Sigma.values)
        print(f"  收益={ret:.1%} 风险={risk:.1%} 夏普={sharpe:.2f}")

# 最大夏普
def max_sharpe(mu, Sigma, rf=0.03):
    n = len(mu)
    w0 = np.ones(n) / n
    cons = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bnds = [(0, 1) for _ in range(n)]
    res = minimize(lambda w: -(np.dot(w, mu) - rf) / np.sqrt(np.dot(w.T, np.dot(Sigma, w))),
                   w0, method='SLSQP', bounds=bnds, constraints=cons)
    return res.x

w_opt = max_sharpe(mu.values, Sigma.values)
ret_opt, risk_opt, sharpe_opt = port_stats(w_opt, mu.values, Sigma.values)
print(f"\n最大夏普: 收益={ret_opt:.1%} 风险={risk_opt:.1%} 夏普={sharpe_opt:.2f}")
print(f"  权重:", {t: f"{w_opt[i]:.1%}" for i, t in enumerate(tickers)})

# 最小方差
def min_var(Sigma):
    n = len(Sigma)
    cons = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bnds = [(0, 1) for _ in range(n)]
    res = minimize(lambda w: np.dot(w.T, np.dot(Sigma, w)),
                   np.ones(n)/n, method='SLSQP', bounds=bnds, constraints=cons)
    return res.x

w_mv = min_var(Sigma.values)
ret_mv, risk_mv, sharpe_mv = port_stats(w_mv, mu.values, Sigma.values)
print(f"\n最小方差: 收益={ret_mv:.1%} 风险={risk_mv:.1%}")
print(f"  权重:", {t: f"{w_mv[i]:.1%}" for i, t in enumerate(tickers)})

# 对比
w_eq = np.ones(5) / 5
ret_eq, risk_eq, sharpe_eq = port_stats(w_eq, mu.values, Sigma.values)
print(f"\n等权组合: 收益={ret_eq:.1%} 风险={risk_eq:.1%} 夏普={sharpe_eq:.2f}")

# ============================================================
# 3. 风险平价
# ============================================================
print("\n" + "=" * 60)
print("3. 风险平价")
print("=" * 60)
vols = np.sqrt(np.diag(Sigma))
w_rp = (1 / vols) / np.sum(1 / vols)
ret_rp, risk_rp, sharpe_rp = port_stats(w_rp, mu.values, Sigma.values)
print(f"朴素风险平价 (1/波动率):")
print(f"  收益={ret_rp:.1%} 风险={risk_rp:.1%} 夏普={sharpe_rp:.2f}")
print(f"  权重:", {t: f"{w_rp[i]:.1%}" for i, t in enumerate(tickers)})

# ============================================================
# 4. 止损演示
# ============================================================
print("\n" + "=" * 60)
print("4. 追踪止损演示")
print("=" * 60)

np.random.seed(123)
price = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 50))
trail_pct = 0.08
peak = price[0]
stop = peak * (1 - trail_pct)
stopped = False

for i, p in enumerate(price):
    if p > peak:
        peak = p
        stop = peak * (1 - trail_pct)
    if p <= stop:
        print(f"  第{i}天触发止损! 最高${peak:.2f} → 止损${stop:.2f} → 当前${p:.2f}")
        stopped = True
        break

if not stopped:
    print(f"  未触发止损, 最终价格=${price[-1]:.2f}")

print("\n风险管理学习完成！")
print("  - 凯利: 理论最优仓位, 实践用 1/2 或 1/4")
print("  - Markowitz: 对输入极度敏感, 等权/风险平价更稳健")
print("  - 止损: 策略的一部分, 不是'认错'")
