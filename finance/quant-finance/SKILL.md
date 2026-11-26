---
name: quant-finance
description: >
  Quantitative finance toolkit for personal strategy development.
  Covers: data acquisition (yfinance/akshare), vectorized & event-driven backtesting,
  trend/mean-reversion/factor/ML strategies, portfolio optimization (Markowitz, Risk Parity),
  risk management (Kelly criterion, stop-loss). Use this whenever the user wants to
  develop, backtest, or analyze quantitative trading strategies.
tags: [quant, finance, trading, backtesting, python]
---

# Quant Finance Skill

## Environment

Python 3.12 on macOS. Key packages installed:
- numpy, pandas, matplotlib, scipy, scikit-learn, statsmodels
- yfinance (global markets), akshare (Chinese markets)
- backtrader (event-driven backtesting)
- empyrical-reloaded, pyfolio-reloaded (performance analysis)
- ta (technical indicators)

**SSL workaround**: On this macOS, `pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org <packages>` is needed.

## Project Structure

All quant lab code lives in `/Users/you/quant-lab/`:
- `00_glossary.md` — Comprehensive Chinese terminology reference (50+ concepts)
- `00_glossary.html` — Same glossary as a self-contained dark-themed HTML page (open in browser)
- `01_finance_basics.py` — Returns, volatility, Sharpe, CAPM, portfolio basics
- `02_data_acquisition.py` — yfinance + akshare data fetching and cleaning
- `03_backtesting.py` — Vectorized + Backtrader backtesting
- `04_strategies.py` — Trend, mean-reversion, factor, ML strategies
- `05_risk_management.py` — Kelly criterion, Markowitz, risk parity, stop-loss
- `data/` — Downloaded market data:
  - `index_*.csv` (4 files): 沪深300, 上证指数, 中证500, 创业板指 (akshare format, flat columns)
  - `stock_*.csv` (8 files): 贵州茅台, 宁德时代, 比亚迪, 中国平安, 招商银行, 五粮液, 隆基绿能, 药明康德 (yfinance MultiIndex format)

## Reference Files

- `references/glossary.md` — Full Chinese quant finance terminology dictionary
- `references/a-share-data-pull.md` — Reliable recipe for A-share index + stock data (akshare + yfinance fallback pattern)
- `references/insurance-ml-patterns.md` — Production ML: sentinel imputation, F-beta threshold tuning, key cleaning, prediction-as-feature
- `references/offline-pip-install.md` — Offline Python package management: PyPI JSON API, Tsinghua mirror, batch install scripts
- `references/01_finance_basics.py` through `references/05_risk_management.py` — Runnable learning modules

## Core Knowledge

### 1. Returns
- Simple return: (P_t - P_t-1) / P_t-1
- Log return: ln(P_t / P_t-1) — additive, approximately normal, preferred for modeling
- Annualization: daily return × 252, daily vol × sqrt(252)

### 2. Key Metrics
- Sharpe Ratio = (annual_return - rf) / annual_vol. Interpretation: >1 good, >2 excellent, >3 exceptional
- Max Drawdown: max(peak - trough) / peak
- Calmar Ratio: annual_return / |max_drawdown|
- VaR (95%): 5th percentile of returns (historical), or mean + σ × Φ⁻¹(0.05) (parametric)
- Beta = Cov(R_i, R_m) / Var(R_m)
- Alpha = actual_return - CAPM_predicted_return (annualized from regression intercept)

### 3. Data Sources

**yfinance** — global stocks/ETFs/indices:
- `yf.download('AAPL', start='2023-01-01', end='2025-12-31')`
- A-share tickers: Shanghai `CODE.SS` (e.g. `600519.SS`), Shenzhen `CODE.SZ` (e.g. `300750.SZ`)
- **MultiIndex column format**: Since yfinance 0.2.x, returned DataFrames use MultiIndex columns `(Price, Ticker)`. Always check:
  ```python
  if isinstance(data.columns, pd.MultiIndex):
      # Single ticker: data['Close'] is a DataFrame → .squeeze() or .iloc[:,0]
      # Multi ticker:  data['Close'] is a DataFrame with one column per ticker
      close = data['Close'].squeeze()  # safe for both
  ```
- When downloading multiple tickers: `data['Close']['AAPL']` works. For single ticker: `data['Close'].squeeze()` returns a Series.

**akshare** — Chinese A-shares, futures, funds, macro data:
- Indices (always works): `ak.stock_zh_index_daily(symbol="sh000300")`
  - Shanghai indices: `sh` prefix (sh000001=上证, sh000300=沪深300, sh000905=中证500)
  - Shenzhen indices: `sz` prefix (sz399006=创业板指)
  - Column `date` is `datetime.date`, filter with `date(2025,5,1)` not strings
- Individual stocks (`ak.stock_zh_a_hist`): **may fail** due to network/proxy restrictions on `push2his.eastmoney.com`.
  **Fallback**: Use yfinance with `.SS`/`.SZ` suffix — covers all major A-shares and is more reliable.

