import { useState } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import './index.css';

// ── API Gateway URL ───────────────────────────────────
const API = 'http://127.0.0.1:8088';

export default function App() {
  const [ticker, setTicker]       = useState('AAPL');
  const [inputVal, setInputVal]   = useState('AAPL');
  const [stockData, setStockData] = useState(null);
  const [history, setHistory]     = useState([]);
  const [sentiment, setSentiment] = useState(null);
  const [news, setNews]           = useState([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const quickTickers = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN'];

  // ── Fetch all data ──────────────────────────────────
  const fetchData = async (symbol) => {
    setLoading(true);
    setError(null);

    try {
      // Call all endpoints simultaneously
      const [dashRes, histRes] = await Promise.all([
        axios.get(`${API}/api/dashboard/${symbol}`),
        axios.get(`${API}/api/stock/${symbol}/history?period=1mo`)
      ]);

      const dash = dashRes.data;
      setStockData(dash.stock);
      setSentiment(dash.sentiment);
      setNews(dash.news?.headlines || []);

      // Format history for Recharts
      const formatted = (histRes.data.history || []).map(d => ({
        date: d.date.slice(5),    // show MM-DD only
        close: d.close
      }));
      setHistory(formatted);

    } catch (err) {
      setError('Failed to fetch data. Make sure all services are running!');
    } finally {
      setLoading(false);
    }
  };

  // ── On Search ───────────────────────────────────────
  const handleSearch = () => {
    const sym = inputVal.trim().toUpperCase();
    if (!sym) return;
    setTicker(sym);
    fetchData(sym);
  };

  // Fetch on first load
  useState(() => { fetchData('AAPL'); }, []);

  // ── Sentiment color helper ──────────────────────────
  const sentimentColor = (s) => {
    if (s === 'positive') return '#00d4aa';
    if (s === 'negative') return '#ff6b6b';
    return '#ffd93d';
  };

  const sentimentClass = (s) => {
    if (s === 'positive') return 'positive';
    if (s === 'negative') return 'negative';
    return 'neutral';
  };

  const formatValue = (value) => (
    typeof value === 'number' ? value.toFixed(2) : 'N/A'
  );

  const priceChange =
    stockData?.current_price != null && stockData?.previous_close != null
      ? stockData.current_price - stockData.previous_close
      : null;

  const priceChangePct =
    priceChange != null && stockData?.previous_close
      ? (priceChange / stockData.previous_close) * 100
      : null;

  const rawRangePct =
    stockData?.day_high != null &&
    stockData?.day_low != null &&
    stockData.day_high > stockData.day_low &&
    stockData.current_price != null
      ? (stockData.current_price - stockData.day_low) /
        (stockData.day_high - stockData.day_low)
      : null;

  const rangePct =
    rawRangePct != null ? Math.min(Math.max(rawRangePct, 0), 1) : null;

  const confidencePct =
    sentiment?.avg_confidence != null
      ? Math.round(sentiment.avg_confidence * 100)
      : null;

  const handleQuickTicker = (symbol) => {
    setInputVal(symbol);
    setTicker(symbol);
    fetchData(symbol);
  };

  return (
    <div className="app-shell">
      <div className="dashboard">
        <div className="topbar">
          <div className="brand">
            <div className="brand-mark">SB</div>
            <div>
              <div className="brand-title">SignalBoard</div>
              <div className="brand-subtitle">Market intelligence in one glance</div>
            </div>
          </div>
          <div className="status-pill">
            <span className="status-dot" />
            Live
          </div>
        </div>

        <div className="hero">
          <div className="hero-copy">
            <h1>Stock Dashboard</h1>
            <p>Track price action, AI sentiment, and news in one focused view.</p>
            <div className="hero-kpis">
              <div className="hero-kpi">
                <span className="kpi-label">Ticker</span>
                <span className="kpi-value">{ticker}</span>
              </div>
              <div className="hero-kpi">
                <span className="kpi-label">Exchange</span>
                <span className="kpi-value">{stockData?.exchange || '--'}</span>
              </div>
              <div className="hero-kpi">
                <span className="kpi-label">Currency</span>
                <span className="kpi-value">{stockData?.currency || '--'}</span>
              </div>
            </div>
          </div>

          <div className="search-panel">
            <div className="search-bar">
              <input
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                placeholder="e.g. AAPL, TSLA"
              />
              <button onClick={handleSearch}>Search</button>
            </div>
            <div className="quick-tickers">
              {quickTickers.map((symbol) => (
                <button
                  key={symbol}
                  className={`chip ${symbol === ticker ? 'active' : ''}`}
                  onClick={() => handleQuickTicker(symbol)}
                >
                  {symbol}
                </button>
              ))}
            </div>
            <div className="search-hint">Press Enter to search</div>
          </div>
        </div>

        {loading && <div className="loading">Loading {ticker} data...</div>}
        {error   && <div className="error-msg">{error}</div>}

        {stockData && !loading && (
          <>
            <div className="cards-grid">
              <div className="card card--primary">
                <div className="card-head">
                  <div className="label">Current Price</div>
                  {priceChange != null && priceChangePct != null && (
                    <div
                      className={`change-pill ${priceChange >= 0 ? 'trend-up' : 'trend-down'}`}
                    >
                      {`${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)} (${priceChangePct >= 0 ? '+' : ''}${priceChangePct.toFixed(2)}%)`}
                    </div>
                  )}
                </div>
                <div className="value">{formatValue(stockData.current_price)}</div>
                <div className="sub">Prev close {formatValue(stockData.previous_close)}</div>
                {rangePct != null && (
                  <div className="range-track">
                    <div className="range-label">Day range</div>
                    <div className="range-bar">
                      <div className="range-fill" style={{ width: `${rangePct * 100}%` }} />
                      <div className="range-marker" style={{ left: `${rangePct * 100}%` }} />
                    </div>
                    <div className="range-meta">
                      <span>{formatValue(stockData.day_low)}</span>
                      <span>{formatValue(stockData.day_high)}</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="card">
                <div className="label">Previous Close</div>
                <div className="value">{formatValue(stockData.previous_close)}</div>
                <div className="sub">{stockData.exchange}</div>
              </div>

              <div className="card">
                <div className="label">Day High</div>
                <div className="value positive">{formatValue(stockData.day_high)}</div>
              </div>

              <div className="card">
                <div className="label">Day Low</div>
                <div className="value negative">{formatValue(stockData.day_low)}</div>
              </div>

              {sentiment && (
                <div className="card">
                  <div className="label">AI Sentiment</div>
                  <div className={`value ${sentimentClass(sentiment.overall_sentiment)}`}>
                    {sentiment.overall_sentiment?.toUpperCase()}
                  </div>
                  <div className="sub">
                    Confidence: {(sentiment.avg_confidence * 100).toFixed(0)}%
                  </div>
                </div>
              )}
            </div>

            {history.length > 0 && (
              <div className="chart-card">
                <div className="chart-head">
                  <h2>{ticker} Price History</h2>
                  <span className="chart-meta">1 Month</span>
                </div>
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#9aa6b2', fontSize: 11 }}
                      interval={4}
                    />
                    <YAxis
                      tick={{ fill: '#9aa6b2', fontSize: 11 }}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#0f1726',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '12px',
                        color: '#e6f0ff'
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#23d3b2"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="bottom-grid">
              {sentiment && (
                <div className="sentiment-card">
                  <div className="sentiment-head">
                    <h2>AI Sentiment Analysis</h2>
                    {confidencePct != null && (
                      <div
                        className="confidence-ring"
                        style={{ '--confidence': confidencePct }}
                      >
                        <span>{confidencePct}%</span>
                      </div>
                    )}
                  </div>
                  <div
                    className="signal-badge"
                    style={{ color: sentimentColor(sentiment.overall_sentiment) }}
                  >
                    {sentiment.trading_signal}
                  </div>
                  <div className="sub">
                    Based on {sentiment.headlines_analysed} headlines - Source: {sentiment.data_source}
                  </div>
                  <div className="sentiment-bars">
                    {Object.entries(sentiment.sentiment_breakdown || {}).map(([label, count]) => (
                      <div className="bar-row" key={label}>
                        <span className="bar-label">{label}</span>
                        <div className="bar-fill-wrapper">
                          <div
                            className="bar-fill"
                            style={{
                              width: `${(count / sentiment.headlines_analysed) * 100}%`,
                              background: sentimentColor(label)
                            }}
                          />
                        </div>
                        <span className="bar-value">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="news-card">
                <h2>Latest News</h2>
                {news.length === 0
                  ? <p className="empty-state">No news available</p>
                  : news.map((item, i) => (
                    <div className="news-item" key={i}>
                      <div className="news-title">{item.title}</div>
                      <div className="news-meta">
                        {item.publisher} - {item.published}
                      </div>
                    </div>
                  ))
                }
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}