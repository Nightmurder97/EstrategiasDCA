import datetime
import logging
import aiohttp
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

@dataclass
class MarketCondition:
    """Condición del mercado basada en análisis técnico"""
    trend: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0-1, qué tan fuerte es la tendencia
    volatility: float  # Volatilidad del mercado
    volume_trend: str  # 'increasing', 'decreasing', 'stable'
    risk_level: str  # 'low', 'medium', 'high'

class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calcula el RSI (Relative Strength Index)"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(period-1) + upval)/period
            down = (down*(period-1) + downval)/period
            rs = up/down
            rsi[i] = 100. - 100./(1. + rs)

        return rsi

    @staticmethod
    def calculate_macd(prices: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula MACD (Moving Average Convergence Divergence)"""
        exp1 = pd.Series(prices).ewm(span=fast_period, adjust=False).mean()
        exp2 = pd.Series(prices).ewm(span=slow_period, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        return macd.to_numpy(), signal.to_numpy()

    @staticmethod
    def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, num_std: float = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calcula las Bandas de Bollinger"""
        rolling_mean = pd.Series(prices).rolling(window=period).mean()
        rolling_std = pd.Series(prices).rolling(window=period).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        return upper_band.to_numpy(), rolling_mean.to_numpy(), lower_band.to_numpy()

    @staticmethod
    def calculate_volume_profile(volumes: np.ndarray, window: int = 20) -> str:
        """Analiza el perfil de volumen"""
        if len(volumes) < window:
            return 'stable'

        recent_vol = np.mean(volumes[-window:])
        prev_vol = np.mean(volumes[-2*window:-window])

        change_pct = (recent_vol - prev_vol) / prev_vol * 100

        if change_pct > 10:
            return 'increasing'
        elif change_pct < -10:
            return 'decreasing'
        return 'stable'

    @staticmethod
    def calculate_volatility(prices: np.ndarray, window: int = 20) -> float:
        """Calcula la volatilidad histórica"""
        if len(prices) < 2:
            return 0.0

        returns = np.log(prices[1:] / prices[:-1])
        return np.std(returns) * np.sqrt(252)  # Anualizada

    @staticmethod
    def calculate_stochastic_oscillator(prices: np.ndarray, k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula el Oscilador Estocástico"""
        lows = pd.Series(prices).rolling(window=k_period).min()
        highs = pd.Series(prices).rolling(window=k_period).max()
        k = 100 * (prices - lows) / (highs - lows)
        d = k.rolling(window=d_period).mean()
        return k.to_numpy(), d.to_numpy()

    @staticmethod
    def calculate_average_true_range(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calcula el Average True Range (ATR)"""
        highs = prices[1:]
        lows = prices[:-1]
        closes = prices[:-1]
        tr = np.maximum(highs - lows, np.abs(highs - closes), np.abs(lows - closes))
        atr = pd.Series(tr).rolling(window=period).mean()
        return atr.to_numpy()

class MarketAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.market_data = {}
        self.session = None
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def _update_current_prices(self):
        """Actualiza los precios actuales de los activos"""
        try:
            async with aiohttp.ClientSession() as session:
                for symbol in self.market_data.keys():
                    ticker_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                    async with session.get(ticker_url) as response:
                        if response.status == 200:
                            ticker_data = await response.json()
                            self.market_data[symbol]['price'] = float(ticker_data['price'])
                        else:
                            logging.error(f"Error fetching current price for {symbol}: {response.status}")
        except Exception as e:
            logging.error(f"Error updating current prices: {e}")

    async def _fetch_market_data(self):
        """Fetch current and historical market data from Binance API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Obtener datos actuales de los símbolos que nos interesan
                symbols = [
                    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'BNBUSDT',
                    'DOGEUSDT', 'ADAUSDT', 'TRXUSDT', 'AVAXUSDT', 'LINKUSDT'
                ]
    
                self.market_data = {}
    
                for symbol in symbols:
                    # Obtener precio actual y volumen 24h
                    ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
                    async with session.get(ticker_url) as response:
                        if response.status == 200:
                            ticker_data = await response.json()
                            logging.debug(f"Fetched ticker data for {symbol}: {ticker_data}")
                            self.market_data[symbol] = {
                                'price': float(ticker_data['lastPrice']),
                                'volume': float(ticker_data['volume']) * float(ticker_data['lastPrice']),
                                'change_24h': float(ticker_data['priceChangePercent']),
                                'market_cap': 0  # Binance no proporciona market cap
                            }
    
                            # Obtener datos históricos (klines/candlesticks)
                            klines_url = f"https://api.binance.com/api/v3/klines"
                            params = {
                                'symbol': symbol,
                                'interval': '1d',
                                'limit': 30  # Últimos 30 días
                            }
    
                            async with session.get(klines_url, params=params) as hist_response:
                                if hist_response.status == 200:
                                    klines_data = await hist_response.json()
                                    logging.debug(f"Fetched historical data for {symbol}: {klines_data}")
                                    self.market_data[symbol]['historical'] = self._process_binance_klines(klines_data)
                                else:
                                    logging.error(f"Error fetching historical data for {symbol}: {hist_response.status}")
                        else:
                            logging.error(f"Error fetching ticker data for {symbol}: {response.status}")
    
        except Exception as e:
            logging.error(f"Error in market data fetch: {e}")

    def _process_binance_klines(self, klines_data: list) -> Dict:
        """Procesa datos históricos de Binance"""
        prices = []
        volumes = []
        timestamps = []

        for kline in klines_data:
            timestamps.append(kline[0])  # Open time
            prices.append(float(kline[4]))  # Close price
            volumes.append(float(kline[5]))  # Volume

        return {
            'prices': np.array(prices),
            'volumes': np.array(volumes),
            'timestamps': timestamps
        }

    def _process_historical_data(self, hist_data: Dict) -> Dict:
        """Procesa datos históricos"""
        prices = []
        volumes = []
        timestamps = []

        for quote in hist_data['quotes']:
            prices.append(quote['quote']['USD']['price'])
            volumes.append(quote['quote']['USD']['volume_24h'])
            timestamps.append(quote['timestamp'])

        return {
            'prices': np.array(prices),
            'volumes': np.array(volumes),
            'timestamps': timestamps
        }

    def _process_market_data(self, raw_data: list) -> Dict[str, Dict]:
        """Process raw API data into structured format"""
        processed = {}
        for item in raw_data:
            processed[item['symbol']] = {
                'price': item['quote']['USD']['price'],
                'volume': item['quote']['USD']['volume_24h'],
                'market_cap': item['quote']['USD']['market_cap'],
                'change_24h': item['quote']['USD']['percent_change_24h']
            }
        return processed

    def _calculate_average_price(self, prices):
        """Calculates the average price."""
        if not prices:
            logging.error("Error calculating average price: No prices provided.")
            return None
        try:
            return sum(prices) / len(prices)
        except TypeError as e:
            logging.error(f"Error calculating average price: {e}")
            return None

    def _calculate_price_change(self, current_price, previous_price):
         """Calculates the price change."""
         if not isinstance(current_price, (int, float)) or not isinstance(previous_price, (int, float)):
            logging.error(f"Error calculating price change: Invalid price types. Current: {type(current_price)}, Previous: {type(previous_price)}")
            return None
         try:
            return current_price - previous_price
         except Exception as e:
            logging.error(f"Error calculating price change: {e}")
            return None

    def generate_report(self):
        """Genera un reporte detallado del análisis de mercado"""
        report = "=== Análisis de Mercado Detallado ===\n\n"
        if not self.market_data:
            logging.error("Error generating report: No market data available.")
            return "No hay datos de mercado disponibles."

        try:
            # Analizar el mercado
            analysis = asyncio.run(self.analyze_market())

            # Resumen general del mercado
            report += "Condiciones Generales del Mercado:\n"
            report += f"Estado: {analysis['market_conditions'].upper()}\n"
            if 'market_metrics' in analysis:
                metrics = analysis['market_metrics']
                report += f"Fuerza promedio: {metrics['average_strength']:.2f}\n"
                report += f"Volatilidad promedio: {metrics['average_volatility']:.2f}\n"
                report += f"Porcentaje alcista: {metrics['bullish_percentage']:.1f}%\n"
                report += f"Porcentaje bajista: {metrics['bearish_percentage']:.1f}%\n"
            report += "\n"

            # Análisis por símbolo
            report += "Análisis por Criptomoneda:\n"
            for symbol, data in analysis['symbol_data'].items():
                report += f"\n{symbol}:\n"
                report += f"  Precio actual: ${data['price']:,.2f}\n"
                report += f"  Cambio 24h: {data['change_24h']:+.2f}%\n"
                report += f"  Volumen 24h: ${data['volume']:,.2f}\n"
                report += f"  Cap. de mercado: ${data['market_cap']:,.2f}\n"

                if 'market_condition' in data:
                    mc = data['market_condition']
                    report += f"  Tendencia: {mc.trend.upper()}\n"
                    report += f"  Fuerza de tendencia: {mc.strength:.2f}\n"
                    report += f"  Volatilidad: {mc.volatility:.2f}\n"
                    report += f"  Tendencia volumen: {mc.volume_trend}\n"
                    report += f"  Nivel de riesgo: {mc.risk_level.upper()}\n"

                if 'indicators' in data:
                    ind = data['indicators']
                    report += "  Indicadores Técnicos:\n"
                    report += f"    RSI: {ind['rsi']:.2f}\n"
                    report += f"    MACD: {ind['macd']:.2f}\n"
                    report += f"    MACD Signal: {ind['macd_signal']:.2f}\n"
                    report += f"    Bandas de Bollinger:\n"
                    report += f"      Superior: ${ind['bollinger'][0]:,.2f}\n"
                    report += f"      Media: ${ind['bollinger'][1]:,.2f}\n"
                    report += f"      Inferior: ${ind['bollinger'][2]:,.2f}\n"
                    report += f"    Oscilador Estocástico:\n"
                    report += f"      %K: {ind['stochastic'][0]:.2f}\n"
                    report += f"      %D: {ind['stochastic'][1]:.2f}\n"
                    report += f"    ATR: {ind['atr']:.2f}\n"

            return report
        except Exception as e:
            logging.error(f"Error generating report: {e}")
            return f"Error generando reporte: {str(e)}"

    def _analyze_symbol(self, symbol: str, data: Dict) -> Dict:
        """Analiza un símbolo específico usando indicadores técnicos"""
        if 'historical' not in data:
            return {
                'price': data['price'],
                'volume': data['volume'],
                'market_cap': data['market_cap'],
                'change_24h': data['change_24h'],
                'indicators': {
                    'rsi': 50,
                    'macd': 0,
                    'bollinger': [0, 0, 0],
                    'stochastic': [0, 0],
                    'atr': 0
                }
            }

        hist_prices = data['historical']['prices']
        hist_volumes = data['historical']['volumes']

        # Calcular indicadores técnicos
        rsi = TechnicalIndicators.calculate_rsi(hist_prices)[-1]
        macd, signal = TechnicalIndicators.calculate_macd(hist_prices)
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(hist_prices)
        volatility = TechnicalIndicators.calculate_volatility(hist_prices)
        volume_trend = TechnicalIndicators.calculate_volume_profile(hist_volumes)
        k, d = TechnicalIndicators.calculate_stochastic_oscillator(hist_prices)
        atr = TechnicalIndicators.calculate_average_true_range(hist_prices)[-1]

        # Determinar tendencia
        trend = 'neutral'
        if data['change_24h'] > 5 and rsi > 60:
            trend = 'bullish'
        elif data['change_24h'] < -5 and rsi < 40:
            trend = 'bearish'

        # Calcular fuerza de la tendencia
        trend_strength = min(abs(data['change_24h']) / 10, 1.0)

        # Determinar nivel de riesgo
        risk_level = 'medium'
        if volatility > 0.5 or abs(data['change_24h']) > 20:
            risk_level = 'high'
        elif volatility < 0.2 and abs(data['change_24h']) < 5:
            risk_level = 'low'

        return {
            'price': data['price'],
            'volume': data['volume'],
            'market_cap': data['market_cap'],
            'change_24h': data['change_24h'],
            'indicators': {
                'rsi': float(rsi),
                'macd': float(macd[-1]),
                'macd_signal': float(signal[-1]),
                'bollinger': [float(upper[-1]), float(middle[-1]), float(lower[-1])],
                'stochastic': [float(k[-1]), float(d[-1])],
                'atr': float(atr)
            },
            'market_condition': MarketCondition(
                trend=trend,
                strength=trend_strength,
                volatility=float(volatility),
                volume_trend=volume_trend,
                risk_level=risk_level
            )
        }

    async def analyze_market(self):
        """Analiza las condiciones actuales del mercado"""
        try:
            # Obtener datos actualizados
            await self._fetch_market_data()

            if not self.market_data:
                return {
                    'market_conditions': {},
                    'symbol_data': {},
                    'error': 'No market data available'
                }

            # Analizar cada símbolo
            analysis = {
                'market_conditions': {},
                'symbol_data': {}
            }

            total_strength = 0
            total_volatility = 0
            symbols_analyzed = 0

            for symbol, data in self.market_data.items():
                symbol_analysis = self._analyze_symbol(symbol, data)
                analysis['symbol_data'][symbol] = symbol_analysis

                if 'market_condition' in symbol_analysis:
                    total_strength += symbol_analysis['market_condition'].strength
                    total_volatility += symbol_analysis['market_condition'].volatility
                    symbols_analyzed += 1

            # Determinar condición general del mercado
            if symbols_analyzed > 0:
                avg_strength = total_strength / symbols_analyzed
                avg_volatility = total_volatility / symbols_analyzed

                bullish_count = sum(1 for s in analysis['symbol_data'].values()
                                  if 'market_condition' in s and s['market_condition'].trend == 'bullish')
                bearish_count = sum(1 for s in analysis['symbol_data'].values()
                                  if 'market_condition' in s and s['market_condition'].trend == 'bearish')

                if bullish_count > symbols_analyzed * 0.6:
                    analysis['market_conditions'] = 'bullish'
                elif bearish_count > symbols_analyzed * 0.6:
                    analysis['market_conditions'] = 'bearish'

                analysis['market_metrics'] = {
                    'average_strength': float(avg_strength),
                    'average_volatility': float(avg_volatility),
                    'bullish_percentage': float(bullish_count / symbols_analyzed * 100),
                    'bearish_percentage': float(bearish_count / symbols_analyzed * 100)
                }

            return analysis
        except Exception as e:
            logging.error(f"Error analyzing market: {e}")
            return {
                'market_conditions': 'error',
                'symbol_data': {},
                'error': str(e)
            }
