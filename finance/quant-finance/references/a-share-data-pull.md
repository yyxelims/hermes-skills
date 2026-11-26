# A-Share Data Pull: Reliable Recipe

**Problem**: akshare's `stock_zh_a_hist` hits `push2his.eastmoney.com` which frequently fails with proxy/network errors (ProxyError, RemoteDisconnected) from sandboxed or restricted environments. Web scraping Chinese data portals (Baidu Baike, Ctrip, Baidu Map) for structured data is unreliable due to heavy SPAs, anti-bot measures, and JS rendering requirements.

**Solution**: Two-tier approach for Chinese market data:

## Tier 1: Indices — akshare (always works)

```python
import akshare as ak
from datetime import date

hs300 = ak.stock_zh_index_daily(symbol='sh000300')
hs300 = hs300[(hs300['date'] >= date(2025,5,1)) & (hs300['date'] <= date(2026,5,1))]
# Column `date` is datetime.date, filter with date objects not strings
```

Shanghai indices: `sh` prefix (`sh000001`, `sh000300`, `sh000905`)
Shenzhen indices: `sz` prefix (`sz399006`)

## Tier 2: Individual Stocks — yfinance (more reliable)

```python
import yfinance as yf

# Shanghai: .SS suffix, Shenzhen: .SZ suffix
tickers = {
    '贵州茅台': '600519.SS',
    '宁德时代': '300750.SZ',
    '比亚迪':   '002594.SZ',
}

for name, ticker in tickers.items():
    df = yf.download(ticker, start='2025-05-01', end='2026-05-01', progress=False)
    # yfinance ≥0.2.x returns MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        close = df['Close'].squeeze()  # safe for single ticker
    df.to_csv(f'stock_{name}.csv')
```

## Tier 3: Amap/Baidu API for POI/structured lookup

For phone numbers, addresses, and business data about Chinese entities (scenic spots, companies, etc.), use the Amap Web Service API instead of web scraping. See the `amap-poi-lookup` skill.

### CSV Persistence (yfinance roundtrip)

```python
# SAVE — MultiIndex preserved
df.to_csv('stock.csv')

# LOAD — must specify header rows
df = pd.read_csv('stock.csv', header=[0,1], index_col=0, parse_dates=True)
close = df[('Close', ticker)]  # tuple access for MultiIndex

# akshare index CSVs are flat
df = pd.read_csv('index.csv', parse_dates=['date'])
close = df['close']
```
