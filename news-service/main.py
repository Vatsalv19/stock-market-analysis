from fastapi import FastAPI , HTTPException
import yfinance as yf
from datetime import datetime

app = FastAPI(
    title = "News Service",
    description= "Fetches latest news " 
)
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "stock-data-service",
        "timestamp": datetime.now().isoformat()
    }
@app.get('/news/{ticker}')
def get_news(ticker : str):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        if not news:
            return {f"ticker : {ticker}, headlines = {[]}, message : no news found"}
        
        heaadlines = []
        for item in news[:5]:
            heaadlines.append({
                "title": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
                "published": datetime.fromtimestamp(
                item.get("providerPublishTime", 0)
                ).strftime("%Y-%m-%d %H:%M")
                 })
        return{
            "ticker" : ticker.upper(),
            "total_headlines" : len(heaadlines),
            "headlines": heaadlines,
            "fetched_at" : datetime.now().isoformat()
        }
    except Exception as e:
        return HTTPException(status_code=404,detail=str(e))