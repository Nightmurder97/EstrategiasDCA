# Plan Completo de Implementación - Agente IA Trading Autónomo 24/7

## 📋 Resumen Ejecutivo

Sistema completo de trading autónomo con IA que opera 24/7, analiza múltiples fuentes de datos, detecta oportunidades y envía alertas inteligentes.

**Stack Tecnológico:** Python/FastAPI + React + Apache Kafka + PostgreSQL + InfluxDB + Redis + Docker + AWS

---

## 🏗️ Estructura del Proyecto

```
trading-ai-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   └── database.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   └── middleware.py
│   │   ├── data_collectors/
│   │   │   ├── __init__.py
│   │   │   ├── base_collector.py
│   │   │   ├── market_data_collector.py
│   │   │   ├── news_collector.py
│   │   │   ├── social_collector.py
│   │   │   └── onchain_collector.py
│   │   ├── ai_engine/
│   │   │   ├── __init__.py
│   │   │   ├── price_predictor.py
│   │   │   ├── sentiment_analyzer.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── technical_analyzer.py
│   │   │   └── pattern_recognizer.py
│   │   ├── decision_engine/
│   │   │   ├── __init__.py
│   │   │   ├── decision_maker.py
│   │   │   ├── risk_manager.py
│   │   │   ├── position_manager.py
│   │   │   └── trading_rules.py
│   │   ├── alert_system/
│   │   │   ├── __init__.py
│   │   │   ├── alert_manager.py
│   │   │   ├── telegram_notifier.py
│   │   │   ├── discord_notifier.py
│   │   │   ├── email_notifier.py
│   │   │   └── sms_notifier.py
│   │   ├── report_generator/
│   │   │   ├── __init__.py
│   │   │   ├── report_manager.py
│   │   │   ├── chart_generator.py
│   │   │   └── templates/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── market_data.py
│   │   │   ├── opportunities.py
│   │   │   └── alerts.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── dashboard.py
│   │   │   │   │   ├── opportunities.py
│   │   │   │   │   └── system_status.py
│   │   │   │   └── api.py
│   │   │   └── websocket/
│   │   │       ├── __init__.py
│   │   │       └── connections.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── data_processor.py
│   │   │   ├── ml_service.py
│   │   │   └── scheduler.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── helpers.py
│   │       ├── constants.py
│   │       └── logger.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   ├── OpportunityList/
│   │   │   ├── SystemStatus/
│   │   │   └── Charts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── docker-compose.yml
│   ├── kafka/
│   ├── monitoring/
│   └── aws/
├── ml_models/
│   ├── price_prediction/
│   ├── sentiment_analysis/
│   └── anomaly_detection/
├── scripts/
│   ├── setup.sh
│   ├── deploy.sh
│   └── backup.sh
├── docs/
└── README.md
```

---

## 🔧 Configuraciones Base

### 1. Docker Compose - Infraestructura Completa

```yaml
# infrastructure/docker-compose.yml
version: '3.8'

services:
  # Apache Kafka Stack
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    hostname: zookeeper
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    hostname: kafka
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9101:9101"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_JMX_PORT: 9101
      KAFKA_JMX_HOSTNAME: localhost
    volumes:
      - kafka-data:/var/lib/kafka/data

  # Databases
  postgres:
    image: postgres:15
    container_name: postgres
    restart: always
    environment:
      POSTGRES_USER: trading_ai
      POSTGRES_PASSWORD: secure_password_123
      POSTGRES_DB: trading_ai_db
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  influxdb:
    image: influxdb:2.7
    container_name: influxdb
    restart: always
    ports:
      - "8086:8086"
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: secure_password_123
      DOCKER_INFLUXDB_INIT_ORG: trading_ai
      DOCKER_INFLUXDB_INIT_BUCKET: market_data
    volumes:
      - influxdb-data:/var/lib/influxdb2

  # Monitoring Stack
  grafana:
    image: grafana/grafana:10.0.0
    container_name: grafana
    restart: always
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin123
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning

  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  # Trading AI Backend
  trading-ai-backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: trading-ai-backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://trading_ai:secure_password_123@postgres:5432/trading_ai_db
      REDIS_URL: redis://redis:6379
      INFLUXDB_URL: http://influxdb:8086
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
    depends_on:
      - postgres
      - redis
      - influxdb
      - kafka
    volumes:
      - ./logs:/app/logs
      - ./ml_models:/app/ml_models

  # Trading AI Frontend
  trading-ai-frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: trading-ai-frontend
    restart: always
    ports:
      - "3001:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
      REACT_APP_WS_URL: ws://localhost:8000/ws
    depends_on:
      - trading-ai-backend

volumes:
  zookeeper-data:
  kafka-data:
  postgres-data:
  redis-data:
  influxdb-data:
  grafana-data:
  prometheus-data:

networks:
  default:
    name: trading-ai-network
```

### 2. Backend - Configuración Principal

```python
# backend/app/config/settings.py
from pydantic import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Trading AI Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database Settings
    DATABASE_URL: str = "postgresql://trading_ai:secure_password_123@localhost:5432/trading_ai_db"
    REDIS_URL: str = "redis://localhost:6379"
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = ""
    INFLUXDB_ORG: str = "trading_ai"
    INFLUXDB_BUCKET: str = "market_data"
    
    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    
    # API Keys
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    COINBASE_API_KEY: str = ""
    COINBASE_SECRET_KEY: str = ""
    COINMARKETCAP_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""
    
    # Notification Settings
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    DISCORD_WEBHOOK_URL: str = ""
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    ALERT_PHONE_NUMBER: str = ""
    
    # Trading Settings
    DEFAULT_SYMBOLS: List[str] = ["BTC", "ETH", "ADA", "SOL", "AVAX"]
    MIN_CONFIDENCE_THRESHOLD: float = 0.6
    MAX_RISK_LEVEL: float = 0.3
    POSITION_SIZE_PERCENTAGE: float = 0.02
    
    # AI Model Settings
    MODEL_UPDATE_INTERVAL: int = 3600  # seconds
    PREDICTION_TIMEFRAMES: List[str] = ["1h", "4h", "1d", "1w"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# backend/app/config/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from influxdb_client import InfluxDBClient
from .settings import settings

# PostgreSQL
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# InfluxDB
influx_client = InfluxDBClient(
    url=settings.INFLUXDB_URL,
    token=settings.INFLUXDB_TOKEN,
    org=settings.INFLUXDB_ORG
)
```

### 3. Main Backend Application

```python
# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import logging
from contextlib import asynccontextmanager

from .config.settings import settings
from .api.v1.api import api_router
from .services.scheduler import start_background_tasks
from .api.websocket.connections import ConnectionManager
from .utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# WebSocket connection manager
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Trading AI Agent...")
    
    # Start background tasks
    asyncio.create_task(start_background_tasks())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Trading AI Agent...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "app": settings.APP_NAME
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

### 4. Data Collectors

```python
# backend/app/data_collectors/base_collector.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import asyncio
import aiohttp
import time
import logging
from ..utils.helpers import exponential_backoff

logger = logging.getLogger(__name__)

@dataclass
class DataPoint:
    source: str
    symbol: str
    timestamp: float
    data_type: str
    content: Dict[str, Any]
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

