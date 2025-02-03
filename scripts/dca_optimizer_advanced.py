import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from dataclasses import dataclass
import time
from bs4 import BeautifulSoup
import yfinance as yf


@dataclass
class DCAParameters:
    base_investment: float  # Inversión base semanal
    rsi_period: int = 14  # Período para calcular RSI
    price_drop_threshold: float = 0.15  # Caída de precio significativa (15%)
    max_correlation: float = 0.7  # Máximo coeficiente de correlación
    min_volume_percentile: float = 25  # Percentil mínimo para volumen


class AdvancedDCAOptimizer:
    def __init__(self, symbols: List[str], start_date: datetime, end_date: datetime, params: DCAParameters):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.params = params
        self.historical_data = {}
        self.cmc_api_key = "7d306239-f647-4b67-8638-4b6f2e9fbae5"
        self._load_historical_data()

    def _get_yahoo_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos históricos de Yahoo Finance"""
        try:
            # Añadir sufijo -USD para criptomonedas en Yahoo Finance
            ticker = yf.Ticker(f"{symbol}-USD")
            df = ticker.history(start=self.start_date, end=self.end_date)
            
            if not df.empty:
                return df[['Close', 'Volume']].rename(columns={'Close': 'close', 'Volume': 'volume'})
            return pd.DataFrame()
        except Exception as e:
            print(f"Error al obtener datos de Yahoo Finance para {symbol}: {str(e)}")
            return pd.DataFrame()

    def _get_alternative_data(self, symbol: str) -> pd.DataFrame:
        """Intenta obtener datos de fuentes alternativas públicas"""
        try:
            # Intentar con CryptoCompare (acceso público sin API key)
            url = f"https://min-api.cryptocompare.com/data/v2/histoday"
            params = {
                'fsym': symbol,
                'tsym': 'USD',
                'limit': 180,  # 6 meses de datos
                'toTs': int(self.end_date.timestamp())
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Data' not in data or 'Data' not in data['Data']:
                print(f"No hay datos históricos para {symbol}")
                return pd.DataFrame()
            
            # Procesar datos
            df = pd.DataFrame(data['Data']['Data'])
            df['timestamp'] = pd.to_datetime(df['time'], unit='s')
            df = df.set_index('timestamp')
            df = df.rename(columns={'close': 'close', 'volumeto': 'volume'})
            
            # Verificar que tenemos suficientes datos
            if len(df) < 90:  # Al menos 3 meses de datos
                print(f"Datos insuficientes para {symbol} ({len(df)} días)")
                return pd.DataFrame()
            
            return df[['close', 'volume']]
            
        except Exception as e:
            print(f"Error al obtener datos alternativos para {symbol}: {str(e)}")
            return pd.DataFrame()

    def _get_coingecko_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos históricos de CoinGecko sin API key"""
        try:
            # Convertir símbolo a minúsculas para CoinGecko
            symbol = symbol.lower()
            
            # Obtener lista de monedas para encontrar el id
            url = "https://api.coingecko.com/api/v3/coins/list"
            response = requests.get(url)
            if response.status_code == 429:
                print(f"Rate limit alcanzado, esperando 60 segundos...")
                time.sleep(60)
                response = requests.get(url)
            
            coins = response.json()
            coin_id = None
            
            # Buscar el id de la moneda
            for coin in coins:
                if coin['symbol'] == symbol:
                    coin_id = coin['id']
                    break
            
            if not coin_id:
                return pd.DataFrame()
            
            # Obtener datos históricos
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': '180',  # 6 meses
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 429:
                print(f"Rate limit alcanzado para {symbol}, esperando 60 segundos...")
                time.sleep(60)
                response = requests.get(url, params=params)
            
            data = response.json()
            
            # Procesar datos
            prices = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
            volumes = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
            
            prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')
            df = prices.merge(volumes[['timestamp', 'volume']], on='timestamp')
            df = df.set_index('timestamp')
            
            return df
            
        except Exception as e:
            print(f"Error al obtener datos de CoinGecko para {symbol}: {str(e)}")
            return pd.DataFrame()

    def _get_coinmarketcap_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos históricos de CoinMarketCap"""
        try:
            # Primero obtener el listado de todas las criptomonedas
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            headers = {
                'X-CMC_PRO_API_KEY': self.cmc_api_key,
                'Accept': 'application/json'
            }
            params = {
                'start': '1',
                'limit': '500',
                'convert': 'USD'
            }
            
            while True:
                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                
                if 'status' in data and 'error_code' in data['status'] and data['status']['error_code'] == 1008:
                    print(f"Rate limit alcanzado, esperando 60 segundos...")
                    time.sleep(60)
                    continue
                break
            
            if 'data' not in data:
                print(f"Error al obtener listado de criptomonedas: {data}")
                return pd.DataFrame()
            
            # Buscar el ID de la criptomoneda
            coin_id = None
            for coin in data['data']:
                if coin['symbol'] == symbol:
                    coin_id = coin['id']
                    break
            
            if not coin_id:
                print(f"No se encontró el ID para {symbol}")
                return pd.DataFrame()
            
            # Esperar un poco antes de la siguiente solicitud
            time.sleep(1)
            
            # Obtener datos históricos
            url = f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/ohlcv/historical"
            params = {
                'id': coin_id,
                'time_start': int(self.start_date.timestamp()),
                'time_end': int(self.end_date.timestamp()),
                'interval': 'daily',
                'count': 180  # 6 meses
            }
            
            while True:
                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                
                if 'status' in data and 'error_code' in data['status'] and data['status']['error_code'] == 1008:
                    print(f"Rate limit alcanzado, esperando 60 segundos...")
                    time.sleep(60)
                    continue
                break
            
            if 'data' not in data or 'quotes' not in data['data']:
                print(f"No hay datos históricos para {symbol}")
                return pd.DataFrame()
            
            # Procesar datos
            quotes = data['data']['quotes']
            df_data = []
            
            for quote in quotes:
                df_data.append({
                    'timestamp': pd.to_datetime(quote['time_open']),
                    'close': quote['quote']['USD']['close'],
                    'volume': quote['quote']['USD']['volume']
                })
            
            df = pd.DataFrame(df_data)
            df = df.set_index('timestamp')
            
            return df
            
        except Exception as e:
            print(f"Error al obtener datos de CoinMarketCap para {symbol}: {str(e)}")
            return pd.DataFrame()

    def _load_historical_data(self):
        """Carga datos históricos usando CryptoCompare"""
        print("Cargando datos históricos...")
        
        for symbol in self.symbols:
            print(f"Procesando {symbol}...")
            df = self._get_alternative_data(symbol)
            
            if not df.empty:
                self.historical_data[symbol] = df
                print(f"✓ Datos obtenidos para {symbol}")
            else:
                print(f"✗ No se pudieron obtener datos para {symbol}")
            
            # Esperar un poco entre solicitudes
            time.sleep(0.5)

    def _calculate_metrics(self, data: pd.DataFrame) -> Dict:
        """Calcula métricas para un activo"""
        returns = data['close'].pct_change()
        
        metrics = {
            'volatility': returns.std() * np.sqrt(252) * 100,  # Anualizada
            'roi': ((data['close'].iloc[-1] / data['close'].iloc[0]) - 1) * 100,
            'sharpe': (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0,
            'volume_avg': data['volume'].mean(),
            'market_cap': data['close'].iloc[-1] * data['volume'].iloc[-1] / data['close'].iloc[-1]  # Aproximación
        }
        
        return metrics

    def optimize_portfolio(self) -> Dict:
        """Optimiza el portafolio usando múltiples criterios"""
        if not self.historical_data:
            print("No hay datos históricos disponibles")
            return {}

        portfolio = {}
        total_weight = 0
        base_investment = self.params.base_investment

        # Calcular métricas para cada activo
        asset_metrics = {}
        for symbol, data in self.historical_data.items():
            metrics = self._calculate_metrics(data)
            asset_metrics[symbol] = metrics

        # Filtrar por volumen y market cap
        volumes = [m['volume_avg'] for m in asset_metrics.values()]
        min_volume = np.percentile(volumes, self.params.min_volume_percentile)
        
        filtered_assets = {
            symbol: metrics for symbol, metrics in asset_metrics.items()
            if metrics['volume_avg'] >= min_volume and metrics['market_cap'] > 1000000  # Mínimo $1M market cap
        }

        # Ordenar por ratio de Sharpe
        sorted_assets = sorted(
            filtered_assets.items(),
            key=lambda x: x[1]['sharpe'],
            reverse=True
        )

        # Seleccionar los mejores activos
        for symbol, metrics in sorted_assets:
            if total_weight >= 1.0:
                break

            # Calcular peso basado en el ratio de Sharpe y market cap
            weight = min(0.3, 1.0 - total_weight)  # Máximo 30% por activo
            total_weight += weight

            weekly_investment = base_investment * weight
            total_investment = weekly_investment * 26  # 26 semanas en 6 meses

            portfolio[symbol] = {
                'weight': weight,
                'weekly_investment': weekly_investment,
                'total_investment': total_investment,
                'final_value': total_investment * (1 + metrics['roi']/100),
                'roi': metrics['roi'],
                'volatility': metrics['volatility'],
                'sharpe': metrics['sharpe'],
                'market_cap': metrics['market_cap']
            }

        return portfolio

    def plot_results(self, portfolio_results: Dict):
        """Visualiza los resultados del portafolio optimizado"""
        if not portfolio_results:
            print("No hay datos para visualizar")
            return

        plt.figure(figsize=(20, 12))
        
        # 1. Distribución del portafolio
        plt.subplot(2, 2, 1)
        weights = [metrics['weight'] for metrics in portfolio_results.values()]
        plt.pie(weights, labels=portfolio_results.keys(), autopct='%1.1f%%')
        plt.title('Distribución Óptima del Portafolio')
        
        # 2. ROI por activo
        plt.subplot(2, 2, 2)
        rois = [metrics['roi'] for metrics in portfolio_results.values()]
        plt.bar(portfolio_results.keys(), rois)
        plt.xticks(rotation=45)
        plt.ylabel('ROI (%)')
        plt.title('Rendimiento por Criptomoneda')
        
        # 3. Inversión vs Valor Final
        plt.subplot(2, 2, 3)
        investments = [metrics['total_investment'] for metrics in portfolio_results.values()]
        final_values = [metrics['final_value'] for metrics in portfolio_results.values()]
        x = range(len(portfolio_results))
        width = 0.35
        plt.bar(x, investments, width, label='Inversión Total')
        plt.bar([i + width for i in x], final_values, width, label='Valor Final')
        plt.xticks([i + width/2 for i in x], portfolio_results.keys(), rotation=45)
        plt.ylabel('EUR')
        plt.title('Inversión vs Valor Final')
        plt.legend()
        
        # 4. Volatilidad vs ROI
        plt.subplot(2, 2, 4)
        volatilities = [metrics['volatility'] for metrics in portfolio_results.values()]
        plt.scatter(volatilities, rois)
        for i, symbol in enumerate(portfolio_results.keys()):
            plt.annotate(symbol, (volatilities[i], rois[i]))
        plt.xlabel('Volatilidad (%)')
        plt.ylabel('ROI (%)')
        plt.title('Riesgo vs Rendimiento')
        
        plt.tight_layout()
        plt.show()


def main():
    # Configuración de fechas con datos históricos reales
    end_date = datetime(2024, 1, 27)  # Fecha actual
    start_date = datetime(2023, 7, 27)  # 6 meses atrás
    
    print(f"\nPeríodo de análisis:")
    print(f"Fecha de inicio: {start_date.strftime('%d/%m/%Y')}")
    print(f"Fecha de fin: {end_date.strftime('%d/%m/%Y')}")
    print(f"Duración: 6 meses\n")
    
    # Lista de símbolos de las principales criptomonedas
    symbols = [
        'BTC', 'ETH', 'XRP', 'SOL', 'BNB', 'DOGE', 'ADA', 'TRX', 'LINK', 'AVAX',
        'HBAR', 'TON', 'XLM', 'SUI', 'SHIB', 'DOT', 'LEO', 'LTC', 'BCH',
        'UNI', 'NEAR', 'AAVE', 'APT', 'ICP', 'XMR', 'ETC', 'VET', 'MATIC',
        'ALGO', 'FIL', 'ARB', 'FET', 'ATOM', 'SAND', 'APE', 'RUNE', 'MANA', 'GALA',
        'IMX', 'INJ', 'EGLD', 'FLOW', 'THETA', 'XTZ', 'CAKE', 'FTM', 'GRT'
    ]
    
    # Configurar parámetros
    params = DCAParameters(
        base_investment=100,  # 100€ semanales
        rsi_period=14,
        price_drop_threshold=0.15,
        max_correlation=0.7,
        min_volume_percentile=25
    )
    
    # Crear instancia del optimizador
    optimizer = AdvancedDCAOptimizer(symbols, start_date, end_date, params)
    
    print("Iniciando optimización del portafolio...")
    print("Este proceso puede tardar varios minutos debido a las limitaciones de rate de la API")
    
    # Ejecutar optimización
    results = optimizer.optimize_portfolio()
    
    if results:
        print("\nResultados del Portafolio Optimizado:")
        print("\nDistribución semanal de 100€:")
        
        total_value = sum(r['final_value'] for r in results.values())
        total_investment = sum(r['total_investment'] for r in results.values())
        
        # Ordenar resultados por ROI
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['roi'], reverse=True))
        
        for symbol, metrics in sorted_results.items():
            print(f"\n{symbol}:")
            print(f"  Inversión semanal: {metrics['weekly_investment']:.2f} EUR")
            print(f"  Inversión total: {metrics['total_investment']:.2f} EUR")
            print(f"  Valor final: {metrics['final_value']:.2f} EUR")
            print(f"  ROI: {metrics['roi']:.2f}%")
            print(f"  Volatilidad: {metrics['volatility']:.2f}%")
            print(f"  Ratio de Sharpe: {metrics['sharpe']:.2f}")
            print(f"  Market Cap: ${metrics['market_cap']:,.2f}")
        
        print(f"\nMétricas del portafolio:")
        print(f"Inversión total: {total_investment:.2f} EUR")
        print(f"Valor final: {total_value:.2f} EUR")
        print(f"ROI total: {((total_value - total_investment) / total_investment * 100):.2f}%")
        
        optimizer.plot_results(results)
    else:
        print("No se pudo encontrar una estrategia óptima.")


if __name__ == "__main__":
    main() 