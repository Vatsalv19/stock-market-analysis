from fastapi import FastAPI, HTTPException
import yfinance as yf
from datetime import datetime
import redis
import json
import os

app = FastAPI(
    title="Stock Data Service",
    description="Fetches real-time stock data with Redis caching",
    version="2.0.0"
)

# ── Connect to Redis ──────────────────────────────────
# os.getenv reads from environment variables we set in docker-compose
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True        # return strings not bytes
)

@app.get("/health")
def health_check():
    # Also check Redis connection
    try:
        r.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"

    return {
        "status": "healthy",
        "service": "stock-data-service",
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    ticker = ticker.upper()
    cache_key = f"stock:{ticker}"         # e.g. "stock:AAPL"

    # ── Step 1: Check Redis cache first ──────────────
    cached = r.get(cache_key)
    if cached:
        data = json.loads(cached)
        data["source"] = "cache"          # tell client it came from cache
        return data

    # ── Step 2: Cache miss — fetch from Yahoo Finance ─
    try:
        stock = yf.Ticker(ticker)
        fast = stock.fast_info

        data = {
            "ticker": ticker,
            "current_price": fast.last_price,
            "previous_close": fast.previous_close,
            "day_high": fast.day_high,
            "day_low": fast.day_low,
            "currency": fast.currency,
            "exchange": fast.exchange,
            "fetched_at": datetime.now().isoformat(),
            "source": "live"              # tell client it came from live API
        }

        # ── Step 3: Store in Redis for 60 seconds ────
        # Next request within 60s gets cached data instantly
        r.setex(cache_key, 60, json.dumps(data))

        # ── Step 4: Publish to Redis channel ─────────
        # Any service subscribed to "stock_updates" gets this!
        r.publish("stock_updates", json.dumps({
            "ticker": ticker,
            "price": fast.last_price,
            "timestamp": datetime.now().isoformat()
        }))

        return data

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Stock '{ticker}' not found",
                "tip": "For Indian stocks use '.NS'. Example: RELIANCE.NS",
                "debug": str(e)
            }
        )

@app.get("/stock/{ticker}/history")
def get_history(ticker: str, period: str = "1mo"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No history for {ticker}")

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