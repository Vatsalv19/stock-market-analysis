from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from datetime import datetime

app = FastAPI(
    title  = "API Gateway",
    description="Central gateway for stock data and sentiment analysis services",
    version="1.0.0"
)
# ── CORS Middleware ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Service URLs (use Docker service names) ─────────
STOCK_SERVICE = "http://localhost:8000"
NEWS_SERVICE = "http://localhost:8001"
SENTIMENT_SERVICE = "http://localhost:8002"

async def call_service(url : str) ->dict:
    """
    Makes async  HTTP call to a microservice .
    REturns error Dict if call fails.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"error": f"Failed to connect to {url}"}
        except TimeoutError:
            return {"error": f"Request to {url} timed out"}
        except Exception as e:
            return {"error":str(e), "url": url}
    
# ── Routes ────────────────────────────────────────────
@app.get('/health')
async def health_check():
     """
    Checks health of ALL services simultaneously
    Uses asyncio.gather to call all at the same time
    """
     stock_health , news_health , sentiment_health = await asyncio.gather(
        call_service(f"{STOCK_SERVICE}/health"),
        call_service(f"{NEWS_SERVICE}/health"),
        call_service(f"{SENTIMENT_SERVICE}/health")
     )

     return {
         "gateway": "Healthy",
         "timestamp": datetime.now().isoformat(),
         "services":{
                "stock_service": stock_health,
                "news_service": news_health,
                "sentiment_service": sentiment_health
         }
     }
@app.get("/api/stock/{ticker}")
async def get_stock(ticker: str):
    """
    Route to stock_service
    """
    return await call_service(f"{STOCK_SERVICE}/stock/{ticker}")


@app.get("/api/stock/{ticker}/history")
async def get_history(ticker: str, period: str = "1mo"):
    """Route to stock-service history"""
    return await call_service(
        f"{STOCK_SERVICE}/stock/{ticker}/history?period={period}"
    )

@app.get("/api/news/{ticker}")
async def get_news(ticker: str):
    """Route to news-service"""
    return await call_service(f"{NEWS_SERVICE}/news/{ticker}")

@app.get("/api/sentiment/{ticker}")
async def get_sentiment(ticker: str):
    """Route to sentiment-service"""
    return await call_service(f"{SENTIMENT_SERVICE}/sentiment/{ticker}")

@app.get("/api/dashboard/{ticker}")
async def get_dashboard(ticker: str):
    """
    ⭐ THE POWER ENDPOINT ⭐
    Calls stock + news + sentiment ALL AT ONCE
    Returns complete dashboard data in one request!
    """
    # asyncio.gather runs all 3 calls simultaneously
    stock_data, news_data, sentiment_data = await asyncio.gather(
        call_service(f"{STOCK_SERVICE}/stock/{ticker}"),
        call_service(f"{NEWS_SERVICE}/news/{ticker}"),
        call_service(f"{SENTIMENT_SERVICE}/sentiment/{ticker}"),
    )

    return {
        "ticker": ticker.upper(),
        "timestamp": datetime.now().isoformat(),
        "stock":     stock_data,
        "news":      news_data,
        "sentiment": sentiment_data,
    }