import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import json


class DCAOptimizer:
    def __init__(self, symbols: List[str], start_date: datetime, end_date: datetime, config_path: str = "data/config.json"):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.historical_data = {}
        
        # Load configuration
        self.config = self._load_config(config_path)
        self.weight_sharpe = self.config.get("weight_sharpe", 0.25)
        self.weight_volume = self.config.get("weight_volume", 0.20)
        self.weight_momentum = self.config.get("weight_momentum", 0.20)
        self.weight_return = self.config.get("weight_return", 0.20)
        self.weight_volatility = self.config.get("weight_volatility", 0.15)
        self.risk_free_rate = self.config.get("risk_free_rate", 0.02)
        self.min_assets = self.config.get("min_assets", 3)
        self.max_assets = self.config.get("max_assets", 8)
        self.correlation_threshold = self.config.get("correlation_threshold", 0.7)
        
        self._load_historical_data()

    def _load_config(self, config_path: str) -> dict:
        """Load optimization configuration from JSON file"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {str(e)}")
            print("Using default configuration values")
            return {}

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

    def _calculate_correlation_matrix(self) -> pd.DataFrame:
        """Calcula la matriz de correlación entre los activos"""
        returns = pd.DataFrame()
        for symbol, data in self.historical_data.items():
            returns[symbol] = data['close'].pct_change().dropna()
        return returns.corr()

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

    def optimize_portfolio(self, weekly_investment: float) -> Tuple[Dict, pd.DataFrame]:
        """Optimiza la distribución del portafolio usando múltiples factores"""
        # Calcular métricas para cada criptomoneda
        asset_metrics = {}
        for symbol, data in self.historical_data.items():
            # Calcular métricas básicas
            returns = data['close'].pct_change().dropna()
            avg_volume = data['volume'].mean()
            price_return = (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0]
            volatility = returns.std() * np.sqrt(252)
            momentum = (data['close'].iloc[-1] - data['close'].iloc[-21]) / data['close'].iloc[-21]  # 21-day momentum
            
            # Calcular Sharpe ratio
            excess_returns = returns - self.risk_free_rate/252
            sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            
            asset_metrics[symbol] = {
                'avg_volume': avg_volume,
                'return': price_return,
                'volatility': volatility,
                'momentum': momentum,
                'sharpe': sharpe
            }
        
        # Crear DataFrame con métricas
        metrics_df = pd.DataFrame.from_dict(asset_metrics, orient='index')
        
        # Normalizar métricas
        metrics_df['volume_score'] = metrics_df['avg_volume'] / metrics_df['avg_volume'].max()
        metrics_df['return_score'] = (metrics_df['return'] - metrics_df['return'].min()) / (metrics_df['return'].max() - metrics_df['return'].min())
        metrics_df['volatility_score'] = 1 - (metrics_df['volatility'] / metrics_df['volatility'].max())  # Invertir volatilidad
        metrics_df['momentum_score'] = (metrics_df['momentum'] - metrics_df['momentum'].min()) / (metrics_df['momentum'].max() - metrics_df['momentum'].min())
        metrics_df['sharpe_score'] = (metrics_df['sharpe'] - metrics_df['sharpe'].min()) / (metrics_df['sharpe'].max() - metrics_df['sharpe'].min())
        
        # Calcular score combinado usando pesos del config
        metrics_df['total_score'] = (
            self.weight_sharpe * metrics_df['sharpe_score'] +
            self.weight_volume * metrics_df['volume_score'] +
            self.weight_momentum * metrics_df['momentum_score'] +
            self.weight_return * metrics_df['return_score'] +
            self.weight_volatility * metrics_df['volatility_score']
        )
        
        # Ordenar activos por score total
        sorted_assets = metrics_df.sort_values('total_score', ascending=False)
        
        # Seleccionar activos basados en correlación
        selected_assets = []
        correlation_matrix = self._calculate_correlation_matrix()
        
        for symbol in sorted_assets.index:
            if len(selected_assets) >= self.max_assets:
                break
                
            # Verificar correlación con activos ya seleccionados
            add_asset = True
            for selected_symbol in selected_assets:
                if abs(correlation_matrix.loc[symbol, selected_symbol]) > self.correlation_threshold:
                    add_asset = False
                    break
                    
            if add_asset:
                selected_assets.append(symbol)
                
        # Asegurar mínimo de activos
        if len(selected_assets) < self.min_assets:
            # Agregar los mejores activos restantes sin considerar correlación
            remaining_assets = [s for s in sorted_assets.index if s not in selected_assets]
            needed = self.min_assets - len(selected_assets)
            selected_assets.extend(remaining_assets[:needed])
            
        # Calcular pesos basados en el score total
        selected_metrics = metrics_df.loc[selected_assets]
        weights = selected_metrics['total_score'] / selected_metrics['total_score'].sum()
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
    # Lista actualizada de las principales criptomonedas con sus pesos de mercado
    symbols = [
        'BTCUSDT',   # 61.92% - $104,868.19
        'ETHUSDT',   # 12.27% - $3,416.44
        'XRPUSDT',   # 5.51% - $3.21
        'SOLUSDT',   # 3.14% - $216.70
        'BNBUSDT',   # 3.10% - $722.66
        'DOGEUSDT',  # 1.80% - $0.41
        'ADAUSDT',   # 1.18% - $1.12
        'TRXUSDT',   # 0.63% - $0.2468
        'AVAXUSDT',  # 0.50% - $40.82
        'LINKUSDT'   # 0.46% - $24.45
    ]
    
    # Usar los últimos 6 meses de datos históricos
    end_date = datetime(2025, 1, 17)  # Fecha actual
    start_date = datetime(2024, 7, 17)  # 6 meses atrás
    
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
