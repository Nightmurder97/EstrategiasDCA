import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple


class DCAOptimizer:
    def __init__(self, symbols: List[str], start_date: datetime, end_date: datetime):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.historical_data = {}
        self._load_historical_data()

    def _get_binance_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos históricos de Binance"""
        base_url = "https://api.binance.com/api/v3/klines"
        interval = "1d"  # Datos diarios
        
        # Convertir fechas a timestamp en milisegundos
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

    def calculate_portfolio_metrics(self, investment_amount: float, portfolio_weights: Dict[str, float]) -> Dict:
        """Calcula métricas de rendimiento para una cartera DCA"""
        results = {}
        portfolio_value = 0
        portfolio_investment = 0
        
        # Calcular métricas para cada criptomoneda en el portafolio
        for symbol, weight in portfolio_weights.items():
            if symbol in self.historical_data:
                prices = self.historical_data[symbol]['close']
                
                # Calcular inversión y monedas compradas
                symbol_investment = investment_amount * weight
                coins_bought = symbol_investment / prices.iloc[0]
                final_value = coins_bought * prices.iloc[-1]
                
                # Calcular métricas individuales
                roi = (final_value - symbol_investment) / symbol_investment * 100
                daily_returns = prices.pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252) * 100
                
                results[symbol] = {
                    'weight': weight,
                    'investment': symbol_investment,
                    'final_value': final_value,
                    'roi': roi,
                    'volatility': volatility
                }
                
                portfolio_value += final_value
                portfolio_investment += symbol_investment
        
        # Calcular métricas del portafolio
        if portfolio_investment > 0:
            portfolio_roi = (portfolio_value - portfolio_investment) / portfolio_investment * 100
            
            # Calcular volatilidad del portafolio
            portfolio_returns = pd.Series(0.0, index=self.historical_data[list(self.historical_data.keys())[0]]['close'].index)
            for symbol, weight in portfolio_weights.items():
                if symbol in self.historical_data:
                    symbol_returns = self.historical_data[symbol]['close'].pct_change()
                    portfolio_returns += symbol_returns * weight
            
            portfolio_volatility = portfolio_returns.std() * np.sqrt(252) * 100
            
            # Calcular Ratio de Sharpe del portafolio
            risk_free_rate = 0.02
            excess_returns = (portfolio_roi / 100) - risk_free_rate
            portfolio_sharpe = excess_returns / (portfolio_volatility / 100) if portfolio_volatility != 0 else 0
            
            results['portfolio'] = {
                'total_investment': portfolio_investment,
                'final_value': portfolio_value,
                'roi': portfolio_roi,
                'volatility': portfolio_volatility,
                'sharpe_ratio': portfolio_sharpe
            }
        
        return results

    def optimize_portfolio(self, weekly_investment: float, num_assets: int = 5) -> Tuple[Dict, pd.DataFrame]:
        """Optimiza la distribución del portafolio basado en volumen y rendimiento"""
        # Calcular volumen promedio y rendimiento para cada criptomoneda
        asset_metrics = {}
        for symbol, data in self.historical_data.items():
            avg_volume = data['volume'].mean()
            price_return = (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0]
            asset_metrics[symbol] = {
                'avg_volume': avg_volume,
                'return': price_return
            }
        
        # Crear DataFrame con métricas
        metrics_df = pd.DataFrame.from_dict(asset_metrics, orient='index')
        
        # Normalizar métricas
        metrics_df['volume_score'] = metrics_df['avg_volume'] / metrics_df['avg_volume'].max()
        metrics_df['return_score'] = (metrics_df['return'] - metrics_df['return'].min()) / (metrics_df['return'].max() - metrics_df['return'].min())
        
        # Calcular score combinado (50% volumen, 50% rendimiento)
        metrics_df['total_score'] = 0.5 * metrics_df['volume_score'] + 0.5 * metrics_df['return_score']
        
        # Seleccionar las mejores n criptomonedas
        top_assets = metrics_df.nlargest(num_assets, 'total_score')
        
        # Calcular pesos basados en el score total
        weights = top_assets['total_score'] / top_assets['total_score'].sum()
        portfolio_weights = weights.to_dict()
        
        # Calcular métricas del portafolio optimizado
        portfolio_metrics = self.calculate_portfolio_metrics(weekly_investment, portfolio_weights)
        
        return portfolio_metrics, metrics_df

    def plot_portfolio_results(self, portfolio_metrics: Dict):
        """Visualiza los resultados del portafolio"""
        if not portfolio_metrics:
            print("No hay datos para visualizar")
            return

        plt.figure(figsize=(15, 10))
        
        # Gráfico de distribución del portafolio
        plt.subplot(2, 2, 1)
        symbols = [k for k in portfolio_metrics.keys() if k != 'portfolio']
        weights = [portfolio_metrics[k]['weight'] for k in symbols]
        plt.pie(weights, labels=symbols, autopct='%1.1f%%')
        plt.title('Distribución del Portafolio')
        
        # Gráfico de ROI por activo
        plt.subplot(2, 2, 2)
        rois = [portfolio_metrics[k]['roi'] for k in symbols]
        plt.bar(symbols, rois)
        plt.xticks(rotation=45)
        plt.ylabel('ROI (%)')
        plt.title('ROI por Criptomoneda')
        
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
    
    # Usar los últimos 6 meses de datos históricos
    end_date = datetime(2025, 1, 6)  # Fecha actual
    start_date = datetime(2024, 7, 10)  # 6 meses atrás
    
    print(f"\nPeríodo de análisis (últimos 6 meses de datos históricos):")
    print(f"Fecha de inicio: {start_date.strftime('%d/%m/%Y')}")
    print(f"Fecha de fin: {end_date.strftime('%d/%m/%Y')}")
    print(f"Duración: 6 meses\n")
    
    weekly_investment = 100  # EUR por semana
    
    # Crear y ejecutar el optimizador
    optimizer = DCAOptimizer(symbols, start_date, end_date)
    portfolio_metrics, metrics_df = optimizer.optimize_portfolio(weekly_investment)
    
    if portfolio_metrics:
        print("\nResultados del Portafolio Optimizado:")
        print("\nDistribución del portafolio:")
        for symbol, metrics in portfolio_metrics.items():
            if symbol != 'portfolio':
                print(f"{symbol}: {metrics['weight']*100:.2f}% - Inversión semanal: {metrics['investment']:.2f} EUR")
        
        print("\nMétricas del portafolio:")
        portfolio = portfolio_metrics['portfolio']
        print(f"ROI total: {portfolio['roi']:.2f}%")
        print(f"Volatilidad: {portfolio['volatility']:.2f}%")
        print(f"Ratio de Sharpe: {portfolio['sharpe_ratio']:.2f}")
        
        # Visualizar resultados
        optimizer.plot_portfolio_results(portfolio_metrics)
    else:
        print("No se pudo encontrar una estrategia óptima.")


if __name__ == "__main__":
    main() 