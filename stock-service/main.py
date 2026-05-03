from fastapi import FastAPI, HTTPException
import yfinance as yf
from datetime import datetime

# ── Fix for Yahoo Finance blocking Docker requests ──
import yfinance.data as _yf_data
_yf_data._DT_FORMAT = "%Y-%m-%d %H:%M:%S"

app = FastAPI(
    title="Stock Data Service",
    description="Fetches real-time stock data",
    version="1.0.0"
)

# Helper function - reuse across routes
def get_ticker(symbol: str):
    ticker = yf.Ticker(symbol)
    # Force yfinance to use browser-like headers
    ticker._session = None
    return ticker

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "stock-data-service",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        
        # Use fast_info - more reliable than .info
        fast = stock.fast_info

        return {
            "ticker": ticker.upper(),
            "current_price": fast.last_price,
            "previous_close": fast.previous_close,
            "day_high": fast.day_high,
            "day_low": fast.day_low,
            "volume": fast.three_month_average_volume,
            "currency": fast.currency,
            "exchange": fast.exchange,
            "fetched_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Stock '{ticker}' not found",
                "tip": "For Indian stocks use '.NS'. Example: RELIANCE.NS, TCS.NS",
                "debug": str(e)
            }
        )

@app.get("/stock/{ticker}/history")
def get_history(ticker: str, period: str = "1mo"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"No history found for '{ticker}'",
                    "tip": "Try AAPL, GOOGL, or RELIANCE.NS"
                }
            )

        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": str(date.date()),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"])
            })

        return {
            "ticker": ticker.upper(),
            "period": period,
            "data_points": len(data),
            "history": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))