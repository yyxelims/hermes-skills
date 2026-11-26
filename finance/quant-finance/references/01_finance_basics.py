"""
=== 量化金融基础：核心概念与 Python 实现 ===

本模块涵盖个人量化策略开发必需的金融基础知识：
1. 收益率计算 (简单收益率 vs 对数收益率)
2. 风险指标 (波动率、最大回撤、VaR)
3. 绩效指标 (夏普比率、Alpha/Beta、信息比率)
4. 资产定价基础 (CAPM)

适合 Python 熟练、数学基础扎实的学习者。
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from scipy import stats

# ============================================================
# 1. 收益率计算
# ============================================================
print("=" * 60)
print("1. 收益率计算")
print("=" * 60)

# 简单收益率: R_t = (P_t - P_{t-1}) / P_{t-1}
# 对数收益率: r_t = ln(P_t / P_{t-1})
# 对数收益率有可加性：多期对数收益 = 各期之和
# 对数收益率近似正态分布，更适合统计建模

prices = np.array([100, 102, 98, 103, 105, 101])

simple_returns = np.diff(prices) / prices[:-1]
log_returns = np.log(prices[1:] / prices[:-1])

print(f"价格序列: {prices}")
print(f"简单收益率: {simple_returns}")
print(f"对数收益率: {log_returns}")
print(f"对数收益可加性验证: sum(log_returns) = {sum(log_returns):.6f}")
print(f"总对数收益 vs 首尾: ln({prices[-1]}/{prices[0]}) = {np.log(prices[-1]/prices[0]):.6f}")
print()

# pandas 内置方法
df = pd.DataFrame({'price': prices})
df['simple_ret'] = df['price'].pct_change()
df['log_ret'] = np.log(df['price'] / df['price'].shift(1))
print(df)
print()

# ============================================================
# 2. 风险指标
# ============================================================
print("=" * 60)
print("2. 风险指标")
print("=" * 60)

# 2.1 波动率 (年化)
# 年化波动率 = 日波动率 * sqrt(252)

daily_returns = np.array([0.02, -0.01, 0.015, -0.005, 0.01, -0.02,
                           0.03, -0.015, 0.005, 0.01])

daily_vol = np.std(daily_returns, ddof=1)
annual_vol = daily_vol * np.sqrt(252)

print(f"日波动率: {daily_vol:.4f} ({daily_vol*100:.2f}%)")
print(f"年化波动率: {annual_vol:.4f} ({annual_vol*100:.2f}%)")
print()

# 2.2 最大回撤 (Maximum Drawdown)
# MDD = max((累计最高 - 当前值) / 累计最高)

def max_drawdown(returns):
    """计算最大回撤（接受 numpy array 或 pandas Series）"""
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min(), drawdown

cum_ret = np.array([1.0, 1.02, 1.05, 1.08, 1.03, 0.98, 1.0, 1.04, 0.95, 1.01])
mdd, dd_series = max_drawdown(np.diff(cum_ret) / cum_ret[:-1])

print(f"最大回撤: {mdd:.4f} ({mdd*100:.2f}%)")
print()

# 2.3 VaR (Value at Risk) - 历史模拟法
# 95% VaR = 收益分布的第 5 百分位数

var_95 = np.percentile(daily_returns, 5)
var_95_parametric = np.mean(daily_returns) + np.std(daily_returns, ddof=1) * stats.norm.ppf(0.05)

print(f"95% VaR (历史模拟法): {var_95:.4f} ({var_95*100:.2f}%)")
print(f"95% VaR (参数法-正态假设): {var_95_parametric:.4f} ({var_95_parametric*100:.2f}%)")
print()

# ============================================================
# 3. 绩效指标
# ============================================================
print("=" * 60)
print("3. 绩效指标")
print("=" * 60)

# 3.1 夏普比率 (Sharpe Ratio)
# Sharpe = (年化收益率 - 无风险利率) / 年化波动率
# 衡量单位风险的超额收益

rf = 0.03  # 无风险利率 3%
mean_daily = np.mean(daily_returns)
annual_return = mean_daily * 252
sharpe = (annual_return - rf) / annual_vol

print(f"日平均收益: {mean_daily:.6f}")
print(f"年化收益率: {annual_return:.4f} ({annual_return*100:.2f}%)")
print(f"年化波动率: {annual_vol:.4f} ({annual_vol*100:.2f}%)")
print(f"夏普比率: {sharpe:.4f}")
print("  解释: >1 良好, >2 优秀, >3 极好")
print()

# 3.2 Calmar 比率
# Calmar = 年化收益率 / |最大回撤|
calmar = annual_return / abs(mdd)
print(f"Calmar 比率: {calmar:.4f}")
print()

# ============================================================
# 4. CAPM 与 Alpha/Beta
# ============================================================
print("=" * 60)
print("4. CAPM (资本资产定价模型)")
print("=" * 60)
print("""
CAPM 公式: E(R_i) = R_f + β_i * (E(R_m) - R_f)

其中:
  E(R_i): 资产 i 的期望收益
  R_f: 无风险利率
  β_i: 资产 i 相对市场的敏感度
  E(R_m) - R_f: 市场风险溢价

Alpha = 实际收益 - CAPM 预测收益
Beta = Cov(R_i, R_m) / Var(R_m)
""")

# 模拟计算 Beta
market_returns = np.array([0.01, -0.005, 0.02, -0.01, 0.015, -0.008,
                            0.025, -0.012, 0.008, 0.005])
stock_returns = daily_returns  # 复用前面的日收益

covariance = np.cov(stock_returns, market_returns, ddof=1)[0, 1]
market_variance = np.var(market_returns, ddof=1)
beta = covariance / market_variance

# Alpha: 回归截距
slope, intercept, r_value, p_value, std_err = stats.linregress(market_returns, stock_returns)
alpha = intercept * 252  # 年化

print(f"Beta: {beta:.4f}")
print(f"  解释: Beta=1 与市场同步, >1 比市场波动大, <1 比市场稳定")
print(f"年化 Alpha: {alpha:.4f} ({alpha*100:.2f}%)")
print(f"R²: {r_value**2:.4f}")
print()

# ============================================================
# 5. 组合基础
# ============================================================
print("=" * 60)
print("5. 组合收益率与风险")
print("=" * 60)

# 两资产组合
w1, w2 = 0.6, 0.4  # 权重
r1, r2 = 0.12, 0.08  # 年化期望收益
s1, s2 = 0.20, 0.15  # 年化波动率
rho = 0.3  # 相关系数

portfolio_return = w1 * r1 + w2 * r2
portfolio_risk = np.sqrt(w1**2 * s1**2 + w2**2 * s2**2 + 2 * w1 * w2 * s1 * s2 * rho)

print(f"组合收益: {portfolio_return:.4f} ({portfolio_return*100:.2f}%)")
print(f"组合风险: {portfolio_risk:.4f} ({portfolio_risk*100:.2f}%)")
print(f"分散化收益: 加权平均风险={w1*s1 + w2*s2:.4f}, 组合风险={portfolio_risk:.4f}")
print()

# ============================================================
print("=" * 60)
print("基础概念学习完成！")
print("核心要点：")
print("  - 对数收益率适合统计建模 (可加性+近似正态)")
print("  - 年化: 日收益率 * 252, 日波动率 * sqrt(252)")
print("  - 夏普比率是最常用的风险调整后收益指标")
print("  - 最大回撤衡量策略最坏情况下的亏损幅度")
print("  - Beta 衡量系统性风险, Alpha 衡量超额收益")
print("=" * 60)