**A-share data strategy**: Prefer yfinance for individual stocks (`.SS`/`.SZ`), use akshare for indices and when yfinance coverage is insufficient.
- **财联社 (Cailian Press) financial news**: akshare's cls support is deprecated (old endpoint `/nodeapi/telegraphList` is 404). For 财联社电报/data, see `china-web-data` skill → `references/cailianpress-data-access.md` — covers RSSHub, a-stock-data, cailianpress-unified, Investor RSS, and direct API findings.

### 4. Data Cleaning
- Missing values: **ffill** for financial data (never mean-fill)
- Outlier detection: MAD (Median Absolute Deviation) more robust than Z-score
- Outlier treatment: Winsorize (clip at quantiles) preserves data volume
- Suspension detection: consecutive days with price_diff == 0
- **pandas pct_change deprecation**: In pandas ≥2.1, use `pct_change(fill_method=None)` to silence FutureWarning.

### 4b. CSV Persistence (yfinance MultiIndex roundtrip)

yfinance DataFrames have 3-row MultiIndex headers `(Price, Ticker)`. When saved/loaded:

```python
# SAVE — preserves MultiIndex
df.to_csv('stock_茅台.csv')

# LOAD — must specify header rows
df = pd.read_csv('stock_茅台.csv', header=[0,1], index_col=0, parse_dates=True)
# Access: ('Close', ticker) tuple
close = df[('Close', df.columns[0][1])]

# Multi-ticker download: df['Close'] is a DataFrame, one column per ticker
multi = pd.read_csv('multi.csv', header=[0,1], index_col=0, parse_dates=True)
returns = multi['Close'].pct_change(fill_method=None)
```

**akshare index CSVs** are simpler — flat columns, `date` column:
```python
df = pd.read_csv('index_沪深300.csv', parse_dates=['date'])
close = df['close']  # simple column access
```

### 5. Backtesting Approaches

**Vectorized (pandas-based)**: Fast, good for quick idea validation.
- Signal shifted by 1 day (yesterday's signal → today's position)
- Transaction costs: commission + slippage deducted on position changes
- Limitation: cannot model intraday, complex order logic

**Event-driven (Backtrader)**: Professional, simulates real trading.
- `bt.Strategy` subclass with `__init__` (indicators) and `next()` (logic per bar)
- Use `self.order = self.buy()` / `self.sell()`, check `self.position`
- Analyzers: SharpeRatio, DrawDown, Returns, TradeAnalyzer
- Commission: `cerebro.broker.setcommission(commission=0.001)`

**Common pitfalls**: look-ahead bias, survivorship bias, overfitting, ignoring transaction costs, data snooping.

### 6. Strategy Types

**Trend Following** — works in trending markets, whipsaws in ranges:
- SMA crossover (20/50): Golden Cross / Death Cross
- Momentum (60-day): long if past 60d return > 0
- Donchian Channel (20-day): breakout above N-day high

**Mean Reversion** — works in range-bound markets, fails in trends:
- Bollinger Bands (20,2): buy at lower band, sell at upper band
- RSI (14, 30/70): buy oversold (<30), sell overbought (>70)
- Pairs Trading: cointegration test → trade spread z-score

**Factor Investing** — institutional approach:
- Value, Momentum, Quality, Low Vol, Size factors
- IC (Information Coefficient): Spearman rank correlation of factor vs future return
- IC_IR = mean(IC) / std(IC) — measures factor stability

**ML-based** — use models to predict returns:
- Time series split (NOT random K-fold)
- Feature engineering matters more than model choice
- RandomForest, XGBoost, LGBM for tabular data; LSTM for sequences
- Overfitting is the #1 enemy

### 7. Risk Management

**Kelly Criterion**: f* = (p × b - (1-p)) / b
- f* = optimal bet fraction; use 1/2 or 1/4 Kelly in practice
- Larger bets REDUCE long-term returns due to volatility drag

**Markowitz Mean-Variance**:
- min w^T Σ w s.t. w^T μ = target, Σw = 1, w ≥ 0
- Extremely sensitive to input estimates; equal-weight often more robust

**Risk Parity**:
- Naive: w_i ∝ 1/σ_i (inverse volatility weighting)
- Each asset contributes equal risk to the portfolio

**Stop-Loss Types**:
- Fixed %: exit at X% loss
- Trailing: exit when price drops X% from peak
- Time-based: exit after N days without profit
- ATR-based: dynamic stop distance based on volatility

## Workflow for Strategy Development

1. Get data: `yfinance` for global, `akshare` for Chinese markets
2. Clean data: handle missing values, outliers, suspensions
3. Define signals: use `ta` library for technical indicators
4. Backtest: vectorized (fast) first, then Backtrader (rigorous)
5. Evaluate: Sharpe, max drawdown, win rate, profit factor
6. Optimize: walk-forward validation, not in-sample optimization
7. Risk management: position sizing (Kelly), stop-loss, portfolio constraints
