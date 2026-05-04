# 📈 Stock Market Dashboard

A full-stack microservices application that provides real-time stock data, financial news, and AI-powered sentiment analysis — all orchestrated with Docker Compose.







***

## 🏗️ Architecture

```
Browser (React)
     │
     ▼ http://localhost:3000
┌─────────────────┐
│   Frontend      │  React + Recharts
│   (Port 3000)   │
└────────┬────────┘
         │ http://localhost:8088
         ▼
┌─────────────────┐
│   API Gateway   │  FastAPI — routes & aggregates all services
│   (Port 8088)   │
└────────┬────────┘
         │ Docker Internal Network (service names)
    ┌────┴─────────────────────────┐
    │            │                 │
    ▼            ▼                 ▼
┌────────┐  ┌─────────┐  ┌──────────────────┐
│ Stock  │  │  News   │  │   Sentiment AI   │
│Service │  │ Service │  │    Service       │
│:8000   │  │ :8001   │  │    :8002         │
└───┬────┘  └─────────┘  └──────────────────┘
    │              (FinBERT NLP Model)
    ▼
┌─────────┐
│  Redis  │  Cache Layer (60s TTL)
│  :6379  │
└─────────┘
```

## 🚀 Services

| Service | Port | Tech Stack | Responsibility |
|---|---|---|---|
| **Frontend** | 3000 | React, Recharts | Dashboard UI with charts |
| **API Gateway** | 8088 | FastAPI, httpx | Request routing & aggregation |
| **Stock Service** | 8000 | FastAPI, yfinance | Real-time stock prices & history |
| **News Service** | 8001 | FastAPI | Financial news aggregation |
| **Sentiment Service** | 8002 | FastAPI, FinBERT, PyTorch | AI-powered sentiment analysis |
| **Redis** | 6379 | Redis 7 | Caching with 60s TTL |

***

## ✨ Features

- **Real-Time Stock Data** — Live prices, OHLCV data, and historical charts via yfinance
- **AI Sentiment Analysis** — FinBERT transformer model analyzes news sentiment (Positive/Neutral/Negative)
- **Redis Caching** — 60-second TTL cache reduces API calls and improves response time
- **Microservices Architecture** — Each service is independently deployable and scalable
- **API Gateway Pattern** — Single entry point aggregates all services into one `/api/dashboard/{symbol}` response
- **Graceful Fallback** — Mock data fallback ensures dashboard never breaks if Yahoo Finance is unavailable
- **Health Checks** — Every service exposes a `/health` endpoint; Docker Compose uses healthchecks for startup order

***

## 🛠️ Tech Stack

### Backend
- **FastAPI** — High-performance async Python web framework
- **yfinance** — Yahoo Finance market data library
- **Transformers (HuggingFace)** — FinBERT pre-trained NLP model for financial sentiment
- **PyTorch (CPU)** — Deep learning inference engine
- **Redis (redis-py)** — In-memory caching client
- **httpx** — Async HTTP client for inter-service communication

### Frontend
- **React 18** — Component-based UI library
- **Recharts** — Composable chart library for stock price graphs
- **Axios** — HTTP client for API calls

### Infrastructure
- **Docker** — Containerization for all 6 services
- **Docker Compose** — Multi-container orchestration
- **Docker Bridge Network** — Isolated internal network for service-to-service communication

***

## 📦 Project Structure

```
Stock-Market-Dashboard/
├── docker-compose.yml          # Orchestrates all 6 services
│
├── frontend/                   # React dashboard
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       └── App.js
│
├── api-gateway/                # FastAPI API Gateway
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── stock-service/              # Stock price & history service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── news-service/               # Financial news service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
└── sentiment-service/          # AI sentiment analysis service
    ├── Dockerfile
    ├── requirements.txt
    └── main.py
```

***

## ⚡ Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- 4GB+ RAM (FinBERT model requires ~2GB)

### Run the project

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/Stock-Market-Dashboard.git
cd Stock-Market-Dashboard

