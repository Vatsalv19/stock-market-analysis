# sentiment-service/main.py
from fastapi import FastAPI, HTTPException
from transformers import pipeline
import yfinance as yf
from datetime import datetime
import os

app = FastAPI(
    title="Sentiment Analysis Service",
    description="Analyses financial news sentiment using FinBERT",
    version="2.0.0"
)

# ── Load FinBERT Model ────────────────────────────────
print("🤖 Loading FinBERT model... please wait")

sentiment_pipeline = pipeline(
    task="text-classification",
    model="ProsusAI/finbert",
    top_k=None
)

print("✅ FinBERT model loaded and ready!")

# ── Helper: Analyse single text ───────────────────────
def analyse_text(text: str) -> dict:
    results = sentiment_pipeline(text[:512])
    scores = {item['label']: round(item['score'], 4) for item in results[0]}
    dominant = max(scores, key=scores.get)
    return {
        "text": text[:100] + "..." if len(text) > 100 else text,
        "sentiment": dominant,
        "confidence": scores[dominant],
        "scores": scores
    }

# ── Routes ────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "sentiment-service",
        "model": "ProsusAI/finbert",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyse")
def analyse_single(payload: dict):
    """
    Analyse sentiment of a single text.
    Body: { "text": "Apple reports record profits" }
    """
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required")
    return analyse_text(text)

@app.get("/test")
def test_finbert():
    """
    Quick test to verify FinBERT is working correctly.
    No yfinance needed — tests directly with known headlines.
    """
    test_headlines = [
        "Apple reports record profits beating all expectations",
        "Company faces massive lawsuit over data privacy breach",
        "Federal Reserve announces interest rate decision tomorrow"
    ]
    results = [analyse_text(h) for h in test_headlines]
    return {
        "message": "FinBERT is working correctly!",
        "expected": ["positive", "negative", "neutral"],
        "test_results": results
    }

@app.get("/debug/{ticker}")
def debug_news(ticker: str):
    """See raw news structure from yfinance"""
    stock = yf.Ticker(ticker)
    news = stock.news
    return {
        "news_count": len(news) if news else 0,
        "raw_news": news[:2] if news else [],  # show first 2 items raw
        "first_item_keys": list(news[0].keys()) if news else []
    }



@app.get("/sentiment/{ticker}")
def get_ticker_sentiment(ticker: str):
    """
    Fetch latest news for a ticker and analyse sentiment.
    Falls back to sample headlines if no live news available.
    """
    try:
        # ── Step 1: Try fetching real news ───────────
        stock = yf.Ticker(ticker)
        news = stock.news
        headlines_source = "live"

        # ── Step 2: Fallback to sample headlines ─────
        if not news:
            print(f"⚠️  No live news for {ticker}, using sample headlines")
            headlines_source = "sample"
            news = [
                {"title": f"{ticker} stock shows strong momentum in market trading"},
                {"title": f"Investors watch {ticker} closely amid market volatility"},
                {"title": f"{ticker} reports quarterly results meeting expectations"},
                {"title": f"Analysts upgrade {ticker} price target on growth outlook"},
                {"title": f"{ticker} faces headwinds as sector sees increased competition"}
            ]

             # ── Step 3: Analyse each headline ────────────
        analysed = []
        for item in news[:5]:
            # Handle both old and new yfinance news structure
            title = (
                item.get("title")                           # old format
                or item.get("content", {}).get("title")    # new format
                or item.get("headline")                    # alternative
                or ""
            ).strip()

            if not title:
                continue

            result = analyse_text(title)
            result["publisher"] = (
                item.get("publisher")
                or item.get("content", {}).get("provider", {}).get("displayName", "")
                or "Unknown"
            )
            result["published"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            analysed.append(result)

        if not analysed:
            raise HTTPException(status_code=404, detail="No headlines to analyse")

        # ── Step 4: Calculate overall sentiment ──────
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_confidence = 0

        for item in analysed:
            sentiment_counts[item["sentiment"]] += 1
            total_confidence += item["confidence"]

        overall = max(sentiment_counts, key=sentiment_counts.get)
        avg_confidence = round(total_confidence / len(analysed), 4)

        signal_map = {
            "positive": "📈 BUY signal — positive news sentiment",
            "negative": "📉 SELL signal — negative news sentiment",
            "neutral":  "➡️  HOLD signal — neutral news sentiment"
        }

        return {
            "ticker": ticker.upper(),
            "overall_sentiment": overall,
            "avg_confidence": avg_confidence,
            "trading_signal": signal_map[overall],
            "sentiment_breakdown": sentiment_counts,
            "headlines_analysed": len(analysed),
            "data_source": headlines_source,
            "headlines": analysed,
            "analysed_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))