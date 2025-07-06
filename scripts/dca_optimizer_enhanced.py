import os
from dotenv import load_dotenv
import re
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import json
from binance.client import Client
import warnings
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.gridspec as gridspec
import traceback
warnings.filterwarnings('ignore')

# Configurar el estilo de matplotlib
plt.style.use('default')  # Usar estilo default en lugar de seaborn
sns.set_theme()  # Aplicar tema de seaborn de forma segura

# Configurar para mostrar caracteres en español
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = [12, 8]  # Tamaño predeterminado de figuras
plt.rcParams['figure.dpi'] = 100  # DPI predeterminado

# Configurar logging con más detalles
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno al inicio
load_dotenv('config/.env')

@dataclass
class OptimizationConfig:
    """Configuración para la optimización del portafolio"""
    def __init__(self):
        # Pesos para diferentes métricas
        self.weight_sharpe = 0.20
        self.weight_volume = 0.15
        self.weight_momentum = 0.15
        self.weight_return = 0.15
        self.weight_volatility = 0.15
        self.weight_market_cap = 0.10
        self.weight_liquidity = 0.10
        
        # Límites del portafolio
        self.min_assets = 5
        self.max_assets = 15
        
        # Criterios mínimos
        self.min_market_cap = 100_000  # 100k USD
        self.min_volume_24h = 10_000   # 10k USD
        self.correlation_threshold = 0.7
        
        # Parámetros financieros
        self.risk_free_rate = 0.02  # 2% anual

