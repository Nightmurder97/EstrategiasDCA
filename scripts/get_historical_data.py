from binance.client import Client
import pandas as pd
import os
import requests
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional
import json
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

class MultiSourceDataCollector:
    def __init__(self):
        # Configuración de directorios
        self.data_dir = 'data/historical'
        os.makedirs(self.data_dir, exist_ok=True)
        self.metadata_file = os.path.join(self.data_dir, 'crypto_metadata.json')
        
        # URLs base de las APIs
        self.livecoinwatch_base_url = "https://api.livecoinwatch.com"
        self.coincodex_base_url = "https://api.coincodex.com"
        self.cryptocompare_base_url = "https://min-api.cryptocompare.com/data"
        self.kucoin_base_url = "https://api.kucoin.com"
        
        # Inicializar clientes
        self.binance_client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
        
        # Cache para IDs de CoinGecko
        self.coingecko_ids = self._get_coingecko_ids()

    def _get_coingecko_ids(self) -> Dict[str, str]:
        """Obtiene el mapeo de símbolos a IDs de CoinGecko"""
        try:
            response = requests.get(f"{self.coingecko_base_url}/coins/list")
            coins = response.json()
            return {coin['symbol'].upper(): coin['id'] for coin in coins}
        except Exception as e:
            print(f"Error obteniendo IDs de CoinGecko: {str(e)}")
            return {}

    def get_historical_data_livecoinwatch(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de LiveCoinWatch"""
        try:
            url = f"{self.livecoinwatch_base_url}/coins/historical"
            params = {
                'code': symbol,
                'currency': 'USD',
                'start': int((datetime.now() - timedelta(days=365)).timestamp() * 1000),
                'end': int(datetime.now().timestamp() * 1000),
                'meta': False
            }
            response = requests.get(url, params=params)
            return self._process_livecoinwatch_data(response.json())
        except Exception as e:
            logger.error(f"Error getting data from LiveCoinWatch for {symbol}: {str(e)}")
            return None

    def get_historical_data_coincodex(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de CoinCodex"""
        try:
            url = f"{self.coincodex_base_url}/api/cryptocurrency/history"
            params = {
                'symbol': symbol,
                'time_start': int((datetime.now() - timedelta(days=365)).timestamp()),
                'time_end': int(datetime.now().timestamp())
            }
            response = requests.get(url, params=params)
            return self._process_coincodex_data(response.json())
        except Exception as e:
            logger.error(f"Error getting data from CoinCodex for {symbol}: {str(e)}")
            return None

    def get_historical_data_cryptocompare(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de CryptoCompare"""
        try:
            url = f"{self.cryptocompare_base_url}/v2/histoday"
            params = {
                'fsym': symbol,
                'tsym': 'USD',
                'limit': 365
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'Data' in data and 'Data' in data['Data']:
                df = pd.DataFrame(data['Data']['Data'])
                df['timestamp'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('timestamp', inplace=True)
                df = df[['close', 'volumeto']]
                df.columns = ['close', 'volume']
                return df
                
            return None
            
        except Exception as e:
            print(f"Error obteniendo datos de CryptoCompare para {symbol}: {str(e)}")
            return None

    def get_historical_data_yahoo(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de Yahoo Finance"""
        try:
            ticker = yf.Ticker(f"{symbol}-USD")
            df = ticker.history(period="1y")
            
            if not df.empty:
                df = df[['Close', 'Volume']]
                df.columns = ['close', 'volume']
                return df
                
            return None
            
        except Exception as e:
            print(f"Error obteniendo datos de Yahoo Finance para {symbol}: {str(e)}")
            return None

    def get_historical_data_binance(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de Binance"""
        try:
            klines = self.binance_client.get_historical_klines(
                symbol,
                Client.KLINE_INTERVAL_1DAY,
                "1 year ago UTC"
            )
            
            if klines:
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades',
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df[['close', 'volume']].astype(float)
                
            return None
            
        except Exception as e:
            print(f"Error obteniendo datos de Binance para {symbol}: {str(e)}")
            return None

    def get_historical_data_kucoin(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de KuCoin"""
        try:
            end_time = int(datetime.now().timestamp())
            start_time = end_time - 365 * 24 * 60 * 60
            
            url = f"{self.kucoin_base_url}/api/v1/market/candles"
            params = {
                'symbol': f"{symbol}-USDT",
                'type': '1day',
                'startAt': start_time,
                'endAt': end_time
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'data' in data:
                df = pd.DataFrame(data['data'], columns=[
                    'timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                return df[['close', 'volume']].astype(float)
                
            return None
            
        except Exception as e:
            print(f"Error obteniendo datos de KuCoin para {symbol}: {str(e)}")
            return None

    def get_best_data_source(self, symbol: str, coin_id: str = None) -> Optional[pd.DataFrame]:
        """Intenta obtener datos de la mejor fuente disponible"""
        # 1. Intentar LiveCoinWatch
        df = self.get_historical_data_livecoinwatch(symbol)
        if df is not None and not df.empty:
            return df, 'livecoinwatch'
        
        # 2. Intentar CoinCodex
        df = self.get_historical_data_coincodex(symbol)
        if df is not None and not df.empty:
            return df, 'coincodex'
        
        # 3. Intentar Binance
        df = self.get_historical_data_binance(f"{symbol}USDT")
        if df is not None and not df.empty:
            return df, 'binance'
        
        # 4. Intentar KuCoin
        df = self.get_historical_data_kucoin(symbol)
        if df is not None and not df.empty:
            return df, 'kucoin'
        
        # 5. Intentar CryptoCompare
        df = self.get_historical_data_cryptocompare(symbol)
        if df is not None and not df.empty:
            return df, 'cryptocompare'
        
        # 6. Intentar Yahoo Finance
        df = self.get_historical_data_yahoo(symbol)
        if df is not None and not df.empty:
            return df, 'yahoo'
        
        return None, None

    def collect_all_data(self):
        """Proceso principal de recolección de datos"""
        print("Collecting top 500 cryptocurrencies data...")
        try:
            data = self.get_top_500_from_livecoinwatch()
        except Exception as e:
            logger.warning(f"Failed to get data from LiveCoinWatch: {e}")
            data = self.get_top_500_from_coincodex()
        
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'total_cryptos': len(data),
            'cryptos': []
        }
        
        print("\nDownloading historical data...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for crypto in data:
                futures.append(
                    executor.submit(
                        self.get_best_data_source,
                        crypto['symbol']
                    )
                )
            
            for i, future in enumerate(tqdm(futures, desc="Progreso", unit="crypto")):
                df, source = future.result()
                crypto = data[i]
                
                if df is not None:
                    symbol = crypto['symbol'].upper()
                    output_file = os.path.join(self.data_dir, f'{symbol}_historical_data.csv')
                    df.to_csv(output_file)
                    
                    metadata['cryptos'].append({
                        'rank': i + 1,
                        'name': crypto['name'],
                        'symbol': symbol,
                        'market_cap': crypto['market_cap'],
                        'volume_24h': crypto['total_volume'],
                        'price': crypto['current_price'],
                        'data_source': source
                    })
        
        # Guardar metadatos
        metadata['available_cryptos'] = len(metadata['cryptos'])
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        print(f"\nProceso completado.")
        print(f"Se obtuvieron datos para {len(metadata['cryptos'])} de {len(data)} criptomonedas")
        print(f"Los datos han sido guardados en el directorio '{self.data_dir}'")
        print(f"Los metadatos están disponibles en '{self.metadata_file}'")

class CoinCodexDataCollector:
    def __init__(self):
        self.base_url = 'https://coincodex.com/api/v1'
        
    def get_market_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos de mercado de CoinCodex"""
        try:
            # Obtener datos históricos
            endpoint = f"{self.base_url}/get_coin/{symbol}"
            response = requests.get(endpoint)
            data = response.json()
            
            # Obtener datos de precio con más historia (90 días)
            price_endpoint = f"{self.base_url}/get_coin_history/{symbol}/2160/90"  # 90 días de datos
            price_response = requests.get(price_endpoint)
            price_data = price_response.json()
            
            df = pd.DataFrame(price_data)
            df['timestamp'] = pd.to_datetime(df['time'], unit='s')
            df = df.set_index('timestamp')
            
            # Añadir métricas adicionales
            df['market_cap'] = data.get('market_cap', 0)
            df['volume_24h'] = data.get('volume_24h', 0)
            df['change_24h'] = data.get('change_24h', 0)
            df['rank'] = data.get('rank', 0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de CoinCodex para {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_top_coins(self, limit: int = 500) -> list:
        """Obtiene lista de las principales 500 criptomonedas"""
        try:
            # Obtener lista completa de monedas
            endpoint = f"{self.base_url}/get_coin_list"
            response = requests.get(endpoint)
            data = response.json()
            
            # Ordenar por capitalización de mercado
            sorted_coins = sorted(data, key=lambda x: float(x.get('market_cap', 0) or 0), reverse=True)
            
            # Tomar las primeras 500
            top_500 = sorted_coins[:limit]
            
            logger.info(f"Obtenidas {len(top_500)} criptomonedas principales")
            return top_500
            
        except Exception as e:
            logger.error(f"Error obteniendo lista de monedas: {str(e)}")
            return []

def main():
    try:
        logger.info("Iniciando recolección de datos...")
        
        # Inicializar colector
        collector = CoinCodexDataCollector()
        
        # Obtener lista de monedas
        logger.info("Obteniendo lista de top 500 criptomonedas...")
        coins = collector.get_top_coins(limit=500)
        
        if not coins:
            logger.error("No se pudieron obtener las monedas")
            return
            
        logger.info(f"Obtenidas {len(coins)} monedas")
        
        # Mostrar primeras 5 para verificar
        for coin in coins[:5]:
            logger.info(f"Procesando {coin['symbol']} - {coin.get('name', 'N/A')}")
            data = collector.get_market_data(coin['symbol'])
            if not data.empty:
                logger.info(f"Datos obtenidos correctamente para {coin['symbol']}")
            else:
                logger.warning(f"No se pudieron obtener datos para {coin['symbol']}")
                
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")

if __name__ == "__main__":
    main()
