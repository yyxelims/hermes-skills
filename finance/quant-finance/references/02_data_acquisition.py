"""
=== 量化金融数据获取与清洗 ===

数据源:
  - yfinance: 全球股票/ETF/指数数据 (免费, Yahoo Finance)
  - akshare: A股/期货/基金/债券/宏观数据 (免费, 国内全覆盖)

关键数据处理技巧:
  1. 复权处理 (前复权/后复权)
  2. 停牌/缺失值处理
  3. 异常值检测
  4. 技术指标计算
  5. 日频 → 周频/月频转换
"""

import numpy as np
import pandas as pd
import yfinance as yf
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 第一部分: yfinance - 全球市场数据
# ============================================================
print("=" * 60)
print("第一部分: yfinance 获取美股/全球数据")
print("=" * 60)

def demo_yfinance():
    """演示 yfinance 基本用法"""

    # --- 下载单只股票历史数据 ---
    print("\n1. 下载苹果(AAPL)近 1 年日线数据")
    aapl = yf.download('AAPL', period='6mo', progress=False)

    if isinstance(aapl.columns, pd.MultiIndex):
        aapl.columns = aapl.columns.droplevel(1)

    print(f"   数据形状: {aapl.shape}")
    print(f"   日期范围: {aapl.index[0].strftime('%Y-%m-%d')} ~ {aapl.index[-1].strftime('%Y-%m-%d')}")
    print(f"   列名: {list(aapl.columns)}")
    print(aapl.tail(3))

    # --- 多只股票同时下载 ---
    print("\n2. 批量下载多只股票")
    tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    data = yf.download(tickers, period='3mo', progress=False)

    # 计算收益率
    close_prices = data['Close']
    returns = close_prices.pct_change().dropna()

    print(f"   各股票日收益率统计:")
    print(f"   {'Ticker':<8} {'年均收益':>10} {'年化波动':>10} {'夏普比率':>10}")
    print(f"   {'-'*45}")
    for ticker in tickers:
        r = returns[ticker]
        ann_ret = r.mean() * 252
        ann_vol = r.std() * np.sqrt(252)
        sharpe = (ann_ret - 0.04) / ann_vol if ann_vol > 0 else 0
        print(f"   {ticker:<8} {ann_ret:>10.4f} {ann_vol:>10.4f} {sharpe:>10.4f}")

    # --- 获取指数数据 ---
    print("\n3. 指数数据")
    sp500 = yf.download('^GSPC', period='6mo', progress=False)
    print(f"   标普500: {sp500['Close'].iloc[-1].item():.2f}")

    return aapl, returns

aapl_data, returns_data = demo_yfinance()

# ============================================================
# 第二部分: akshare - A 股 / 国内数据
# ============================================================
print("\n" + "=" * 60)
print("第二部分: akshare 获取 A 股数据")
print("=" * 60)

def demo_akshare():
    """演示 akshare 基本用法"""

    # --- A 股个股日线 ---
    print("\n1. 贵州茅台(600519)日线数据")
    try:
        df = ak.stock_zh_a_hist(symbol="600519", period="daily",
                                start_date="20240101", end_date="20240630",
                                adjust="qfq")  # qfq=前复权

        print(f"   数据形状: {df.shape}")
        print(f"   列名: {list(df.columns)}")
        print(df.tail(3))
    except Exception as e:
        print(f"   akshare 获取失败: {e} (可能需要网络或版本更新)")

    # --- A 股实时行情 ---
    print("\n2. A 股市值排行 (Top 5)")
    try:
        market = ak.stock_zh_a_spot_em()
        top5 = market.nlargest(5, '总市值')[['代码', '名称', '最新价', '总市值', '市盈率-动态']]
        print(top5.to_string(index=False))
    except Exception as e:
        print(f"   获取失败: {e}")

    # --- 指数数据 ---
    print("\n3. 沪深300指数")
    try:
        hs300 = ak.stock_zh_index_daily(symbol="sh000300")
        print(f"   数据形状: {hs300.shape}")
        print(hs300.tail(3))
    except Exception as e:
        print(f"   获取失败: {e}")

try:
    demo_akshare()
except Exception as e:
    print(f"akshare 演示部分失败: {e}")

# ============================================================
# 第三部分: 数据清洗与预处理
# ============================================================
print("\n" + "=" * 60)
print("第三部分: 数据清洗与特征工程")
print("=" * 60)

np.random.seed(42)
dates = pd.date_range('2024-01-01', '2024-06-30', freq='B')
n = len(dates)

price = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, n))
price[10] = np.nan
price[20] = price[20] * 3
price[50:53] = 100

df = pd.DataFrame({
    'date': dates,
    'close': price,
    'volume': np.random.randint(1000000, 10000000, n).astype(float)
})
df.set_index('date', inplace=True)
df.loc[df.index[10], 'volume'] = np.nan

print("原始数据统计 (含异常值):")
print(df.describe())

# --- 缺失值处理 ---
print("\n缺失值处理")
missing = df.isnull().sum()
print(f"   缺失值: close={missing['close']}, volume={missing['volume']}")

df['close'] = df['close'].ffill()
df['volume'] = df['volume'].fillna(df['volume'].median())
print(f"   填充后缺失值: {df.isnull().sum().sum()}")

# --- 异常值检测 (MAD) ---
print("\n异常值检测 (MAD 方法)")
returns = df['close'].pct_change()
median_ret = returns.median()
mad = np.median(np.abs(returns - median_ret))
threshold = 5
outliers = np.abs(returns - median_ret) > threshold * mad
print(f"   检测到 {outliers.sum()} 个异常收益日")

upper = returns.quantile(0.99)
lower = returns.quantile(0.01)
returns_winsorized = returns.clip(lower, upper)
print(f"   Winsorize 后范围: [{lower:.4f}, {upper:.4f}]")

# --- 停牌识别 ---
print("\n停牌识别")
price_diff = df['close'].diff()
suspension = (price_diff == 0)
print(f"   疑似停牌日数: {suspension.sum()}")

# --- 技术指标 ---
print("\n技术指标计算")
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

clean_price = df['close'].ffill()
df['sma_20'] = SMAIndicator(close=clean_price, window=20).sma_indicator()
df['rsi_14'] = RSIIndicator(close=clean_price, window=14).rsi()
bb = BollingerBands(close=clean_price, window=20, window_dev=2)
df['bb_upper'] = bb.bollinger_hband()
df['bb_lower'] = bb.bollinger_lband()
macd = MACD(close=clean_price)
df['macd'] = macd.macd()

print(f"   特征列: {list(df.columns)}")
print(df[['close', 'sma_20', 'rsi_14', 'bb_upper', 'bb_lower', 'macd']].tail(5))

# --- 重采样 ---
print("\n重采样 (日频 → 周频)")
weekly = df['close'].resample('W').agg(['first', 'last', 'max', 'min', 'mean'])
weekly['return'] = weekly['last'].pct_change()
print(f"   周线数据: {len(weekly)} 周")
print(weekly.tail(3))

print("\n" + "=" * 60)
print("数据获取与清洗学习完成！")
print("=" * 60)
