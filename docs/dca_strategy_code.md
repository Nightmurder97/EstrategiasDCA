# Código de la Estrategia DCA para Criptomonedas

Este documento contiene el código completo de la estrategia DCA (Dollar Cost Averaging) para criptomonedas. 
El código está formateado para lectura y análisis, no para ejecución directa.

```python
#!/usr/bin/env python3
"""
Estrategia DCA (Dollar Cost Averaging) para Criptomonedas
Este script combina la lógica de trading DCA con un sistema de copias de seguridad.
"""

# Importaciones necesarias
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from dataclasses import dataclass
import json
import os
from concurrent.futures import ThreadPoolExecutor
import warnings
import shutil
import glob
import logging
warnings.filterwarnings('ignore')

# Configuración de logging
logging.basicConfig(
    filename='dca_trader.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_cached_symbol_data(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Carga datos en caché si existen y coinciden con el rango requerido."""
    cache_file = f"data/{symbol}_cache.csv"
    if os.path.exists(cache_file):
        try:
            df_cache = pd.read_csv(cache_file, parse_dates=['timestamp'], index_col='timestamp')
            # Filtrar por rango de fechas
            df_cache = df_cache[(df_cache.index >= start_date) & (df_cache.index <= end_date)]
            if not df_cache.empty:
                logging.info(f"Datos cargados de caché para {symbol}")
                return df_cache
        except Exception as e:
            logging.error(f"Error al leer caché para {symbol}: {str(e)}")
    return pd.DataFrame()

def save_cached_symbol_data(symbol: str, df: pd.DataFrame):
    """Guarda datos en formato CSV como caché."""
    os.makedirs("data", exist_ok=True)
    cache_file = f"data/{symbol}_cache.csv"
    try:
        if os.path.exists(cache_file):
            # Añadir datos sin duplicar
            df_existing = pd.read_csv(cache_file, parse_dates=['timestamp'], index_col='timestamp')
            df_combined = pd.concat([df_existing, df]).drop_duplicates().sort_index()
            df_combined.to_csv(cache_file)
        else:
            df.to_csv(cache_file)
        logging.info(f"Datos guardados en caché para {symbol}")
    except Exception as e:
        logging.error(f"Error al guardar caché para {symbol}: {str(e)}")

def fetch_symbol_data(symbol: str, start_date: datetime, end_date: datetime) -> Tuple[str, pd.DataFrame]:
    """Descarga datos de Binance si no están en caché."""
    # Primero tratar de leer en caché
    df = get_cached_symbol_data(symbol, start_date, end_date)
    if not df.empty:
        return symbol, df
    
    try:
        # Si no hay datos en caché, realizar petición
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": int(start_date.timestamp() * 1000),
            "endTime": int(end_date.timestamp() * 1000),
            "limit": 1000
        }
        response = requests.get(url, params=params)
        data = response.json()

        df = pd.DataFrame(data)[[0, 4, 5]]  # timestamp, close, volume
        df.columns = ['timestamp', 'close', 'volume']
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df.set_index('timestamp', inplace=True)
        
        # Guardar datos en caché
        save_cached_symbol_data(symbol, df)
        logging.info(f"Datos descargados y guardados para {symbol}")
        
        return symbol, df
    except Exception as e:
        logging.error(f"Error al descargar datos para {symbol}: {str(e)}")
        return symbol, pd.DataFrame()

@dataclass
class LiveTradingParameters:
    weekly_investment: float = 100  # Inversión semanal en EUR
    lookback_period: int = 90  # Días de datos históricos a considerar
    min_volume_percentile: float = 25  # Filtro de volumen mínimo
    max_position_size: float = 0.30  # Máximo % del portafolio en un activo
    rebalance_threshold: float = 0.05  # Umbral de desviación para rebalanceo


class PortfolioBackup:
    def __init__(self):
        self.portfolio_file = 'portfolio_history.json'
        self.backup_dir = 'backups'
        self.daily_dir = os.path.join(self.backup_dir, 'daily')
        self.weekly_dir = os.path.join(self.backup_dir, 'weekly')
        
        # Crear directorios si no existen
        for directory in [self.backup_dir, self.daily_dir, self.weekly_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def create_backup(self):
        """Crear copia de seguridad del portafolio"""
        if not os.path.exists(self.portfolio_file):
            print(f"Error: No se encuentra el archivo {self.portfolio_file}")
            return False
        
        # Obtener fecha actual
        now = datetime.now()
        
        # Crear copia diaria
        daily_backup = os.path.join(
            self.daily_dir,
            f'portfolio_{now.strftime("%Y-%m-%d")}.json'
        )
        
        # Crear copia semanal (cada lunes)
        if now.weekday() == 0:  # 0 = Lunes
            weekly_backup = os.path.join(
                self.weekly_dir,
                f'portfolio_{now.strftime("%Y-W%W")}.json'
            )
            shutil.copy2(self.portfolio_file, weekly_backup)
            print(f"Copia semanal creada: {weekly_backup}")
        
        # Copiar archivo
        shutil.copy2(self.portfolio_file, daily_backup)
        print(f"Copia diaria creada: {daily_backup}")
        
        # Limpiar copias antiguas
        self._cleanup_old_backups()
        
        return True
    
    def _cleanup_old_backups(self):
        """Eliminar copias de seguridad antiguas"""
        # Mantener solo los últimos 7 días
        daily_backups = glob.glob(os.path.join(self.daily_dir, 'portfolio_*.json'))
        daily_backups.sort(reverse=True)
        
        for backup in daily_backups[7:]:  # Mantener solo los 7 más recientes
            os.remove(backup)
            print(f"Eliminada copia diaria antigua: {backup}")
        
        # Mantener solo las últimas 8 semanas
        weekly_backups = glob.glob(os.path.join(self.weekly_dir, 'portfolio_*.json'))
        weekly_backups.sort(reverse=True)
        
        for backup in weekly_backups[8:]:  # Mantener solo las 8 más recientes
            os.remove(backup)
            print(f"Eliminada copia semanal antigua: {backup}")


class LiveDCATrader:
    def __init__(self, params: LiveTradingParameters):
        self.params = params
        self.portfolio_file = 'portfolio_history.json'
        self.portfolio_history = self._load_portfolio_history()
        self.backup = PortfolioBackup()
        
        # Lista actualizada de símbolos
        self.symbols = [
            'BTCUSDT',  # Mayor capitalización y volumen
            'XRPUSDT',  # Alto volumen y soporte técnico
            'ADAUSDT',  # Bajo precio, buen volumen
            'DOGEUSDT', # Meme coin popular
            'DOTUSDT'   # Proyecto sólido
        ]

    def get_market_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de mercado usando caché cuando es posible."""
        logging.info("Iniciando descarga de datos de mercado")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.params.lookback_period)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(
                lambda s: fetch_symbol_data(s, start_date, end_date), 
                self.symbols
            )
        market_data = dict(results)
        return {k: v for k, v in market_data.items() if not v.empty}

    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Calcula el RSI (Relative Strength Index)."""
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ma_up = up.rolling(window=period).mean()
        ma_down = down.rolling(window=period).mean()
        rs = ma_up / ma_down
        return 100 - (100 / (1 + rs))

    def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcula las Bandas de Bollinger."""
        ma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = ma + (std * num_std)
        lower = ma - (std * num_std)
        return upper, ma, lower

    def _calculate_metrics(self, data: pd.DataFrame) -> Dict:
        """Calcula métricas técnicas para un activo."""
        try:
            # Calcular métricas básicas
            prices = data['close']
            returns = prices.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            sharpe = returns.mean() / volatility if volatility != 0 else 0
            volume_rank = data['volume'].rank(pct=True).mean()
            
            # Calcular RSI
            rsi14 = self.rsi(prices, 14)
            latest_rsi = rsi14.iloc[-1] if len(rsi14) > 14 else None
            
            # Calcular Bandas de Bollinger
            upper, ma20, lower = self.bollinger_bands(prices)
            bb_position = (prices.iloc[-1] - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])
            
            # Calcular medias móviles
            ma7 = prices.rolling(window=7).mean()
            ma25 = prices.rolling(window=25).mean()
            ma99 = prices.rolling(window=99).mean()
            
            # Calcular cambio porcentual diario
            daily_change = (prices.iloc[-1] - prices.iloc[-2]) / prices.iloc[-2] * 100
            
            # Evaluar tendencia técnica
            trend_score = 0
            if ma7.iloc[-1] > ma25.iloc[-1]:  # Tendencia alcista corto plazo
                trend_score += 1
            if ma25.iloc[-1] > ma99.iloc[-1]:  # Tendencia alcista medio plazo
                trend_score += 1
            if prices.iloc[-1] > ma7.iloc[-1]:  # Precio sobre MA7
                trend_score += 0.5
            
            # Calcular score de oportunidad de compra
            dip_opportunity = 0
            
            # Señales de RSI
            if latest_rsi is not None:
                if latest_rsi < 30:  # Sobreventa
                    dip_opportunity += 1.5
                elif latest_rsi < 40:
                    dip_opportunity += 0.75
            
            # Señales de Bollinger
            if bb_position < 0.2:  # Cerca de la banda inferior
                dip_opportunity += 1
            elif bb_position < 0.3:
                dip_opportunity += 0.5
            
            # Señales de precio
            if daily_change < -5:  # Caída significativa
                if trend_score >= 2:  # Tendencia general alcista
                    dip_opportunity += 1.5
                elif trend_score >= 1:
                    dip_opportunity += 0.75
            elif daily_change < -3:  # Caída moderada
                if trend_score >= 2:
                    dip_opportunity += 1
                elif trend_score >= 1:
                    dip_opportunity += 0.5
            
            return {
                'sharpe': sharpe,
                'volatility': volatility,
                'volume_rank': volume_rank,
                'daily_change': daily_change,
                'trend_score': trend_score,
                'dip_opportunity': dip_opportunity,
                'latest_rsi': latest_rsi,
                'bb_position': bb_position
            }
        except Exception as e:
            logging.error(f"Error al calcular métricas: {str(e)}")
            return {}

    def calculate_optimal_allocation(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calcula la asignación óptima basada en múltiples factores."""
        try:
            metrics = {}
            base_weights = {
                'BTCUSDT': 0.25,   # 25% base para BTC
                'XRPUSDT': 0.20,   # 20% base para XRP
                'ADAUSDT': 0.20,   # 20% base para ADA
                'DOGEUSDT': 0.20,  # 20% base para DOGE
                'DOTUSDT': 0.15    # 15% base para DOT
            }
            
            # Calcular métricas para cada símbolo
            for symbol, data in market_data.items():
                symbol_metrics = self._calculate_metrics(data)
                if not symbol_metrics:
                    continue
                
                # Ajustar peso según múltiples factores
                weight = base_weights[symbol]
                
                # 1. Ajuste por RSI
                if symbol_metrics['latest_rsi'] is not None:
                    if symbol_metrics['latest_rsi'] < 30:
                        weight *= 1.3  # Aumentar 30% en sobreventa
                    elif symbol_metrics['latest_rsi'] > 70:
                        weight *= 0.7  # Reducir 30% en sobrecompra
                
                # 2. Ajuste por Bollinger Bands
                if symbol_metrics['bb_position'] < 0.2:
                    weight *= 1.2  # Aumentar 20% cerca de banda inferior
                elif symbol_metrics['bb_position'] > 0.8:
                    weight *= 0.8  # Reducir 20% cerca de banda superior
                
                # 3. Ajuste por tendencia
                if symbol_metrics['trend_score'] >= 2:
                    weight *= 1.1  # Aumentar 10% en tendencia alcista fuerte
                elif symbol_metrics['trend_score'] <= 0.5:
                    weight *= 0.9  # Reducir 10% en tendencia bajista
                
                # 4. Ajuste por volatilidad
                vol_factor = 1 / (1 + symbol_metrics['volatility'])
                weight *= (0.8 + 0.4 * vol_factor)  # Ajuste entre -20% y +20%
                
                # 5. Ajuste por caída de precio
                if symbol_metrics['daily_change'] <= -8:
                    weight *= 1.4  # Aumentar 40% en caídas fuertes
                elif symbol_metrics['daily_change'] <= -5:
                    weight *= 1.25  # Aumentar 25% en caídas moderadas
                elif symbol_metrics['daily_change'] >= 5:
                    weight *= 0.8  # Reducir 20% en subidas significativas
                
                metrics[symbol] = {
                    'daily_change': symbol_metrics['daily_change'],
                    'weight': weight,
                    'metrics': symbol_metrics
                }
            
            # Normalizar pesos para que sumen 1
            total_weight = sum(m['weight'] for m in metrics.values())
            if total_weight > 0:
                for symbol in metrics:
                    metrics[symbol]['weight'] /= total_weight
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error al calcular asignación óptima: {str(e)}")
            return {}

# [Resto del código omitido por brevedad]
# El código completo incluye más funciones para:
# - Obtención de datos de mercado
# - Generación de recomendaciones
# - Actualización del portafolio
# - Generación de reportes
# - Visualización de rendimiento
# - Análisis técnico detallado
```

## Notas Importantes

1. Este código es para análisis y referencia.
2. No ejecutar directamente sin entender completamente su funcionamiento.
3. Requiere configuración adicional y dependencias.
4. Los parámetros y pesos deben ajustarse según tu estrategia.
5. Usar bajo tu propia responsabilidad.

## Dependencias Principales

```python
requirements = {
    'pandas': '>=2.2.0',
    'numpy': '>=1.26.0',
    'matplotlib': '>=3.8.0',
    'requests': '>=2.31.0',
    'tqdm': '>=4.66.0',
    'seaborn': '>=0.13.0'
}
```

## Características Clave

1. Inversión periódica automatizada
2. Ajuste dinámico de pesos
3. Análisis técnico con múltiples indicadores
4. Sistema de copias de seguridad
5. Gestión de portafolio completa 