# Start all 6 services with one command
docker compose up --build
```

> ⏳ First build takes ~5-10 minutes (downloads PyTorch + FinBERT model).
> Subsequent starts use Docker cache and take ~15 seconds.

### Access the app

| URL | Description |
|---|---|
| http://localhost:3000 | React Dashboard |
| http://localhost:8088/api/dashboard/AAPL | Full aggregated data |
| http://localhost:8088/docs | API Gateway Swagger UI |
| http://localhost:8000/docs | Stock Service Swagger UI |
| http://localhost:8002/docs | Sentiment Service Swagger UI |

***

## 🔌 API Reference

### API Gateway — `localhost:8088`

```http
GET /api/dashboard/{symbol}      # All data aggregated (stock + news + sentiment)
GET /api/stock/{symbol}          # Current stock price
GET /api/stock/{symbol}/history  # Historical OHLCV data
GET /api/news/{symbol}           # Latest news articles
GET /api/sentiment/{symbol}      # AI sentiment score
GET /health                      # Gateway health check
```

### Stock Service — `localhost:8000`

```http
GET /stock/{symbol}              # Live price data
GET /stock/{symbol}/history      # OHLCV history (?period=1mo)
GET /cache/info                  # Redis cache status
GET /health                      # Service health + Redis status
```

### Example Response — `/api/dashboard/AAPL`

```json
{
  "ticker": "AAPL",
  "timestamp": "2026-05-05T00:00:00",
  "stock": {
    "ticker": "AAPL",
    "current_price": 189.5,
    "previous_close": 187.2,
    "day_high": 191.3,
    "day_low": 186.8,
    "currency": "USD",
    "source": "live 🌐"
  },
  "news": { "articles": [...] },
  "sentiment": {
    "symbol": "AAPL",
    "sentiment": "positive",
    "score": 0.87,
    "model": "FinBERT"
  }
}
```

***

## 🐳 Docker Compose Details

### Service Startup Order

```
Redis (healthcheck) → Stock Service → News Service → Sentiment Service → API Gateway → Frontend
```

Redis uses a `healthcheck` with `redis-cli ping`. All dependent services use `condition: service_healthy` to guarantee correct startup order.

### Networking

All services share a custom Docker bridge network `stock-network`. Services communicate using Docker's internal DNS — service names resolve to container IPs automatically:

```python
# ✅ Correct — inside containers
STOCK_URL = "http://stock-service:8000"

# ❌ Wrong — localhost resolves to the container itself
STOCK_URL = "http://localhost:8000"
```

### Environment Variables

| Variable | Service | Default | Description |
|---|---|---|---|
| `REDIS_HOST` | stock-service | `localhost` | Redis hostname |
| `REDIS_PORT` | stock-service | `6379` | Redis port |
| `STOCK_SERVICE_URL` | api-gateway | `http://stock-service:8000` | Internal stock URL |
| `NEWS_SERVICE_URL` | api-gateway | `http://news-service:8001` | Internal news URL |
| `SENTIMENT_SERVICE_URL` | api-gateway | `http://sentiment-service:8002` | Internal sentiment URL |
| `REACT_APP_API_URL` | frontend | `http://localhost:8088` | Gateway URL for browser |

***

## 🤖 AI Sentiment Analysis

The sentiment service uses **FinBERT** — a BERT model fine-tuned on financial text by ProsusAI. It classifies news headlines into:

- 🟢 **Positive** — Bullish market signal
- 🟡 **Neutral** — No strong directional signal
- 🔴 **Negative** — Bearish market signal

```python
from transformers import pipeline

nlp = pipeline("sentiment-analysis", model="ProsusAI/finbert")
result = nlp("Apple reports record quarterly earnings")
# → [{'label': 'positive', 'score': 0.98}]
```

***

## 🧠 Key Concepts Demonstrated

- **Microservices Pattern** — Services are decoupled, independently deployable units
- **API Gateway Pattern** — Single entry point that aggregates multiple backend services
- **Redis Caching** — TTL-based cache reduces latency and external API load
- **Docker Networking** — Bridge networks with DNS-based service discovery
- **Health Checks** — Liveness probes ensure services start in correct dependency order
- **Graceful Degradation** — Mock data fallback prevents full system failure
- **Async HTTP** — `httpx.AsyncClient` for non-blocking inter-service calls
- **NLP in Production** — Serving a transformer model via REST API in Docker

***

## 🛠️ Development

### Rebuild a single service (without restarting others)

```bash
docker compose build stock-service
docker compose up -d stock-service
```

### View logs

```bash
docker compose logs -f                    # all services
docker compose logs -f stock-service      # single service
docker compose logs sentiment-service --tail=50
```

### Stop everything

```bash
docker compose down          # stop containers
docker compose down -v       # stop + delete Redis data
```

### Test individual services

```bash
# Stock service health
curl http://localhost:8000/health

# Redis cache contents
curl http://localhost:8000/cache/info

# Sentiment analysis
curl http://localhost:8002/sentiment/AAPL
```

***

## 🔧 Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `port already allocated` | Redis running locally | `docker stop redis-local && docker rm redis-local` |
| `null` stock prices | Yahoo Finance blocking Docker IP | Mock fallback activates automatically |
| `Failed to connect to localhost:8001` | Wrong URL in API gateway | Use service names, not `localhost` |
| NumPy 2.x error | torch compiled with NumPy 1.x | Pin `numpy<2.0` in sentiment requirements |
| Sentiment service slow to start | FinBERT model downloading | Wait ~60s on first run |

***

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

***

## 👨‍💻 Author

Built as a full-stack microservices project demonstrating Docker, FastAPI, React, Redis, and AI/ML integration.