class EnhancedDCAOptimizer:
    def __init__(self, data_dir: str = 'data/historical'):
        self.data_dir = data_dir
        self.config = OptimizationConfig()
        self.historical_data = {}
        self.metadata = {}
        self.correlation_matrix = pd.DataFrame()
        
        # Configurar fechas
        self.end_date = datetime(2025, 1, 6)  # Fecha actual fija
        self.start_date = self.end_date - timedelta(days=180)  # 6 meses de datos
        
        # Cargar símbolos del archivo
        self.symbols = self._load_symbols_from_file()
        if not self.symbols:
            logger.error("No se pudieron cargar los símbolos. Usando lista predeterminada.")
            self.symbols = [
                'BTCUSDT', 'ETHUSDT', 'XRPUSDT'  # Lista reducida como fallback
            ]
        
        # Cargar datos históricos desde múltiples fuentes
        logger.info(f"Cargando datos históricos desde {self.start_date.strftime('%Y-%m-%d')} hasta {self.end_date.strftime('%Y-%m-%d')}")
        self._load_historical_data()
        self.correlation_matrix = self._calculate_correlation_matrix()

    def _load_symbols_from_file(self) -> List[str]:
        """Carga los símbolos de las 500 principales criptomonedas"""
        try:
            with open('data/500topcriptomonedas.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            symbols = []
            stablecoins = ['USDT', 'USDC', 'DAI', 'TUSD', 'USDD', 'FDUSD', 'PYUSD', 'USDB', 'USDP']
            seen_symbols = set()  # Para evitar duplicados
            
            # Buscar líneas que contienen el número de ranking y el símbolo
            pattern = r'^\d+\s+[A-Z0-9]+\s+logo\s+[^\n]+\s+([A-Z0-9]+)\s*$'
            matches = re.finditer(pattern, content, re.MULTILINE)
            
            for match in matches:
                symbol = match.group(1)
                if symbol not in stablecoins and symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    symbols.append(f"{symbol}USDT")
            
            logger.info(f"Se cargaron {len(symbols)} símbolos del archivo")
            logger.info(f"Primeros 10 símbolos: {symbols[:10]}")
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error cargando símbolos del archivo: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _load_historical_data(self):
        """Carga datos históricos desde múltiples fuentes"""
        try:
            # 1. Intentar primero con Binance
            self._load_from_binance()
            
            # 2. Para los símbolos que faltan, intentar con CoinGecko
            missing_symbols = [s for s in self.symbols if s not in self.historical_data]
            if missing_symbols:
                logger.info(f"Intentando cargar {len(missing_symbols)} símbolos desde CoinGecko")
                self._load_from_coingecko(missing_symbols)
            
            # 3. Para los que aún faltan, intentar con LiveCoinWatch
            missing_symbols = [s for s in self.symbols if s not in self.historical_data]
            if missing_symbols:
                logger.info(f"Intentando cargar {len(missing_symbols)} símbolos desde LiveCoinWatch")
                self._load_from_livecoinwatch(missing_symbols)
            
            num_loaded = len(self.historical_data)
            logger.info(f"Total de datos históricos cargados: {num_loaded} criptomonedas")
            logger.info(f"- Binance: {self._count_by_source('binance')}")
            logger.info(f"- CoinGecko: {self._count_by_source('coingecko')}")
            logger.info(f"- LiveCoinWatch: {self._count_by_source('livecoinwatch')}")
            
        except Exception as e:
            logger.error(f"Error cargando datos históricos: {str(e)}")

    def _load_from_binance(self):
        """Carga datos históricos desde Binance"""
        try:
            # Configurar cliente de Binance con credenciales
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            self.client = Client(api_key, api_secret)
            
            # Obtener información de todos los símbolos disponibles en Binance
            exchange_info = self.client.get_exchange_info()
            valid_symbols = {s['symbol'] for s in exchange_info['symbols']}
            
            for symbol in tqdm(self.symbols, desc="Cargando desde Binance"):
                try:
                    # Verificar si el símbolo existe en Binance
                    if symbol not in valid_symbols:
                        logger.debug(f"Símbolo {symbol} no disponible en Binance")
                        continue
                    
                    # Obtener klines (velas) de Binance
                    klines = self.client.get_historical_klines(
                        symbol,
                        Client.KLINE_INTERVAL_1DAY,
                        self.start_date.strftime("%d %b %Y %H:%M:%S"),
                        self.end_date.strftime("%d %b %Y %H:%M:%S")
                    )
                    
                    if not klines:
                        logger.warning(f"No hay datos históricos para {symbol}")
                        continue
                    
                    # Convertir a DataFrame
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])
                    
                    # Convertir tipos de datos
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Verificar datos válidos
                    if df['close'].isnull().all() or df['volume'].isnull().all():
                        logger.warning(f"Datos inválidos para {symbol}")
                        continue
                    
                    # Guardar solo los datos necesarios
                    self.historical_data[symbol] = pd.DataFrame({
                        'close': df['close'],
                        'volume': df['volume']
                    })
                    
                    # Obtener información del ticker para metadatos más precisos
                    ticker = self.client.get_ticker(symbol=symbol)
                    
                    # Guardar metadatos
                    self.metadata[symbol] = {
                        'market_cap': float(ticker['quoteVolume']) * float(ticker['lastPrice']),
                        'volume_24h': float(ticker['volume']),
                        'price': float(ticker['lastPrice']),
                        'rank': self.symbols.index(symbol) + 1,
                        'data_source': 'binance'
                    }
                    
                    logger.info(f"Datos cargados de Binance para {symbol}")
                    time.sleep(0.1)  # Respetar límites de rate
                    
                except Exception as e:
                    logger.warning(f"Error con Binance para {symbol}: {str(e)}")
                    continue
            
            num_loaded = len(self.historical_data)
            logger.info(f"Datos cargados de Binance: {num_loaded} criptomonedas")
            
        except Exception as e:
            logger.error(f"Error en la conexión con Binance: {str(e)}")
            traceback.print_exc()

    def _load_from_livecoinwatch(self, symbols: List[str]):
        """Carga datos desde LiveCoinWatch"""
        api_key = os.getenv('LIVECOINWATCH_API_KEY')
        if not api_key:
            logger.error("No se encontró API key de LiveCoinWatch")
            return
        
        base_url = "https://api.livecoinwatch.com/coins/single/history"
        headers = {
            'x-api-key': api_key,
            'content-type': 'application/json'
        }
        
        for symbol in tqdm(symbols, desc="Cargando desde LiveCoinWatch"):
            try:
                clean_symbol = symbol.replace("USDT", "")
                payload = json.dumps({
                    "currency": "USD",
                    "code": clean_symbol,
                    "start": int(self.start_date.timestamp() * 1000),
                    "end": int(self.end_date.timestamp() * 1000),
                    "meta": True
                })
                
                response = requests.post(base_url, headers=headers, data=payload)
                
                if response.status_code == 429:
                    logger.warning("Rate limit alcanzado, esperando 60s...")
                    time.sleep(60)
                    response = requests.post(base_url, headers=headers, data=payload)
                    
                if response.status_code != 200:
                    continue
                
                data = response.json()
                if 'history' in data:
                    df = pd.DataFrame(data['history'])
                    df['timestamp'] = pd.to_datetime(df['date'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    self.historical_data[symbol] = pd.DataFrame({
                        'close': df['rate'],
                        'volume': df['volume']
                    })
                    
                    self.metadata[symbol] = {
                        'market_cap': data.get('cap', 0),
                        'volume_24h': data.get('volume', 0),
                        'price': data.get('rate', 0),
                        'rank': data.get('rank', 999),
                        'data_source': 'livecoinwatch'
                    }
                    
                    logger.info(f"Datos cargados de LiveCoinWatch para {symbol}")
                
                time.sleep(1)  # Respetar límites de rate
                
            except Exception as e:
                logger.warning(f"Error con LiveCoinWatch para {symbol}: {str(e)}")

    def _load_from_coingecko(self, symbols: List[str]):
        """Carga datos desde CoinGecko"""
        for symbol in tqdm(symbols, desc="Cargando desde CoinGecko"):
            try:
                # Convertir símbolo a formato CoinGecko
                clean_symbol = symbol.replace("USDT", "").lower()
                
                # Obtener metadatos primero
                url = f"https://api.coingecko.com/api/v3/coins/{clean_symbol}"
                response = requests.get(url)
                if response.status_code != 200:
                    continue
                
                meta = response.json()
                
                # Guardar metadatos antes de obtener datos históricos
                self.metadata[symbol] = {
                    'market_cap': meta['market_data']['market_cap']['usd'],
                    'volume_24h': meta['market_data']['total_volume']['usd'],
                    'price': meta['market_data']['current_price']['usd'],
                    'rank': meta['market_cap_rank'] or 999,
                    'data_source': 'coingecko'
                }
                
                # Obtener datos históricos
                url = f"https://api.coingecko.com/api/v3/coins/{clean_symbol}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': '180',
                    'interval': 'daily'
                }
                
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    del self.metadata[symbol]  # Eliminar metadatos si no hay datos históricos
                    continue
                
                data = response.json()
                
                # Convertir a DataFrame
                prices_df = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
                volumes_df = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
                
                df = prices_df.merge(volumes_df, on='timestamp')
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                self.historical_data[symbol] = df
                
                logger.info(f"Datos cargados de CoinGecko para {symbol}")
                time.sleep(1.5)  # Respetar límites de rate
                
            except Exception as e:
                logger.warning(f"Error con CoinGecko para {symbol}: {str(e)}")
                if symbol in self.metadata:
                    del self.metadata[symbol]  # Limpiar metadatos en caso de error

    def _count_by_source(self, source: str) -> int:
        """Cuenta cuántos símbolos se cargaron de cada fuente"""
        return sum(1 for meta in self.metadata.values() if meta['data_source'] == source)

    def _calculate_correlation_matrix(self) -> pd.DataFrame:
        """Calcula la matriz de correlación entre los activos"""
        # Crear un diccionario para almacenar los retornos
        returns_data = {}
        
        for symbol, data in self.historical_data.items():
            returns = data['close'].pct_change().dropna()
            returns_data[symbol] = returns
        
        # Crear DataFrame de una sola vez para evitar fragmentación
        returns_df = pd.DataFrame(returns_data)
        
        # Si no hay datos suficientes, retornar una matriz vacía
        if returns_df.empty:
            logger.warning("No hay suficientes datos para calcular correlaciones")
            return pd.DataFrame()
        
        # Calcular matriz de correlación
        correlation_matrix = returns_df.corr(method='pearson')
        
        return correlation_matrix

    def calculate_asset_metrics(self) -> pd.DataFrame:
        """Calcula métricas para cada activo"""
        metrics = []
        
        for symbol, data in self.historical_data.items():
            try:
                # Calcular retornos y volatilidad
                returns = data['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)
                
                # Evitar división por cero en el cálculo del retorno
                initial_price = data['close'].iloc[0]
                if initial_price == 0:
                    price_return = 0
                else:
                    price_return = (data['close'].iloc[-1] - initial_price) / initial_price
                
                # Calcular Sharpe Ratio (usando tasa libre de riesgo = 0 para simplicidad)
                excess_returns = returns - 0
                if len(excess_returns) > 0 and excess_returns.std() != 0:
                    sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
                else:
                    sharpe = 0
                
                # Calcular Sortino Ratio
                negative_returns = returns[returns < 0]
                if len(negative_returns) > 0 and negative_returns.std() != 0:
                    sortino = np.sqrt(252) * returns.mean() / negative_returns.std()
                else:
                    sortino = 0
                
                # Calcular momentum
                if len(data) >= 30:
                    price_30d = data['close'].iloc[-30]
                    momentum_1m = 0 if price_30d == 0 else (data['close'].iloc[-1] - price_30d) / price_30d
                else:
                    momentum_1m = 0
                
                if len(data) >= 90:
                    price_90d = data['close'].iloc[-90]
                    momentum_3m = 0 if price_90d == 0 else (data['close'].iloc[-1] - price_90d) / price_90d
                else:
                    momentum_3m = 0
                
                # Calcular máximo drawdown
                rolling_max = data['close'].expanding().max()
                drawdowns = (data['close'] - rolling_max) / rolling_max
                max_drawdown = drawdowns.min()
                
                # Obtener volumen promedio y market cap
                avg_volume = data['volume'].mean()
                market_cap = self.metadata.get(symbol, {}).get('market_cap', 0)
                volume_24h = self.metadata.get(symbol, {}).get('volume_24h', 0)
                rank = self.metadata.get(symbol, {}).get('rank', 999)
                
                # Calcular ratio de liquidez
                if avg_volume == 0:
                    liquidity_ratio = 0
                else:
                    liquidity_ratio = volume_24h / avg_volume
                
                metrics.append({
                    'symbol': symbol,
                    'price_return': price_return,
                    'volatility': volatility,
                    'sharpe': sharpe,
                    'sortino': sortino,
                    'momentum_1m': momentum_1m,
                    'momentum_3m': momentum_3m,
                    'max_drawdown': max_drawdown,
                    'avg_volume': avg_volume,
                    'market_cap': market_cap,
                    'volume_24h': volume_24h,
                    'rank': rank,
                    'liquidity_ratio': liquidity_ratio
                })
            
            except Exception as e:
                logger.warning(f"Error calculando métricas para {symbol}: {str(e)}")
                continue
        
        metrics_df = pd.DataFrame(metrics)
        if metrics_df.empty:
            logger.warning("No se pudieron calcular métricas para ningún activo")
            return pd.DataFrame()
        
        metrics_df.set_index('symbol', inplace=True)
        
        # Normalizar métricas
        metrics_to_normalize = [
            'price_return', 'volatility', 'sharpe', 'sortino',
            'momentum_1m', 'momentum_3m', 'avg_volume', 'market_cap',
            'volume_24h', 'liquidity_ratio'
        ]
        
        for metric in metrics_to_normalize:
            if metric in metrics_df.columns:
                min_val = metrics_df[metric].min()
                max_val = metrics_df[metric].max()
                if max_val != min_val:
                    metrics_df[metric] = (metrics_df[metric] - min_val) / (max_val - min_val)
                else:
                    metrics_df[metric] = 0
        
        # Invertir volatilidad normalizada (menor es mejor)
        if 'volatility' in metrics_df.columns:
            metrics_df['volatility'] = 1 - metrics_df['volatility']
        
        # Calcular score total
        metrics_df['total_score'] = (
            self.config.weight_return * metrics_df['price_return'] +
            self.config.weight_volatility * metrics_df['volatility'] +
            self.config.weight_sharpe * metrics_df['sharpe'] +
            self.config.weight_momentum * (
                0.6 * metrics_df['momentum_1m'] +
                0.4 * metrics_df['momentum_3m']
            ) +
            self.config.weight_volume * metrics_df['avg_volume'] +
            self.config.weight_market_cap * metrics_df['market_cap'] +
            self.config.weight_liquidity * metrics_df['liquidity_ratio']
        )
        
        # Normalizar score total
        min_score = metrics_df['total_score'].min()
        max_score = metrics_df['total_score'].max()
        if max_score != min_score:
            metrics_df['total_score'] = (metrics_df['total_score'] - min_score) / (max_score - min_score)
        
        return metrics_df

    def optimize_portfolio(self, weekly_investment: float) -> Tuple[Dict, pd.DataFrame]:
        """Optimiza el portafolio DCA"""
        try:
            # Calcular métricas para cada activo
            metrics_df = self.calculate_asset_metrics()
            
            # Filtrar activos que cumplen criterios mínimos y tienen metadatos válidos
            valid_assets = []
            for symbol in metrics_df.index:
                try:
                    metadata = self.metadata.get(symbol, {})
                    if not metadata:
                        logger.warning(f"No hay metadatos para {symbol}")
                        continue
                        
                    market_cap = metadata.get('market_cap', 0)
                    volume_24h = metadata.get('volume_24h', 0)
                    
                    if market_cap >= self.config.min_market_cap and volume_24h >= self.config.min_volume_24h:
                        valid_assets.append(symbol)
                    else:
                        logger.debug(f"{symbol} no cumple criterios mínimos: MC={market_cap}, Vol={volume_24h}")
                        
                except Exception as e:
                    logger.warning(f"Error validando {symbol}: {str(e)}")
                    continue
            
            if not valid_assets:
                logger.warning("No hay activos que cumplan con los criterios mínimos")
                return {}, pd.DataFrame()
            
            metrics_df = metrics_df.loc[valid_assets]
            
            # Ordenar por score total
            sorted_assets = metrics_df.sort_values('total_score', ascending=False)
            
            # Seleccionar activos considerando correlación
            selected_assets = []
            for symbol in sorted_assets.index:
                if len(selected_assets) >= self.config.max_assets:
                    break
                
                # Si no hay matriz de correlación, agregar el activo
                if self.correlation_matrix.empty:
                    selected_assets.append(symbol)
                    continue
                
                # Verificar correlación con activos ya seleccionados
                add_asset = True
                for selected in selected_assets:
                    if symbol in self.correlation_matrix.index and selected in self.correlation_matrix.columns:
                        if abs(self.correlation_matrix.loc[symbol, selected]) > self.config.correlation_threshold:
                            add_asset = False
                            break
                
                if add_asset:
                    selected_assets.append(symbol)
            
            # Asegurar mínimo de activos
            if len(selected_assets) < self.config.min_assets:
                remaining = [s for s in sorted_assets.index if s not in selected_assets]
                selected_assets.extend(remaining[:self.config.min_assets - len(selected_assets)])
            
            # Calcular pesos óptimos
            selected_metrics = metrics_df.loc[selected_assets]
            weights = selected_metrics['total_score'] / selected_metrics['total_score'].sum()
            
            # Calcular métricas del portafolio
            portfolio_metrics = self.calculate_portfolio_metrics(weekly_investment, dict(weights))
            
            return portfolio_metrics, metrics_df
            
        except Exception as e:
            logger.error(f"Error en la optimización: {str(e)}")
            traceback.print_exc()
            return {}, pd.DataFrame()

    def calculate_portfolio_metrics(self, weekly_investment: float, weights: Dict[str, float]) -> Dict:
        """Calcula métricas para el portafolio completo"""
        if not weights:
            return {}
        
        # Normalizar pesos
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        # Calcular retornos del portafolio
        portfolio_returns = pd.Series(0, index=self.historical_data[list(weights.keys())[0]].index)
        for symbol, weight in weights.items():
            returns = self.historical_data[symbol]['close'].pct_change()
            portfolio_returns += returns * weight
        
        # Calcular métricas
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe = self._calculate_sharpe_ratio(portfolio_returns)
        sortino = self._calculate_sortino_ratio(portfolio_returns)
        
        # Calcular drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # Calcular ROI total
        total_return = 0
        for symbol, weight in weights.items():
            initial_price = self.historical_data[symbol]['close'].iloc[0]
            final_price = self.historical_data[symbol]['close'].iloc[-1]
            symbol_return = (final_price - initial_price) / initial_price
            total_return += symbol_return * weight
        total_return *= 100  # Convertir a porcentaje
        
        # Preparar métricas del portafolio
        portfolio_metrics = {
            'weights': weights,
            'roi': total_return,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_drawdown * 100,
            'weekly_investment': weekly_investment
        }
        
        # Agregar métricas por activo
        for symbol, weight in weights.items():
            investment = weekly_investment * weight
            portfolio_metrics[symbol] = {
                'weight': weight * 100,
                'weekly_investment': investment,
                'market_cap': self.metadata[symbol]['market_cap'],
                'volume_24h': self.metadata[symbol]['volume_24h'],
                'rank': self.metadata[symbol]['rank']
            }
        
        return portfolio_metrics

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calcula el ratio de Sharpe"""
        if returns.empty:
            return 0
        
        # Anualizar retornos y volatilidad
        excess_returns = returns - (self.config.risk_free_rate / 252)  # Convertir tasa anual a diaria
        annual_excess_return = excess_returns.mean() * 252
        annual_vol = returns.std() * np.sqrt(252)
        
        if annual_vol == 0:
            return 0
        
        return annual_excess_return / annual_vol

    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calcula el ratio de Sortino"""
        if returns.empty:
            return 0
        
        # Anualizar retornos
        excess_returns = returns - (self.config.risk_free_rate / 252)  # Convertir tasa anual a diaria
        annual_excess_return = excess_returns.mean() * 252
        
        # Calcular desviación estándar de retornos negativos
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return 0
        
        downside_vol = negative_returns.std() * np.sqrt(252)
        if downside_vol == 0:
            return 0
        
        return annual_excess_return / downside_vol

    def plot_portfolio_analysis(self, portfolio_metrics: Dict, metrics_df: pd.DataFrame) -> plt.Figure:
        """Genera visualizaciones del análisis del portafolio"""
        try:
            # Configurar estilo
            plt.style.use('default')
            
            # Crear figura con subplots
            fig = plt.figure(figsize=(20, 15))
            gs = gridspec.GridSpec(3, 2, figure=fig)
            
            # 1. Distribución del portafolio
            ax1 = fig.add_subplot(gs[0, 0])
            portfolio_weights = pd.Series(portfolio_metrics['weights'])
            portfolio_weights.plot(kind='pie', ax=ax1, autopct='%1.1f%%')
            ax1.set_title('Distribución del Portafolio')
            
            # 2. Métricas principales
            ax2 = fig.add_subplot(gs[0, 1])
            metrics = ['roi', 'volatility', 'sharpe_ratio', 'max_drawdown']
            values = [portfolio_metrics[m] for m in metrics]
            ax2.bar(metrics, values)
            ax2.set_title('Métricas Principales del Portafolio')
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # 3. Matriz de correlación
            ax3 = fig.add_subplot(gs[1, :])
            if not self.correlation_matrix.empty:
                sns.heatmap(self.correlation_matrix, ax=ax3, cmap='coolwarm', center=0)
                ax3.set_title('Matriz de Correlación')
            
            # 4. Métricas por activo
            ax4 = fig.add_subplot(gs[2, :])
            selected_metrics = metrics_df.loc[portfolio_weights.index][
                ['price_return', 'volatility', 'sharpe', 'sortino']
            ]
            selected_metrics.plot(kind='bar', ax=ax4)
            ax4.set_title('Métricas por Activo')
            plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            logger.error(f"Error generando visualizaciones: {str(e)}")
            return None

    def calculate_optimal_allocation(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calcula la asignación óptima del portafolio considerando múltiples factores"""
        weights = {}
        
        # Añadir nuevos factores de análisis
        for symbol, data in market_data.items():
            # Análisis técnico
            rsi = self._calculate_rsi(data['close'])
            momentum = self._calculate_momentum(data['close'])
            
            # Análisis fundamental
            market_cap = self.metadata[symbol].get('market_cap', 0)
            profit_ratio = self.metadata[symbol].get('ratio_beneficios', 0)
            
            # Análisis de direcciones
            holder_distribution = self._analyze_holder_distribution(symbol)
            
            # Calcular score compuesto
            technical_score = rsi * 0.3 + momentum * 0.2
            fundamental_score = market_cap * 0.2 + profit_ratio * 0.2
            holder_score = holder_distribution * 0.1
            
            total_score = technical_score + fundamental_score + holder_score
            weights[symbol] = total_score
        
        # Normalizar pesos
        total = sum(weights.values())
        return {k: v/total for k,v in weights.items()}

def main():
    try:
        # Configurar optimizador
        config = OptimizationConfig()
        
        data_dir = 'data/historical'
        weekly_investment = 100  # EUR
        
        logger.info("Iniciando optimización de portafolio DCA...")
        optimizer = EnhancedDCAOptimizer(data_dir)
        
        portfolio_metrics, metrics_df = optimizer.optimize_portfolio(weekly_investment)
        
        if not portfolio_metrics:
            logger.error("No se pudo encontrar una estrategia óptima.")
            return
        
        # Imprimir resultados
        logger.info("\nResultados del Portafolio Optimizado:\n")
        logger.info("Distribución del portafolio:\n")
        
        # Imprimir métricas por activo
        for symbol, weight in portfolio_metrics['weights'].items():
            asset_metrics = portfolio_metrics[symbol]
            logger.info(f"{symbol}:")
            logger.info(f"  Peso: {asset_metrics['weight']:.2f}%")
            logger.info(f"  Inversión semanal: {asset_metrics['weekly_investment']:.2f} EUR")
            logger.info(f"  Market Cap: {asset_metrics['market_cap']/1e6:.2f}M USD")
            logger.info(f"  Volumen 24h: {asset_metrics['volume_24h']/1e6:.2f}M USD")
            logger.info(f"  Ranking CMC: {asset_metrics['rank']}")
            logger.info("")
        
        # Imprimir métricas del portafolio
        logger.info("Métricas del portafolio completo:")
        logger.info(f"ROI total: {portfolio_metrics['roi']:.2f}%")
        logger.info(f"Volatilidad: {portfolio_metrics['volatility']:.2f}%")
        logger.info(f"Ratio de Sharpe: {portfolio_metrics['sharpe_ratio']:.2f}")
        logger.info(f"Ratio de Sortino: {portfolio_metrics['sortino_ratio']:.2f}")
        logger.info(f"Máximo Drawdown: {portfolio_metrics['max_drawdown']:.2f}%")
        
        # Generar visualizaciones
        fig = optimizer.plot_portfolio_analysis(portfolio_metrics, metrics_df)
        if fig:
            fig.savefig('portfolio_analysis.png')
            plt.close(fig)
            logger.info("\nVisualizaciones guardadas en 'portfolio_analysis.png'")
        
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 