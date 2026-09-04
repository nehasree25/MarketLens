import yfinance as yf

symbols = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "ITC.NS",
    "BHARTIARTL.NS",
    "LT.NS",
    "AXISBANK.NS"
]

data = yf.download(
    symbols,
    period="1d",
    interval="5m",
    group_by="ticker"
)

print(data)