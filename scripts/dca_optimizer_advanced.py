import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class DCAParameters:
    base_investment: float  # Inversión base semanal
    rsi_period: int = 14  # Período para calcular RSI
    rsi_oversold: float = 30  # Nivel de sobreventa
    rsi_overbought: float = 70  # Nivel de sobrecompra
    price_drop_threshold: float = 0.15  # Caída de precio significativa (15%)
    price_increase_threshold: float = 0.30  # Subida de precio significativa (30%)
    max_investment_multiplier: float = 2.0  # Multiplicador máximo para inversión
    rebalancing_threshold: float = 0.05  # Umbral para reequilibrio (5% de desviación)


class AdvancedDCAOptimizer:
    def __init__(self, symbols: List[str], start_date: datetime, end_date: datetime, params: DCAParameters):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.params = params
        self.historical_data = {}
        self._load_historical_data()

    def _get_binance_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos históricos de Binance"""
        base_url = "https://api.binance.com/api/v3/klines"
        interval = "1d"
        
        start_ts = int(self.start_date.timestamp() * 1000)
        end_ts = int(self.end_date.timestamp() * 1000)
        
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000
        }
        
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if isinstance(data, list):
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 
                                               'volume', 'close_time', 'quote_volume', 'trades',
                                               'taker_buy_base', 'taker_buy_quote', 'ignore'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(float)
                return df.set_index('timestamp')[['close', 'volume']]
            else:
                print(f"Error en la respuesta de Binance para {symbol}: {data}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error al obtener datos de Binance para {symbol}: {str(e)}")
            return pd.DataFrame()

    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calcula el RSI para una serie de precios"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params.rsi_period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_dynamic_investment(self, price: float, avg_price: float, rsi: float, weight: float) -> float:
        """Calcula la inversión dinámica basada en precio, RSI y peso del activo"""
        # Inversión base según el peso del activo
        base_investment = self.params.base_investment * weight
        investment = base_investment
        
        # Ajuste por caída de precio
        if price < avg_price * (1 - self.params.price_drop_threshold):
            # Aumentar la inversión en este activo reduciendo proporcionalmente de otros
            investment *= 1.5
        
        # Ajuste por RSI
        if rsi <= self.params.rsi_oversold:
            investment *= 1.5
        elif rsi >= self.params.rsi_overbought:
            investment *= 0.5
        
        # Limitar el multiplicador máximo manteniendo el presupuesto total
        return min(investment, base_investment * self.params.max_investment_multiplier)

    def optimize_portfolio(self) -> Dict:
        """Optimiza el portafolio usando estrategia DCA avanzada"""
        # Calcular métricas iniciales para cada activo
        initial_metrics = {}
        for symbol in self.symbols:
            if symbol not in self.historical_data:
                continue
                
            data = self.historical_data[symbol]
            prices = data['close']
            returns = prices.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            sharpe = returns.mean() / volatility if volatility != 0 else 0
            
            initial_metrics[symbol] = {
                'sharpe': sharpe,
                'volatility': volatility,
                'avg_volume': data['volume'].mean()
            }
        
        # Seleccionar los 5 mejores activos basados en Sharpe ratio y volumen
        top_assets = sorted(
            initial_metrics.items(),
            key=lambda x: (x[1]['sharpe'] * 0.7 + x[1]['avg_volume'] / max(m['avg_volume'] for m in initial_metrics.values()) * 0.3),
            reverse=True
        )[:5]
        
        # Calcular pesos iniciales basados en Sharpe ratio
        total_sharpe = sum(abs(metrics['sharpe']) for symbol, metrics in top_assets)
        weights = {
            symbol: max(0.1, abs(metrics['sharpe']) / total_sharpe) 
            for symbol, metrics in top_assets
        }
        
        # Normalizar pesos para sumar 100%
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        # Simular inversiones con los pesos calculados
        portfolio_results = {}
        weekly_investments = {symbol: weight * 100 for symbol, weight in weights.items()}  # 100€ semanales en total
        
        for symbol, weekly_amount in weekly_investments.items():
            data = self.historical_data[symbol]
            prices = data['close']
            rsi = self._calculate_rsi(prices)
            
            total_investment = 0
            total_coins = 0
            avg_price = prices.iloc[0]
            investment_dates = []
            
            # Simular inversiones semanales
            current_date = prices.index[0]
            num_weeks = 0
            while current_date <= prices.index[-1]:
                if current_date in prices.index:
                    price = prices[current_date]
                    current_rsi = rsi[current_date] if current_date in rsi.index else 50
                    
                    # Inversión fija semanal según el peso asignado
                    investment = weekly_amount
                    
                    # Realizar inversión
                    coins_bought = investment / price
                    total_coins += coins_bought
                    total_investment += investment
                    
                    # Actualizar precio promedio
                    avg_price = total_investment / total_coins
                    investment_dates.append(current_date)
                    num_weeks += 1
                
                current_date += timedelta(days=7)
            
            # Calcular métricas finales
            if total_investment > 0:
                final_value = total_coins * prices.iloc[-1]
                roi = (final_value - total_investment) / total_investment * 100
                daily_returns = prices.pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252) * 100
                
                portfolio_results[symbol] = {
                    'weight': weights[symbol],
                    'weekly_investment': weekly_amount,
                    'total_investment': total_investment,
                    'final_value': final_value,
                    'roi': roi,
                    'volatility': volatility,
                    'avg_price': avg_price,
                    'total_coins': total_coins,
                    'num_investments': len(investment_dates)
                }
        
        return portfolio_results

    def _load_historical_data(self):
        """Carga datos históricos para todos los símbolos"""
        for symbol in self.symbols:
            print(f"Cargando datos para {symbol}...")
            data = self._get_binance_data(symbol)
            if not data.empty:
                self.historical_data[symbol] = data
                print(f"Datos cargados exitosamente para {symbol}")
            else:
                print(f"No se encontraron datos para {symbol}")

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
    # Lista de las 30 principales criptomonedas en Binance
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'MATICUSDT',
        'SOLUSDT', 'DOTUSDT', 'LTCUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'ATOMUSDT',
        'ETCUSDT', 'XLMUSDT', 'VETUSDT', 'TRXUSDT', 'ALGOUSDT', 'ICPUSDT', 'FILUSDT',
        'AAVEUSDT', 'XTZUSDT', 'AXSUSDT', 'THETAUSDT', 'EOSUSDT', 'CAKEUSDT', 'NEARUSDT',
        'FTMUSDT', 'RUNEUSDT'
    ]
    
    # Configurar fechas
    end_date = datetime(2025, 1, 6)  # Fecha actual
    start_date = datetime(2024, 7, 10)  # 6 meses atrás
    
    print(f"\nPeríodo de análisis (últimos 6 meses de datos históricos):")
    print(f"Fecha de inicio: {start_date.strftime('%d/%m/%Y')}")
    print(f"Fecha de fin: {end_date.strftime('%d/%m/%Y')}")
    print(f"Duración: 6 meses\n")
    
    # Configurar parámetros de la estrategia DCA
    params = DCAParameters(
        base_investment=100,  # 100 EUR base semanal
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70,
        price_drop_threshold=0.15,
        price_increase_threshold=0.30,
        max_investment_multiplier=2.0,
        rebalancing_threshold=0.05
    )
    
    # Crear y ejecutar el optimizador avanzado
    optimizer = AdvancedDCAOptimizer(symbols, start_date, end_date, params)
    portfolio_results = optimizer.optimize_portfolio()
    
    if portfolio_results:
        print("\nResultados del Portafolio Optimizado (Estrategia DCA Avanzada):")
        print("\nDistribución del portafolio y métricas por activo:")
        
        total_portfolio_value = sum(r['final_value'] for r in portfolio_results.values())
        total_portfolio_investment = sum(r['total_investment'] for r in portfolio_results.values())
        
        for symbol, metrics in portfolio_results.items():
            print(f"\n{symbol}:")
            print(f"  Peso en portafolio: {metrics['weight']*100:.2f}%")
            print(f"  Inversión total: {metrics['total_investment']:.2f} EUR")
            print(f"  Valor final: {metrics['final_value']:.2f} EUR")
            print(f"  ROI: {metrics['roi']:.2f}%")
            print(f"  Volatilidad: {metrics['volatility']:.2f}%")
            print(f"  Precio promedio: {metrics['avg_price']:.2f} USD")
            print(f"  Total monedas: {metrics['total_coins']:.6f}")
        
        print(f"\nMétricas del portafolio completo:")
        portfolio_roi = (total_portfolio_value - total_portfolio_investment) / total_portfolio_investment * 100
        print(f"Inversión total: {total_portfolio_investment:.2f} EUR")
        print(f"Valor final: {total_portfolio_value:.2f} EUR")
        print(f"ROI total: {portfolio_roi:.2f}%")
        
        # Visualizar resultados
        optimizer.plot_results(portfolio_results)
    else:
        print("No se pudo encontrar una estrategia óptima.")


if __name__ == "__main__":
    main() 