class BaseCollector(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.error_count = 0
        self.max_errors = config.get('max_errors', 10)
        
    async def start(self):
        """Start the collector"""
        self.is_running = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self.get_headers()
        )
        
        logger.info(f"Starting {self.__class__.__name__}")
        
        while self.is_running:
            try:
                await self.collect_and_publish()
                await asyncio.sleep(self.config.get('interval', 60))
                self.error_count = 0  # Reset on successful run
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in {self.__class__.__name__}: {e}")
                
                if self.error_count >= self.max_errors:
                    logger.critical(f"{self.__class__.__name__} exceeded max errors, stopping")
                    break
                    
                # Exponential backoff on errors
                await asyncio.sleep(exponential_backoff(self.error_count))
    
    async def stop(self):
        """Stop the collector"""
        self.is_running = False
        if self.session:
            await self.session.close()
        logger.info(f"Stopped {self.__class__.__name__}")
    
    @abstractmethod
    async def collect_data(self) -> List[DataPoint]:
        """Collect data from source"""
        pass
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        pass
    
    async def collect_and_publish(self):
        """Collect data and publish to Kafka"""
        data_points = await self.collect_data()
        
        for data_point in data_points:
            await self.publish_data(data_point)
    
    async def publish_data(self, data_point: DataPoint):
        """Publish data point to Kafka"""
        from ..services.data_processor import publish_to_kafka
        await publish_to_kafka(data_point)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate collected data"""
        required_fields = self.config.get('required_fields', [])
        return all(field in data for field in required_fields)
```

```python
# backend/app/data_collectors/market_data_collector.py
import asyncio
import json
from typing import List, Dict, Any
import websocket
from .base_collector import BaseCollector, DataPoint
from ..config.settings import settings

class BinanceCollector(BaseCollector):
    def __init__(self):
        config = {
            'interval': 5,  # 5 seconds
            'symbols': settings.DEFAULT_SYMBOLS,
            'required_fields': ['symbol', 'price', 'volume']
        }
        super().__init__(config)
        self.websocket_url = "wss://stream.binance.com:9443/ws/!ticker@arr"
        self.ws = None
        
    def get_headers(self) -> Dict[str, str]:
        return {
            'X-MBX-APIKEY': settings.BINANCE_API_KEY,
            'User-Agent': 'Trading-AI-Agent/1.0'
        }
    
    async def collect_data(self) -> List[DataPoint]:
        """Collect real-time price data from Binance"""
        data_points = []
        
        try:
            # REST API call for current prices
            url = "https://api.binance.com/api/v3/ticker/24hr"
            async with self.session.get(url) as response:
                if response.status == 200:
                    tickers = await response.json()
                    
                    for ticker in tickers:
                        symbol = ticker['symbol']
                        if any(symbol.startswith(s) for s in self.config['symbols']):
                            data_point = DataPoint(
                                source="binance",
                                symbol=symbol,
                                timestamp=time.time(),
                                data_type="market_data",
                                content={
                                    'price': float(ticker['lastPrice']),
                                    'volume': float(ticker['volume']),
                                    'price_change_24h': float(ticker['priceChangePercent']),
                                    'high_24h': float(ticker['highPrice']),
                                    'low_24h': float(ticker['lowPrice']),
                                    'open_price': float(ticker['openPrice']),
                                    'close_price': float(ticker['lastPrice']),
                                    'bid_price': float(ticker.get('bidPrice', 0)),
                                    'ask_price': float(ticker.get('askPrice', 0)),
                                    'count': int(ticker['count'])
                                }
                            )
                            data_points.append(data_point)
                            
        except Exception as e:
            logger.error(f"Error collecting Binance data: {e}")
            
        return data_points

class CoinbaseCollector(BaseCollector):
    def __init__(self):
        config = {
            'interval': 10,  # 10 seconds
            'symbols': settings.DEFAULT_SYMBOLS
        }
        super().__init__(config)
        
    def get_headers(self) -> Dict[str, str]:
        return {
            'CB-ACCESS-KEY': settings.COINBASE_API_KEY,
            'User-Agent': 'Trading-AI-Agent/1.0'
        }
    
    async def collect_data(self) -> List[DataPoint]:
        """Collect data from Coinbase Pro"""
        data_points = []
        
        try:
            for symbol in self.config['symbols']:
                url = f"https://api.exchange.coinbase.com/products/{symbol}-USD/ticker"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        ticker = await response.json()
                        
                        data_point = DataPoint(
                            source="coinbase",
                            symbol=f"{symbol}USD",
                            timestamp=time.time(),
                            data_type="market_data",
                            content={
                                'price': float(ticker['price']),
                                'volume': float(ticker['volume']),
                                'bid_price': float(ticker['bid']),
                                'ask_price': float(ticker['ask']),
                                'size': float(ticker['size'])
                            }
                        )
                        data_points.append(data_point)
                        
        except Exception as e:
            logger.error(f"Error collecting Coinbase data: {e}")
            
        return data_points
```

```python
# backend/app/data_collectors/news_collector.py
import asyncio
from typing import List
from .base_collector import BaseCollector, DataPoint
from ..config.settings import settings
import time

class NewsAPICollector(BaseCollector):
    def __init__(self):
        config = {
            'interval': 300,  # 5 minutes
            'keywords': ['bitcoin', 'cryptocurrency', 'blockchain', 'ethereum', 'crypto']
        }
        super().__init__(config)
        
    def get_headers(self) -> Dict[str, str]:
        return {
            'X-API-Key': settings.NEWS_API_KEY,
            'User-Agent': 'Trading-AI-Agent/1.0'
        }
    
    async def collect_data(self) -> List[DataPoint]:
        """Collect crypto news from NewsAPI"""
        data_points = []
        
        try:
            for keyword in self.config['keywords']:
                url = f"https://newsapi.org/v2/everything"
                params = {
                    'q': keyword,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'from': time.strftime('%Y-%m-%d', time.gmtime(time.time() - 3600)),  # Last hour
                    'pageSize': 20
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        news_data = await response.json()
                        
                        for article in news_data.get('articles', []):
                            data_point = DataPoint(
                                source="newsapi",
                                symbol="CRYPTO",
                                timestamp=time.time(),
                                data_type="news",
                                content={
                                    'title': article['title'],
                                    'description': article['description'],
                                    'content': article.get('content', ''),
                                    'url': article['url'],
                                    'published_at': article['publishedAt'],
                                    'source_name': article['source']['name'],
                                    'keyword': keyword
                                }
                            )
                            data_points.append(data_point)
                            
        except Exception as e:
            logger.error(f"Error collecting news data: {e}")
            
        return data_points

class CoinDeskCollector(BaseCollector):
    def __init__(self):
        config = {
            'interval': 600,  # 10 minutes
        }
        super().__init__(config)
        
    def get_headers(self) -> Dict[str, str]:
        return {'User-Agent': 'Trading-AI-Agent/1.0'}
    
    async def collect_data(self) -> List[DataPoint]:
        """Collect news from CoinDesk RSS"""
        data_points = []
        
        try:
            import feedparser
            
            # CoinDesk RSS feed
            feed_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
            
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # Last 10 articles
                data_point = DataPoint(
                    source="coindesk",
                    symbol="CRYPTO",
                    timestamp=time.time(),
                    data_type="news",
                    content={
                        'title': entry.title,
                        'description': entry.summary,
                        'url': entry.link,
                        'published_at': entry.published,
                        'source_name': 'CoinDesk',
                        'tags': [tag.term for tag in entry.get('tags', [])]
                    }
                )
                data_points.append(data_point)
                
        except Exception as e:
            logger.error(f"Error collecting CoinDesk data: {e}")
            
        return data_points
```

```python
# backend/app/data_collectors/social_collector.py
import asyncio
from typing import List
import tweepy
from .base_collector import BaseCollector, DataPoint
from ..config.settings import settings
import time

class TwitterCollector(BaseCollector):
    def __init__(self):
        config = {
            'interval': 180,  # 3 minutes
            'keywords': ['#bitcoin', '#cryptocurrency', '#BTC', '#ETH', '#crypto'],
            'max_tweets': 50
        }
        super().__init__(config)
        
        # Initialize Twitter API
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=True
        )
        
    def get_headers(self) -> Dict[str, str]:
        return {'Authorization': f'Bearer {settings.TWITTER_BEARER_TOKEN}'}
    
    async def collect_data(self) -> List[DataPoint]:
        """Collect tweets about crypto"""
        data_points = []
        
        try:
            for keyword in self.config['keywords']:
                # Search recent tweets
                tweets = self.client.search_recent_tweets(
                    query=f"{keyword} -is:retweet lang:en",
                    max_results=self.config['max_tweets'],
                    tweet_fields=['created_at', 'public_metrics', 'context_annotations']
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        data_point = DataPoint(
                            source="twitter",
                            symbol="CRYPTO",
                            timestamp=time.time(),
                            data_type="social",
                            content={
                                'text': tweet.text,
                                'created_at': tweet.created_at.isoformat(),
                                'retweet_count': tweet.public_metrics['retweet_count'],
                                'like_count': tweet.public_metrics['like_count'],
                                'reply_count': tweet.public_metrics['reply_count'],
                                'quote_count': tweet.public_metrics['quote_count'],
                                'keyword': keyword,
                                'tweet_id': tweet.id
                            }
                        )
                        data_points.append(data_point)
                        
        except Exception as e:
            logger.error(f"Error collecting Twitter data: {e}")
            
        return data_points

class RedditCollector(BaseCollector):
    def __init__(self):
        config = {
            'interval': 300,  # 5 minutes
            'subreddits': ['cryptocurrency', 'bitcoin', 'ethereum', 'cryptomarkets'],
            'limit': 25
        }
        super().__init__(config)
        
    def get_headers(self) -> Dict[str, str]:
        return {'User-Agent': 'Trading-AI-Agent/1.0'}
    
    async def collect_data(self) -> List[DataPoint]:
        """Collect posts from crypto subreddits"""
        data_points = []
        
        try:
            for subreddit in self.config['subreddits']:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                params = {'limit': self.config['limit']}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        reddit_data = await response.json()
                        
                        for post in reddit_data['data']['children']:
                            post_data = post['data']
                            
                            data_point = DataPoint(
                                source="reddit",
                                symbol="CRYPTO",
                                timestamp=time.time(),
                                data_type="social",
                                content={
                                    'title': post_data['title'],
                                    'selftext': post_data['selftext'],
                                    'score': post_data['score'],
                                    'upvote_ratio': post_data['upvote_ratio'],
                                    'num_comments': post_data['num_comments'],
                                    'created_utc': post_data['created_utc'],
                                    'subreddit': subreddit,
                                    'url': post_data['url'],
                                    'permalink': f"https://reddit.com{post_data['permalink']}"
                                }
                            )
                            data_points.append(data_point)
                            
        except Exception as e:
            logger.error(f"Error collecting Reddit data: {e}")
            
        return data_points
```

### 5. AI Engine

```python
# backend/app/ai_engine/price_predictor.py
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import logging
from typing import Dict, List, Tuple, Optional
import asyncio

logger = logging.getLogger(__name__)

class LSTMPricePredictor:
    def __init__(self, sequence_length: int = 60, features: int = 5):
        self.sequence_length = sequence_length
        self.features = features
        self.model: Optional[tf.keras.Model] = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        
    def build_model(self) -> tf.keras.Model:
        """Build LSTM model architecture"""
        model = tf.keras.Sequential([
            # First LSTM layer
            tf.keras.layers.LSTM(
                128,
                return_sequences=True,
                input_shape=(self.sequence_length, self.features),
                dropout=0.2
            ),
            tf.keras.layers.BatchNormalization(),
            
            # Second LSTM layer
            tf.keras.layers.LSTM(
                128,
                return_sequences=True,
                dropout=0.2
            ),
            tf.keras.layers.BatchNormalization(),
            
            # Third LSTM layer
            tf.keras.layers.LSTM(
                64,
                return_sequences=False,
                dropout=0.2
            ),
            tf.keras.layers.BatchNormalization(),
            
            # Dense layers
            tf.keras.layers.Dense(50, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(25, activation='relu'),
            tf.keras.layers.Dense(1)  # Price prediction
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='huber',  # Robust to outliers
            metrics=['mae', 'mse']
        )
        
        return model
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training"""
        # Feature engineering
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['rsi'] = self.calculate_rsi(df['close'])
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['ma_50'] = df['close'].rolling(window=50).mean()
        
        # Select features
        features = ['close', 'volume', 'volatility', 'rsi', 'returns']
        feature_data = df[features].dropna()
        
        # Scale features
        scaled_data = self.scaler.fit_transform(feature_data)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i])
            y.append(scaled_data[i, 0])  # Predict close price
            
        return np.array(X), np.array(y)
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    async def train(self, df: pd.DataFrame, validation_split: float = 0.2) -> Dict:
        """Train the LSTM model"""
        logger.info("Starting LSTM model training...")
        
        try:
            # Prepare data
            X, y = self.prepare_data(df)
            
            # Split data
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Build model
            self.model = self.build_model()
            
            # Callbacks
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7
                )
            ]
            
            # Train model
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=100,
                batch_size=32,
                callbacks=callbacks,
                verbose=0
            )
            
            # Evaluate
            train_pred = self.model.predict(X_train)
            val_pred = self.model.predict(X_val)
            
            train_mae = mean_absolute_error(y_train, train_pred)
            val_mae = mean_absolute_error(y_val, val_pred)
            
            self.is_trained = True
            
            logger.info(f"Model training completed. Train MAE: {train_mae:.4f}, Val MAE: {val_mae:.4f}")
            
            return {
                'train_mae': train_mae,
                'val_mae': val_mae,
                'history': history.history,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def predict(self, recent_data: pd.DataFrame, steps_ahead: int = 1) -> Dict:
        """Make price predictions"""
        if not self.is_trained or self.model is None:
            return {'error': 'Model not trained'}
        
        try:
            # Prepare recent data
            features = ['close', 'volume', 'volatility', 'rsi', 'returns']
            feature_data = recent_data[features].tail(self.sequence_length)
            
            # Scale data
            scaled_data = self.scaler.transform(feature_data)
            
            # Reshape for prediction
            X = scaled_data.reshape(1, self.sequence_length, self.features)
            
            predictions = []
            current_sequence = X.copy()
            
            for _ in range(steps_ahead):
                # Predict next value
                pred = self.model.predict(current_sequence, verbose=0)
                predictions.append(pred[0, 0])
                
                # Update sequence for multi-step prediction
                if steps_ahead > 1:
                    new_row = np.zeros((1, 1, self.features))
                    new_row[0, 0, 0] = pred[0, 0]  # Use prediction as next close price
                    # For other features, use last known values (simple approach)
                    new_row[0, 0, 1:] = current_sequence[0, -1, 1:]
                    
                    current_sequence = np.concatenate([
                        current_sequence[:, 1:, :],
                        new_row
                    ], axis=1)
            
            # Inverse transform predictions
            dummy_array = np.zeros((len(predictions), self.features))
            dummy_array[:, 0] = predictions
            inverse_predictions = self.scaler.inverse_transform(dummy_array)[:, 0]
            
            # Calculate confidence based on recent model performance
            confidence = self.calculate_confidence(recent_data)
            
            return {
                'predictions': inverse_predictions.tolist(),
                'confidence': confidence,
                'timeframes': [f"{i+1}h" for i in range(steps_ahead)],
                'model_type': 'LSTM',
                'features_used': features
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {'error': str(e)}
    
    def calculate_confidence(self, recent_data: pd.DataFrame) -> float:
        """Calculate prediction confidence based on recent volatility and model performance"""
        try:
            # Calculate recent volatility
            recent_volatility = recent_data['close'].pct_change().tail(24).std()
            
            # Normalize volatility (0-1 scale, inverse relationship with confidence)
            volatility_factor = max(0, 1 - (recent_volatility * 10))
            
            # Base confidence (can be improved with more sophisticated metrics)
            base_confidence = 0.7
            
            # Combine factors
            confidence = base_confidence * volatility_factor
            return max(0.1, min(1.0, confidence))
            
        except Exception:
            return 0.5  # Default confidence
    
    def save_model(self, filepath: str):
        """Save model and scaler"""
        if self.model:
            self.model.save(f"{filepath}_model.h5")
            joblib.dump(self.scaler, f"{filepath}_scaler.pkl")
            logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load model and scaler"""
        try:
            self.model = tf.keras.models.load_model(f"{filepath}_model.h5")
            self.scaler = joblib.load(f"{filepath}_scaler.pkl")
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")

class EnsemblePricePredictor:
    """Ensemble of multiple prediction models"""
    
    def __init__(self):
        self.models = {
            'lstm': LSTMPricePredictor(),
            'linear': None,  # Can add linear regression
            'xgboost': None  # Can add XGBoost
        }
        self.weights = {'lstm': 0.6, 'linear': 0.2, 'xgboost': 0.2}
    
    async def predict(self, recent_data: pd.DataFrame) -> Dict:
        """Make ensemble predictions"""
        predictions = {}
        total_weight = 0
        weighted_prediction = 0
        
        for model_name, model in self.models.items():
            if model and hasattr(model, 'predict'):
                result = await model.predict(recent_data)
                if 'predictions' in result:
                    predictions[model_name] = result
                    weight = self.weights[model_name]
                    weighted_prediction += result['predictions'][0] * weight
                    total_weight += weight
        
        if total_weight > 0:
            final_prediction = weighted_prediction / total_weight
            avg_confidence = np.mean([p['confidence'] for p in predictions.values()])
            
            return {
                'prediction': final_prediction,
                'confidence': avg_confidence,
                'individual_predictions': predictions,
                'ensemble_weights': self.weights
            }
        
        return {'error': 'No models available for prediction'}
```

```python
# backend/app/ai_engine/sentiment_analyzer.py
import asyncio
import numpy as np
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, List, Optional
import logging
import re
from collections import defaultdict
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import yfinance as yf

logger = logging.getLogger(__name__)

class CryptoSentimentAnalyzer:
    def __init__(self):
        self.finbert_analyzer = None
        self.vader_analyzer = None
        self.crypto_keywords = {
            'bullish': ['moon', 'bull', 'bullish', 'pump', 'rocket', 'hodl', 'buy', 'long', 'rally'],
            'bearish': ['bear', 'bearish', 'dump', 'crash', 'sell', 'short', 'drop', 'fall'],
            'neutral': ['hold', 'wait', 'watch', 'analyze', 'study']
        }
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize sentiment analysis models"""
        try:
            # Load FinBERT for financial sentiment
            self.finbert_analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Load VADER for social media sentiment
            nltk.download('vader_lexicon', quiet=True)
            self.vader_analyzer = SentimentIntensityAnalyzer()
            
            logger.info("Sentiment analysis models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing sentiment models: {e}")
    
    async def analyze_text_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of a single text"""
        try:
            results = {}
            
            # FinBERT analysis (for financial context)
            if self.finbert_analyzer:
                finbert_result = self.finbert_analyzer(text[:512])  # Truncate for model limit
                results['finbert'] = {
                    'label': finbert_result[0]['label'],
                    'score': finbert_result[0]['score']
                }
            
            # VADER analysis (for social media context)
            if self.vader_analyzer:
                vader_scores = self.vader_analyzer.polarity_scores(text)
                results['vader'] = vader_scores
            
            # Crypto-specific keyword analysis
            crypto_sentiment = self.analyze_crypto_keywords(text)
            results['crypto_keywords'] = crypto_sentiment
            
            # Combined sentiment score
            combined_score = self.combine_sentiment_scores(results)
            results['combined'] = combined_score
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing text sentiment: {e}")
            return {'error': str(e)}
    
    def analyze_crypto_keywords(self, text: str) -> Dict:
        """Analyze crypto-specific keywords"""
        text_lower = text.lower()
        
        scores = {
            'bullish': 0,
            'bearish': 0,
            'neutral': 0
        }
        
        for sentiment, keywords in self.crypto_keywords.items():
            for keyword in keywords:
                scores[sentiment] += text_lower.count(keyword)
        
        total_keywords = sum(scores.values())
        if total_keywords == 0:
            return {'sentiment': 'neutral', 'score': 0.0, 'keyword_counts': scores}
        
        # Calculate dominant sentiment
        dominant_sentiment = max(scores, key=scores.get)
        confidence = scores[dominant_sentiment] / total_keywords
        
        return {
            'sentiment': dominant_sentiment,
            'score': confidence,
            'keyword_counts': scores
        }
    
    def combine_sentiment_scores(self, sentiment_results: Dict) -> Dict:
        """Combine different sentiment analysis results"""
        weights = {
            'finbert': 0.4,
            'vader': 0.3,
            'crypto_keywords': 0.3
        }
        
        weighted_score = 0
        total_weight = 0
        sentiment_label = 'neutral'
        
        # FinBERT contribution
        if 'finbert' in sentiment_results:
            finbert = sentiment_results['finbert']
            score = finbert['score'] if finbert['label'] in ['positive', 'bullish'] else -finbert['score']
            weighted_score += score * weights['finbert']
            total_weight += weights['finbert']
        
        # VADER contribution
        if 'vader' in sentiment_results:
            vader_score = sentiment_results['vader']['compound']
            weighted_score += vader_score * weights['vader']
            total_weight += weights['vader']
        
        # Crypto keywords contribution
        if 'crypto_keywords' in sentiment_results:
            crypto = sentiment_results['crypto_keywords']
            if crypto['sentiment'] == 'bullish':
                score = crypto['score']
            elif crypto['sentiment'] == 'bearish':
                score = -crypto['score']
            else:
                score = 0
            weighted_score += score * weights['crypto_keywords']
            total_weight += weights['crypto_keywords']
        
        if total_weight > 0:
            final_score = weighted_score / total_weight
            
            # Determine sentiment label
            if final_score > 0.1:
                sentiment_label = 'bullish'
            elif final_score < -0.1:
                sentiment_label = 'bearish'
            else:
                sentiment_label = 'neutral'
        else:
            final_score = 0
        
        return {
            'score': final_score,
            'label': sentiment_label,
            'confidence': abs(final_score)
        }
    
    async def analyze_batch_sentiment(self, texts: List[str]) -> Dict:
        """Analyze sentiment for a batch of texts"""
        results = []
        
        for text in texts:
            sentiment = await self.analyze_text_sentiment(text)
            results.append(sentiment)
        
        # Aggregate results
        return self.aggregate_sentiment_results(results)
    
    def aggregate_sentiment_results(self, results: List[Dict]) -> Dict:
        """Aggregate multiple sentiment analysis results"""
        if not results:
            return {'error': 'No results to aggregate'}
        
        valid_results = [r for r in results if 'error' not in r and 'combined' in r]
        
        if not valid_results:
            return {'error': 'No valid results found'}
        
        # Calculate aggregated metrics
        scores = [r['combined']['score'] for r in valid_results]
        sentiments = [r['combined']['label'] for r in valid_results]
        
        avg_score = np.mean(scores)
        median_score = np.median(scores)
        std_score = np.std(scores)
        
        # Count sentiment labels
        sentiment_counts = defaultdict(int)
        for sentiment in sentiments:
            sentiment_counts[sentiment] += 1
        
        # Determine overall sentiment
        dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        sentiment_distribution = {k: v/len(sentiments) for k, v in sentiment_counts.items()}
        
        return {
            'overall_sentiment': dominant_sentiment,
            'average_score': avg_score,
            'median_score': median_score,
            'score_volatility': std_score,
            'sentiment_distribution': sentiment_distribution,
            'total_analyzed': len(valid_results),
            'time_period': '1h',  # Can be made dynamic
            'confidence': min(1.0, len(valid_results) / 100)  # More data = higher confidence
        }
    
    async def analyze_social_sentiment(self, social_data: List[Dict]) -> Dict:
        """Analyze sentiment from social media data"""
        texts = []
        weights = []
        
        for item in social_data:
            text = item.get('content', {}).get('text', '')
            if text:
                texts.append(text)
                
                # Weight by engagement (likes, retweets, etc.)
                engagement = (
                    item.get('content', {}).get('like_count', 0) +
                    item.get('content', {}).get('retweet_count', 0) * 2 +
                    item.get('content', {}).get('reply_count', 0)
                )
                weights.append(max(1, engagement))  # Minimum weight of 1
        
        if not texts:
            return {'error': 'No social data to analyze'}
        
        # Analyze sentiment for all texts
        sentiment_results = []
        for i, text in enumerate(texts):
            result = await self.analyze_text_sentiment(text)
            if 'combined' in result:
                result['weight'] = weights[i]
                sentiment_results.append(result)
        
        # Calculate weighted average
        if sentiment_results:
            weighted_scores = []
            total_weight = sum(r['weight'] for r in sentiment_results)
            
            for result in sentiment_results:
                weight_factor = result['weight'] / total_weight
                weighted_scores.append(result['combined']['score'] * weight_factor)
            
            weighted_avg_score = sum(weighted_scores)
            
            # Determine weighted sentiment
            if weighted_avg_score > 0.1:
                overall_sentiment = 'bullish'
            elif weighted_avg_score < -0.1:
                overall_sentiment = 'bearish'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'overall_sentiment': overall_sentiment,
                'weighted_score': weighted_avg_score,
                'total_posts': len(sentiment_results),
                'confidence': min(1.0, len(sentiment_results) / 50),
                'source': 'social_media'
            }
        
        return {'error': 'No valid sentiment results'}
    
    async def analyze_news_sentiment(self, news_data: List[Dict]) -> Dict:
        """Analyze sentiment from news articles"""
        texts = []
        
        for article in news_data:
            content = article.get('content', {})
            # Combine title and description for better context
            text = f"{content.get('title', '')} {content.get('description', '')}"
            if text.strip():
                texts.append(text.strip())
        
        if not texts:
            return {'error': 'No news data to analyze'}
        
        # Analyze sentiment
        results = await self.analyze_batch_sentiment(texts)
        results['source'] = 'news'
        
        return results
    
    def calculate_sentiment_trend(self, historical_sentiment: List[Dict]) -> Dict:
        """Calculate sentiment trend over time"""
        if len(historical_sentiment) < 2:
            return {'trend': 'insufficient_data'}
        
        scores = [item['score'] for item in historical_sentiment if 'score' in item]
        
        if len(scores) < 2:
            return {'trend': 'insufficient_data'}
        
        # Calculate trend direction
        recent_avg = np.mean(scores[-3:])  # Last 3 data points
        older_avg = np.mean(scores[-6:-3]) if len(scores) >= 6 else np.mean(scores[:-3])
        
        trend_change = recent_avg - older_avg
        
        if trend_change > 0.05:
            trend = 'improving'
        elif trend_change < -0.05:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_magnitude': abs(trend_change),
            'recent_average': recent_avg,
            'older_average': older_avg
        }
```

### 6. Decision Engine

```python
# backend/app/decision_engine/decision_maker.py
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta

from .risk_manager import RiskManager
from .trading_rules import TradingRulesEngine
from ..models.opportunities import TradingOpportunity, OpportunityType
from ..ai_engine.price_predictor import EnsemblePricePredictor
from ..ai_engine.sentiment_analyzer import CryptoSentimentAnalyzer
from ..ai_engine.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class DecisionFactors:
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    momentum_score: float
    risk_score: float
    volume_score: float
    volatility_score: float

class DecisionEngine:
    def __init__(self):
        self.risk_manager = RiskManager()
        self.trading_rules = TradingRulesEngine()
        self.price_predictor = EnsemblePricePredictor()
        self.sentiment_analyzer = CryptoSentimentAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        
        # Decision weights (can be optimized over time)
        self.weights = {
            'technical': 0.25,
            'fundamental': 0.20,
            'sentiment': 0.20,
            'momentum': 0.15,
            'risk': 0.10,
            'volume': 0.10
        }
        
        # Thresholds
        self.thresholds = {
            'strong_buy': 0.80,
            'buy': 0.60,
            'hold': 0.40,
            'sell': -0.60,
            'strong_sell': -0.80,
            'min_confidence': 0.50
        }
    
    async def evaluate_opportunity(
        self, 
        symbol: str, 
        market_data: Dict, 
        sentiment_data: Dict, 
        news_data: Dict,
        social_data: Dict
    ) -> Optional[TradingOpportunity]:
        """Main decision evaluation function"""
        
        try:
            logger.info(f"Evaluating opportunity for {symbol}")
            
            # Calculate decision factors
            factors = await self.calculate_decision_factors(
                symbol, market_data, sentiment_data, news_data, social_data
            )
            
            # Calculate overall score
            overall_score = self.calculate_weighted_score(factors)
            
            # Apply trading rules
            decision = await self.apply_trading_rules(symbol, factors, overall_score)
            
            if decision:
                # Risk management validation
                if await self.risk_manager.validate_opportunity(decision):
                    logger.info(f"Opportunity validated for {symbol}: {decision.opportunity_type}")
                    return decision
                else:
                    logger.info(f"Opportunity rejected by risk manager for {symbol}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating opportunity for {symbol}: {e}")
            return None
    
    async def calculate_decision_factors(
        self, 
        symbol: str, 
        market_data: Dict, 
        sentiment_data: Dict, 
        news_data: Dict,
        social_data: Dict
    ) -> DecisionFactors:
        """Calculate all decision factors"""
        
        # Technical Analysis Score
        technical_score = await self.calculate_technical_score(symbol, market_data)
        
        # Fundamental Analysis Score
        fundamental_score = await self.calculate_fundamental_score(symbol, market_data)
        
        # Sentiment Score
        sentiment_score = await self.calculate_sentiment_score(sentiment_data, news_data, social_data)
        
        # Momentum Score
        momentum_score = await self.calculate_momentum_score(symbol, market_data)
        
        # Risk Score
        risk_score = await self.calculate_risk_score(symbol, market_data)
        
        # Volume Score
        volume_score = await self.calculate_volume_score(symbol, market_data)
        
        # Volatility Score
        volatility_score = await self.calculate_volatility_score(symbol, market_data)
        
        return DecisionFactors(
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            sentiment_score=sentiment_score,
            momentum_score=momentum_score,
            risk_score=risk_score,
            volume_score=volume_score,
            volatility_score=volatility_score
        )
    
    async def calculate_technical_score(self, symbol: str, market_data: Dict) -> float:
        """Calculate technical analysis score"""
        try:
            # Get recent price data
            df = await self.get_price_dataframe(symbol, market_data)
            
            if df.empty:
                return 0.0
            
            # Technical indicators
            indicators = await self.technical_analyzer.calculate_indicators(df)
            
            score = 0.0
            total_weight = 0.0
            
            # RSI Score (30-70 range is neutral, outside indicates strong signals)
            if 'rsi' in indicators:
                rsi = indicators['rsi'].iloc[-1]
                if rsi < 30:  # Oversold - bullish
                    rsi_score = (30 - rsi) / 30
                elif rsi > 70:  # Overbought - bearish
                    rsi_score = -(rsi - 70) / 30
                else:  # Neutral zone
                    rsi_score = 0
                score += rsi_score * 0.3
                total_weight += 0.3
            
            # MACD Score
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd'].iloc[-1]
                macd_signal = indicators['macd_signal'].iloc[-1]
                macd_score = 1.0 if macd > macd_signal else -1.0
                score += macd_score * 0.25
                total_weight += 0.25
            
            # Bollinger Bands Score
            if all(k in indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
                current_price = df['close'].iloc[-1]
                bb_upper = indicators['bb_upper'].iloc[-1]
                bb_lower = indicators['bb_lower'].iloc[-1]
                bb_middle = indicators['bb_middle'].iloc[-1]
                
                if current_price < bb_lower:  # Oversold
                    bb_score = 0.8
                elif current_price > bb_upper:  # Overbought
                    bb_score = -0.8
                elif current_price > bb_middle:  # Above middle
                    bb_score = 0.3
                else:  # Below middle
                    bb_score = -0.3
                
                score += bb_score * 0.2
                total_weight += 0.2
            
            # Moving Average Score
            if 'sma_20' in indicators and 'sma_50' in indicators:
                sma_20 = indicators['sma_20'].iloc[-1]
                sma_50 = indicators['sma_50'].iloc[-1]
                current_price = df['close'].iloc[-1]
                
                ma_score = 0
                if current_price > sma_20 > sma_50:  # Strong uptrend
                    ma_score = 0.8
                elif current_price > sma_20 and current_price > sma_50:  # Uptrend
                    ma_score = 0.4
                elif current_price < sma_20 < sma_50:  # Strong downtrend
                    ma_score = -0.8
                elif current_price < sma_20 and current_price < sma_50:  # Downtrend
                    ma_score = -0.4
                
                score += ma_score * 0.25
                total_weight += 0.25
            
            return score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating technical score for {symbol}: {e}")
            return 0.0
    
    async def calculate_fundamental_score(self, symbol: str, market_data: Dict) -> float:
        """Calculate fundamental analysis score"""
        try:
            score = 0.0
            total_weight = 0.0
            
            # Market Cap Analysis
            market_cap = market_data.get('market_cap', 0)
            if market_cap > 0:
                # Prefer mid to large cap (more stable)
                if market_cap > 10_000_000_000:  # >10B - large cap
                    mc_score = 0.3
                elif market_cap > 1_000_000_000:  # >1B - mid cap
                    mc_score = 0.5
                elif market_cap > 100_000_000:  # >100M - small cap
                    mc_score = 0.2
                else:  # <100M - micro cap (risky)
                    mc_score = -0.2
                
                score += mc_score * 0.2
                total_weight += 0.2
            
            # Volume Analysis
            volume_24h = market_data.get('volume_24h', 0)
            if volume_24h > 0 and market_cap > 0:
                volume_ratio = volume_24h / market_cap
                if volume_ratio > 0.1:  # High liquidity
                    vol_score = 0.5
                elif volume_ratio > 0.05:  # Good liquidity
                    vol_score = 0.3
                elif volume_ratio > 0.01:  # Moderate liquidity
                    vol_score = 0.1
                else:  # Low liquidity
                    vol_score = -0.3
                
                score += vol_score * 0.3
                total_weight += 0.3
            
            # Price Performance Analysis
            price_change_24h = market_data.get('price_change_24h', 0)
            price_change_7d = market_data.get('price_change_7d', 0)
            
            # Short-term momentum
            if abs(price_change_24h) < 5:  # Stable
                perf_score = 0.2
            elif price_change_24h > 10:  # Strong gain (might be overbought)
                perf_score = -0.1
            elif price_change_24h < -10:  # Strong loss (might be oversold)
                perf_score = 0.3
            else:
                perf_score = price_change_24h / 100  # Normalize
            
            score += perf_score * 0.3
            total_weight += 0.3
            
            # Network Activity (if available)
            active_addresses = market_data.get('active_addresses', 0)
            if active_addresses > 0:
                # This would need historical comparison
                network_score = 0.1  # Placeholder
                score += network_score * 0.2
                total_weight += 0.2
            
            return score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score for {symbol}: {e}")
            return 0.0
    
    async def calculate_sentiment_score(self, sentiment_data: Dict, news_data: Dict, social_data: Dict) -> float:
        """Calculate sentiment score"""
        try:
            total_score = 0.0
            total_weight = 0.0
            
            # News sentiment
            if news_data and 'overall_sentiment' in news_data:
                news_sentiment = news_data['overall_sentiment']
                news_score_value = news_data.get('average_score', 0)
                
                if news_sentiment == 'bullish':
                    news_score = news_score_value
                elif news_sentiment == 'bearish':
                    news_score = -abs(news_score_value)
                else:
                    news_score = 0
                
                weight = news_data.get('confidence', 0.5)
                total_score += news_score * weight * 0.6
                total_weight += weight * 0.6
            
            # Social media sentiment
            if social_data and 'overall_sentiment' in social_data:
                social_sentiment = social_data['overall_sentiment']
                social_score_value = social_data.get('weighted_score', 0)
                
                if social_sentiment == 'bullish':
                    social_score = social_score_value
                elif social_sentiment == 'bearish':
                    social_score = -abs(social_score_value)
                else:
                    social_score = 0
                
                weight = social_data.get('confidence', 0.5)
                total_score += social_score * weight * 0.4
                total_weight += weight * 0.4
            
            return total_score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0
    
    async def calculate_momentum_score(self, symbol: str, market_data: Dict) -> float:
        """Calculate momentum score"""
        try:
            score = 0.0
            
            # Price momentum
            price_change_1h = market_data.get('price_change_1h', 0)
            price_change_24h = market_data.get('price_change_24h', 0)
            price_change_7d = market_data.get('price_change_7d', 0)
            
            # Weight recent changes more heavily
            momentum = (
                price_change_1h * 0.5 +
                price_change_24h * 0.3 +
                price_change_7d * 0.2
            ) / 100  # Normalize to decimal
            
            # Volume momentum
            volume_24h = market_data.get('volume_24h', 0)
            volume_avg = market_data.get('volume_avg_7d', volume_24h)
            
            if volume_avg > 0:
                volume_momentum = (volume_24h - volume_avg) / volume_avg
                momentum += volume_momentum * 0.3
            
            # Cap momentum score
            return max(-1.0, min(1.0, momentum))
            
        except Exception as e:
            logger.error(f"Error calculating momentum score for {symbol}: {e}")
            return 0.0
    
    async def calculate_risk_score(self, symbol: str, market_data: Dict) -> float:
        """Calculate risk score (lower is better)"""
        try:
            risk_factors = []
            
            # Volatility risk
            volatility = market_data.get('volatility_24h', 0)
            if volatility > 0:
                vol_risk = min(1.0, volatility / 50)  # Normalize high volatility
                risk_factors.append(vol_risk)
            
            # Liquidity risk
            volume_24h = market_data.get('volume_24h', 0)
            market_cap = market_data.get('market_cap', 1)
            if market_cap > 0:
                liquidity_ratio = volume_24h / market_cap
                liquidity_risk = max(0, 1 - liquidity_ratio * 20)  # Lower volume = higher risk
                risk_factors.append(liquidity_risk)
            
            # Market cap risk (smaller = riskier)
            if market_cap > 0:
                if market_cap < 100_000_000:  # <100M
                    cap_risk = 0.8
                elif market_cap < 1_000_000_000:  # <1B
                    cap_risk = 0.5
                elif market_cap < 10_000_000_000:  # <10B
                    cap_risk = 0.3
                else:
                    cap_risk = 0.1
                risk_factors.append(cap_risk)
            
            # Average risk (inverted so lower risk = higher score)
            avg_risk = np.mean(risk_factors) if risk_factors else 0.5
            return 1.0 - avg_risk
            
        except Exception as e:
            logger.error(f"Error calculating risk score for {symbol}: {e}")
            return 0.5
    
    async def calculate_volume_score(self, symbol: str, market_data: Dict) -> float:
        """Calculate volume score"""
        try:
            volume_24h = market_data.get('volume_24h', 0)
            volume_avg_7d = market_data.get('volume_avg_7d', volume_24h)
            
            if volume_avg_7d > 0:
                volume_ratio = volume_24h / volume_avg_7d
                
                if volume_ratio > 2.0:  # Very high volume
                    return 0.8
                elif volume_ratio > 1.5:  # High volume
                    return 0.5
                elif volume_ratio > 0.8:  # Normal volume
                    return 0.2
                else:  # Low volume
                    return -0.3
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating volume score for {symbol}: {e}")
            return 0.0
    
    async def calculate_volatility_score(self, symbol: str, market_data: Dict) -> float:
        """Calculate volatility score"""
        try:
            volatility = market_data.get('volatility_24h', 0)
            
            # Moderate volatility is preferred (opportunity without excessive risk)
            if 5 <= volatility <= 15:  # Sweet spot
                return 0.5
            elif volatility < 5:  # Too stable
                return 0.1
            elif volatility > 30:  # Too volatile
                return -0.5
            else:  # Acceptable volatility
                return 0.3
            
        except Exception as e:
            logger.error(f"Error calculating volatility score for {symbol}: {e}")
            return 0.0
    
    def calculate_weighted_score(self, factors: DecisionFactors) -> float:
        """Calculate weighted overall score"""
        score = (
            factors.technical_score * self.weights['technical'] +
            factors.fundamental_score * self.weights['fundamental'] +
            factors.sentiment_score * self.weights['sentiment'] +
            factors.momentum_score * self.weights['momentum'] +
            factors.risk_score * self.weights['risk'] +
            factors.volume_score * self.weights['volume']
        )
        
        return max(-1.0, min(1.0, score))
    
    async def apply_trading_rules(
        self, 
        symbol: str, 
        factors: DecisionFactors, 
        overall_score: float
    ) -> Optional[TradingOpportunity]:
        """Apply trading rules to generate opportunity"""
        
        # Determine opportunity type based on score
        if overall_score >= self.thresholds['strong_buy']:
            opportunity_type = OpportunityType.STRONG_BUY
        elif overall_score >= self.thresholds['buy']:
            opportunity_type = OpportunityType.BUY
        elif overall_score <= self.thresholds['strong_sell']:
            opportunity_type = OpportunityType.STRONG_SELL
        elif overall_score <= self.thresholds['sell']:
            opportunity_type = OpportunityType.SELL
        else:
            return None  # No clear signal
        
        # Calculate confidence
        confidence = min(1.0, abs(overall_score))
        
        if confidence < self.thresholds['min_confidence']:
            return None
        
        # Generate reasoning
        reasoning = self.generate_reasoning(factors, overall_score)
        
        # Calculate expected return and timeframe
        expected_return = self.estimate_expected_return(overall_score, factors)
        timeframe = self.determine_timeframe(factors)
        
        return TradingOpportunity(
            symbol=symbol,
            opportunity_type=opportunity_type,
            confidence=confidence,
            expected_return=expected_return,
            risk_level=1.0 - factors.risk_score,
            timeframe=timeframe,
            reasoning=reasoning,
            supporting_data={
                'technical_score': factors.technical_score,
                'fundamental_score': factors.fundamental_score,
                'sentiment_score': factors.sentiment_score,
                'momentum_score': factors.momentum_score,
                'risk_score': factors.risk_score,
                'overall_score': overall_score
            },
            timestamp=datetime.utcnow().timestamp()
        )
    
    def generate_reasoning(self, factors: DecisionFactors, overall_score: float) -> List[str]:
        """Generate human-readable reasoning"""
        reasoning = []
        
        # Technical reasoning
        if factors.technical_score > 0.3:
            reasoning.append("Technical indicators showing bullish signals")
        elif factors.technical_score < -0.3:
            reasoning.append("Technical indicators showing bearish signals")
        
        # Sentiment reasoning
        if factors.sentiment_score > 0.3:
            reasoning.append("Positive market sentiment detected")
        elif factors.sentiment_score < -0.3:
            reasoning.append("Negative market sentiment detected")
        
        # Momentum reasoning
        if factors.momentum_score > 0.3:
            reasoning.append("Strong upward momentum observed")
        elif factors.momentum_score < -0.3:
            reasoning.append("Strong downward momentum observed")
        
        # Volume reasoning
        if factors.volume_score > 0.3:
            reasoning.append("Above-average trading volume confirms move")
        
        # Risk reasoning
        if factors.risk_score > 0.7:
            reasoning.append("Risk-reward ratio is favorable")
        elif factors.risk_score < 0.3:
            reasoning.append("High risk detected - proceed with caution")
        
        # Overall confidence
        if abs(overall_score) > 0.8:
            reasoning.append("High confidence signal based on multiple factors")
        
        return reasoning if reasoning else ["Signal based on algorithmic analysis"]
    
    def estimate_expected_return(self, overall_score: float, factors: DecisionFactors) -> float:
        """Estimate expected return percentage"""
        base_return = abs(overall_score) * 10  # Base 10% for perfect score
        
        # Adjust for momentum
        momentum_multiplier = 1 + (factors.momentum_score * 0.5)
        
        # Adjust for volatility (higher volatility = higher potential return)
        volatility_multiplier = 1 + (factors.volatility_score * 0.3)
        
        expected_return = base_return * momentum_multiplier * volatility_multiplier
        
        # Cap at reasonable levels
        return max(0.02, min(0.50, expected_return))  # 2% to 50%
    
    def determine_timeframe(self, factors: DecisionFactors) -> str:
        """Determine recommended timeframe"""
        if factors.momentum_score > 0.5:
            return "1-4 hours"  # Strong momentum = short term
        elif factors.technical_score > 0.5:
            return "1-3 days"  # Technical signals = medium term
        elif factors.fundamental_score > 0.5:
            return "1-2 weeks"  # Fundamental = longer term
        else:
            return "1-2 days"  # Default
    
    async def get_price_dataframe(self, symbol: str, market_data: Dict) -> pd.DataFrame:
        """Get price data as pandas DataFrame"""
        # This would typically fetch from database
        # For now, return a simple DataFrame
        current_price = market_data.get('price', 0)
        
        if current_price == 0:
            return pd.DataFrame()
        
        # Create mock historical data (in real implementation, fetch from DB)
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1H')
        prices = np.random.normal(current_price, current_price * 0.02, 100)
        volumes = np.random.normal(1000000, 200000, 100)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices * np.random.normal(1, 0.01, 100),
            'high': prices * np.random.normal(1.01, 0.01, 100),
            'low': prices * np.random.normal(0.99, 0.01, 100),
            'close': prices,
            'volume': volumes
        })
        
        return df.set_index('timestamp')
```

### 7. Alert System

```python
# backend/app/alert_system/alert_manager.py
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from .telegram_notifier import TelegramNotifier
from .discord_notifier import DiscordNotifier
from .email_notifier import EmailNotifier
from .sms_notifier import SMSNotifier
from ..models.opportunities import TradingOpportunity
from ..config.settings import settings

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self.notifiers = {}
        self.alert_history = []
        self.rate_limits = {
            'telegram': {'count': 0, 'window_start': datetime.now(), 'limit': 50},
            'discord': {'count': 0, 'window_start': datetime.now(), 'limit': 100},
            'email': {'count': 0, 'window_start': datetime.now(), 'limit': 20},
            'sms': {'count': 0, 'window_start': datetime.now(), 'limit': 5}
        }
        
        self.initialize_notifiers()
    
    def initialize_notifiers(self):
        """Initialize all notification channels"""
        try:
            # Telegram
            if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                self.notifiers['telegram'] = TelegramNotifier(
                    bot_token=settings.TELEGRAM_BOT_TOKEN,
                    chat_id=settings.TELEGRAM_CHAT_ID
                )
                logger.info("Telegram notifier initialized")
            
            # Discord
            if settings.DISCORD_WEBHOOK_URL:
                self.notifiers['discord'] = DiscordNotifier(
                    webhook_url=settings.DISCORD_WEBHOOK_URL
                )
                logger.info("Discord notifier initialized")
            
            # Email
            if settings.SMTP_SERVER and settings.SMTP_USERNAME:
                self.notifiers['email'] = EmailNotifier(
                    smtp_server=settings.SMTP_SERVER,
                    smtp_port=settings.SMTP_PORT,
                    username=settings.SMTP_USERNAME,
                    password=settings.SMTP_PASSWORD
                )
                logger.info("Email notifier initialized")
            
            # SMS
            if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                self.notifiers['sms'] = SMSNotifier(
                    account_sid=settings.TWILIO_ACCOUNT_SID,
                    auth_token=settings.TWILIO_AUTH_TOKEN,
                    from_number=settings.TWILIO_PHONE_NUMBER
                )
                logger.info("SMS notifier initialized")
                
        except Exception as e:
            logger.error(f"Error initializing notifiers: {e}")
    
    async def send_opportunity_alert(self, opportunity: TradingOpportunity) -> Dict:
        """Send alert for trading opportunity"""
        try:
            # Determine alert priority
            priority = self.determine_alert_priority(opportunity)
            
            # Check for duplicate alerts
            if self.is_duplicate_alert(opportunity):
                logger.info(f"Skipping duplicate alert for {opportunity.symbol}")
                return {'status': 'skipped', 'reason': 'duplicate'}
            
            # Determine which channels to use
            channels = self.get_alert_channels(priority, opportunity)
            
            # Send alerts
            results = {}
            alert_tasks = []
            
            for channel in channels:
                if channel in self.notifiers and self.check_rate_limit(channel):
                    task = self.send_to_channel(channel, opportunity)
                    alert_tasks.append((channel, task))
            
            # Execute all alert tasks
            for channel, task in alert_tasks:
                try:
                    result = await task
                    results[channel] = result
                    self.update_rate_limit(channel)
                except Exception as e:
                    logger.error(f"Error sending alert to {channel}: {e}")
                    results[channel] = {'status': 'error', 'message': str(e)}
            
            # Log alert
            self.log_alert(opportunity, results)
            
            return {
                'status': 'sent',
                'channels': results,
                'opportunity_id': f"{opportunity.symbol}_{int(opportunity.timestamp)}"
            }
            
        except Exception as e:
            logger.error(f"Error sending opportunity alert: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def determine_alert_priority(self, opportunity: TradingOpportunity) -> str:
        """Determine alert priority based on opportunity characteristics"""
        if opportunity.confidence >= 0.9 and abs(opportunity.expected_return) >= 0.15:
            return 'critical'
        elif opportunity.confidence >= 0.8 and abs(opportunity.expected_return) >= 0.10:
            return 'high'
        elif opportunity.confidence >= 0.7 and abs(opportunity.expected_return) >= 0.05:
            return 'medium'
        else:
            return 'low'
    
    def get_alert_channels(self, priority: str, opportunity: TradingOpportunity) -> List[str]:
        """Determine which channels to use based on priority"""
        channels = []
        
        if priority == 'critical':
            channels = ['telegram', 'discord', 'email', 'sms']
        elif priority == 'high':
            channels = ['telegram', 'discord', 'email']
        elif priority == 'medium':
            channels = ['telegram', 'discord']
        else:  # low
            channels = ['telegram']
        
        # Filter by what's actually configured
        return [ch for ch in channels if ch in self.notifiers]
    
    def check_rate_limit(self, channel: str) -> bool:
        """Check if channel is within rate limits"""
        if channel not in self.rate_limits:
            return True
        
        rate_info = self.rate_limits[channel]
        now = datetime.now()
        
        # Reset counter if window has passed (1 hour windows)
        if now - rate_info['window_start'] > timedelta(hours=1):
            rate_info['count'] = 0
            rate_info['window_start'] = now
        
        return rate_info['count'] < rate_info['limit']
    
    def update_rate_limit(self, channel: str):
        """Update rate limit counter"""
        if channel in self.rate_limits:
            self.rate_limits[channel]['count'] += 1
    
    def is_duplicate_alert(self, opportunity: TradingOpportunity) -> bool:
        """Check if this is a duplicate alert"""
        recent_threshold = datetime.now() - timedelta(minutes=30)
        
        for alert in self.alert_history:
            if (alert['symbol'] == opportunity.symbol and
                alert['opportunity_type'] == opportunity.opportunity_type and
                alert['timestamp'] > recent_threshold):
                return True
        
        return False
    
    async def send_to_channel(self, channel: str, opportunity: TradingOpportunity) -> Dict:
        """Send alert to specific channel"""
        notifier = self.notifiers[channel]
        
        if channel == 'sms':
            # SMS gets shortened message
            message = self.format_sms_message(opportunity)
        else:
            message = self.format_full_message(opportunity)
        
        return await notifier.send_alert(message, opportunity)
    
    def format_full_message(self, opportunity: TradingOpportunity) -> str:
        """Format full alert message"""
        emoji = self.get_emoji(opportunity.opportunity_type)
        confidence_bar = "█" * int(opportunity.confidence * 10)
        
        message = f"""
{emoji} **TRADING OPPORTUNITY DETECTED** {emoji}

**Symbol**: {opportunity.symbol}
**Signal**: {opportunity.opportunity_type.value}
**Confidence**: {confidence_bar} {opportunity.confidence:.1%}
**Expected Return**: {opportunity.expected_return:.1%}
**Risk Level**: {self.format_risk_level(opportunity.risk_level)}
**Timeframe**: {opportunity.timeframe}

**Analysis Summary**:
{chr(10).join(f"• {reason}" for reason in opportunity.reasoning[:5])}

**Supporting Data**:
• Technical Score: {opportunity.supporting_data.get('technical_score', 0):.2f}
• Sentiment Score: {opportunity.supporting_data.get('sentiment_score', 0):.2f}
• Momentum Score: {opportunity.supporting_data.get('momentum_score', 0):.2f}

**Generated**: {datetime.fromtimestamp(opportunity.timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')}

⚠️ **This is not financial advice. Always do your own research.**
        """
        
        return message.strip()
    
    def format_sms_message(self, opportunity: TradingOpportunity) -> str:
        """Format shortened SMS message"""
        return f"""
🚨 CRYPTO ALERT 🚨
{opportunity.symbol}: {opportunity.opportunity_type.value}
Confidence: {opportunity.confidence:.0%}
Return: {opportunity.expected_return:.1%}
Risk: {self.format_risk_level(opportunity.risk_level)}
Time: {opportunity.timeframe}
        """.strip()
    
    def get_emoji(self, opportunity_type) -> str:
        """Get emoji for opportunity type"""
        from ..models.opportunities import OpportunityType
        
        emoji_map = {
            OpportunityType.STRONG_BUY: "🚀",
            OpportunityType.BUY: "📈",
            OpportunityType.SELL: "📉",
            OpportunityType.STRONG_SELL: "⚠️",
            OpportunityType.HOLD: "⏸️"
        }
        
        return emoji_map.get(opportunity_type, "📊")
    
    def format_risk_level(self, risk_level: float) -> str:
        """Format risk level as text"""
        if risk_level < 0.2:
            return "🟢 Low"
        elif risk_level < 0.5:
            return "🟡 Medium"
        elif risk_level < 0.8:
            return "🟠 High"
        else:
            return "🔴 Very High"
    
    def log_alert(self, opportunity: TradingOpportunity, results: Dict):
        """Log alert to history"""
        self.alert_history.append({
            'symbol': opportunity.symbol,
            'opportunity_type': opportunity.opportunity_type,
            'timestamp': datetime.now(),
            'confidence': opportunity.confidence,
            'channels_sent': list(results.keys()),
            'results': results
        })
        
        # Keep only last 1000 alerts in memory
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    async def send_system_alert(self, message: str, alert_type: str = 'info') -> Dict:
        """Send system status alert"""
        try:
            if alert_type == 'critical':
                channels = ['telegram', 'email', 'sms']
            elif alert_type == 'warning':
                channels = ['telegram', 'email']
            else:
                channels = ['telegram']
            
            results = {}
            for channel in channels:
                if channel in self.notifiers and self.check_rate_limit(channel):
                    try:
                        notifier = self.notifiers[channel]
                        result = await notifier.send_system_message(message)
                        results[channel] = result
                        self.update_rate_limit(channel)
                    except Exception as e:
                        logger.error(f"Error sending system alert to {channel}: {e}")
                        results[channel] = {'status': 'error', 'message': str(e)}
            
            return {'status': 'sent', 'channels': results}
            
        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def test_all_channels(self) -> Dict