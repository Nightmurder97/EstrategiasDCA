import logging
import unittest
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple
import os
from src.config_models import load_config
import talib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar el cliente de Binance (usar claves de entorno)
binance = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET')
})

def get_historical_data(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Obtiene datos históricos de precios de cierre desde Binance."""
    try:
        ohlcv = binance.fetch_ohlcv(symbol, timeframe='1d', since=start_date.timestamp() * 1000, limit=1000)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)
        return df.set_index('timestamp')[['close']]
    except ccxt.ExchangeError as e:
        logger.error(f"Error de Binance al obtener datos de {symbol}: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error inesperado al obtener datos de {symbol}: {str(e)}")
        return pd.DataFrame()

def dca_strategy(symbols: List[str], start_date: datetime, end_date: datetime, investment_per_week: float,
                 rebalance_frequency: int = 4, risk_threshold: float = 0.1):
    """Implementa la estrategia DCA con inversión dinámica y rebalanceo."""
    logger.info(f"Iniciando estrategia DCA. Fecha inicio: {start_date}, Fecha fin: {end_date}")
    portfolio = {}
    total_investment = 0
    num_weeks = 0

    try:
        # Aumentar inversión en activos principales
        weights = {
            'BTC-USD': 0.40,  # Aumentamos Bitcoin
            'ETH-USD': 0.25,  # Aumentamos Ethereum
            'BNB-USD': 0.10,  # Exchange tokens suelen ser más estables
            'SOL-USD': 0.10,
            'XRP-USD': 0.05,
            'ADA-USD': 0.05,
            'LINK-USD': 0.05  # Oráculos son infraestructura importante
        }
        
        for symbol in symbols:
            logger.info(f"Procesando símbolo: {symbol}")
            allocation = weights.get(symbol, 0)
            if allocation > 0:
                symbol_investment = investment_per_week * allocation
                logger.info(f"Invirtiendo {symbol_investment}€ en {symbol}")
                data = get_historical_data(symbol, start_date, end_date)
                if data.empty:
                    logger.warning(f"No se pudieron obtener datos para {symbol}.")
                    continue

                prices = data['close']
                rsi = talib.RSI(prices, timeperiod=14)

                current_date = start_date
                while current_date <= end_date:
                    if current_date in prices.index:
                        price = prices[current_date]
                        current_rsi = rsi[current_date]

                        # Inversión dinámica basada en RSI y desviación del precio
                        investment = symbol_investment * (1 + (current_rsi - 50) / 50 * 0.2)

                        if symbol not in portfolio:
                            portfolio[symbol] = {'coins': 0, 'investment': 0}

                        coins_bought = investment / price
                        portfolio[symbol]['coins'] += coins_bought
                        portfolio[symbol]['investment'] += investment
                        total_investment += investment
                        logger.info(f"Fecha: {current_date}, Precio: {price:.2f}, Monedas compradas: {coins_bought:.4f}, Inversión: {investment:.2f}")
                    current_date += timedelta(weeks=1)
                    num_weeks += 1

        final_portfolio_value = 0
        logger.info("\nResumen del portafolio:")
        for symbol, data in portfolio.items():
            final_value = data['coins'] * prices.iloc[-1]
            final_portfolio_value += final_value
            logger.info(f"{symbol}: Monedas: {data['coins']:.4f}, Inversión: {data['investment']:.2f}, Valor final: {final_value:.2f}")

        logger.info(f"\nInversión total: {total_investment:.2f}, Valor final del portafolio: {final_portfolio_value:.2f}")

        # Rebalanceo (implementación simplificada)
        if num_weeks % rebalance_frequency == 0:
            logger.info("\nRebalanceo del portafolio:")
            # Calcular el nuevo peso de cada activo
            # ... (implementación del rebalanceo)

    except Exception as e:
        logger.exception(f"Error en la estrategia DCA: {e}")

class TestDCA(unittest.TestCase):
    def test_get_historical_data(self):
        # Prueba básica para verificar que la función devuelve un DataFrame
        data = get_historical_data('BTCUSDT', datetime(2023, 1, 1), datetime(2023, 1, 31))
        self.assertIsInstance(data, pd.DataFrame)
        self.assertGreater(len(data), 0)

    def test_dca_strategy_empty_data(self):
        # Prueba con datos vacíos
        symbols = ['INVALID_SYMBOL']
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        investment_per_week = 100
        with self.assertRaises(Exception): # Expecting an exception due to empty data
            dca_strategy(symbols, start_date, end_date, investment_per_week)

    def test_dca_strategy_valid_data(self):
        # Prueba con datos válidos
        symbols = ['BTCUSDT']
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        investment_per_week = 100
        dca_strategy(symbols, start_date, end_date, investment_per_week)



def get_historical_data(symbol, start_date, end_date):
    # Obtener datos históricos de Yahoo Finance
    crypto = yf.Ticker(symbol)
    data = crypto.history(start=start_date, end=end_date)
    if data.empty:
        print("No se pudieron obtener datos para esta criptomoneda.")
        return pd.DataFrame()
    data.reset_index(inplace=True)
    data['timestamp'] = data['Date'].apply(lambda x: x.timestamp())
    return data[['timestamp', 'Close']].rename(columns={'Close': 'price'})


def dca_strategy(symbols, start_date, end_date, investment_per_week):
    print(f"Estrategia DCA ajustada para mercado bajista")
    
    # Aumentar inversión en activos principales
    weights = {
        'BTC-USD': 0.40,  # Aumentamos Bitcoin
        'ETH-USD': 0.25,  # Aumentamos Ethereum
        'BNB-USD': 0.10,  # Exchange tokens suelen ser más estables
        'SOL-USD': 0.10,
        'XRP-USD': 0.05,
        'ADA-USD': 0.05,
        'LINK-USD': 0.05  # Oráculos son infraestructura importante
    }
    
    for symbol in symbols:
        allocation = weights.get(symbol, 0)
        if allocation > 0:
            symbol_investment = investment_per_week * allocation
            print(f"\nInvirtiendo {symbol_investment}€ en {symbol}")
            # ... resto del código ...


# Ejemplo de uso
if __name__ == "__main__":
    symbols = [
        'BTC-USD',  # 61.92% - $104,868.19
        'ETH-USD',  # 12.27% - $3,416.44
        'XRP-USD',  # 5.51% - $3.21
        'SOL-USD',  # 3.14% - $216.70
        'BNB-USD',  # 3.10% - $722.66
        'DOGE-USD', # 1.80% - $0.41
        'ADA-USD',  # 1.18% - $1.12
        'TRX-USD',  # 0.63% - $0.2468
        'AVAX-USD', # 0.50% - $40.82
        'LINK-USD'  # 0.46% - $24.45
    ]
    
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    investment_per_week = 100  # Inversión en EUR por semana

    print(f"\nFecha actual: {end_date.strftime('%d/%m/%Y')}")
    print(f"Inversión semanal: {investment_per_week}€")
    print("\nDistribución por capitalización de mercado:")
    print("BTC: 61.92% - $104,868.19")
    print("ETH: 12.27% - $3,416.44")
    print("XRP: 5.51% - $3.21")
    print("SOL: 3.14% - $216.70")
    print("BNB: 3.10% - $722.66")
    print("DOGE: 1.80% - $0.41")
    print("ADA: 1.18% - $1.12")
    print("TRX: 0.63% - $0.2468")
    print("AVAX: 0.50% - $40.82")
    print("LINK: 0.46% - $24.45\n")

    dca_strategy(symbols, start_date, end_date, investment_per_week)