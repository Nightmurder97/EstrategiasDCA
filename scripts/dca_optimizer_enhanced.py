import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Optional
import json
import logging
from dataclasses import dataclass
from scipy.stats import pearsonr

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationConfig:
    """Configuración para el optimizador DCA"""
    weight_sharpe: float = 0.25
    weight_volume: float = 0.20
    weight_momentum: float = 0.20
    weight_return: float = 0.20
    weight_volatility: float = 0.15
    correlation_threshold: float = 0.7
    min_assets: int = 3
    max_assets: int = 8
    risk_free_rate: float = 0.02

class EnhancedDCAOptimizer:
    """
    Optimizador DCA mejorado que incorpora múltiples factores de asignación
    y análisis de correlación para una mejor diversificación.
    """
    def __init__(self, 
                 symbols: List[str], 
                 start_date: datetime, 
                 end_date: datetime,
                 config: Optional[OptimizationConfig] = None):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.config = config or OptimizationConfig()
        self.historical_data = {}
        self.correlation_matrix = None
        self._load_historical_data()
        self._calculate_correlation_matrix()

    def _get_binance_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos históricos de Binance con manejo de errores mejorado"""
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
            response.raise_for_status()
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
                logger.error(f"Error en la respuesta de Binance para {symbol}: {data}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error al obtener datos de Binance para {symbol}: {str(e)}")
            return pd.DataFrame()

    def _load_historical_data(self):
        """Carga datos históricos para todos los símbolos"""
        for symbol in self.symbols:
            logger.info(f"Cargando datos para {symbol}...")
            data = self._get_binance_data(symbol)
            if not data.empty:
                self.historical_data[symbol] = data
                logger.info(f"Datos cargados exitosamente para {symbol}")
            else:
                logger.warning(f"No se encontraron datos para {symbol}")

    def _calculate_correlation_matrix(self):
        """Calcula la matriz de correlación entre los activos"""
        returns_data = {}
        for symbol, data in self.historical_data.items():
            returns_data[symbol] = data['close'].pct_change().dropna()
        
        returns_df = pd.DataFrame(returns_data)
        self.correlation_matrix = returns_df.corr()

    def calculate_asset_metrics(self) -> pd.DataFrame:
        """
        Calcula métricas avanzadas para cada activo incluyendo Sharpe,
        volumen, momentum, retorno y volatilidad.
        """
        metrics = {}
        for symbol, data in self.historical_data.items():
            # Calcular retornos diarios
            returns = data['close'].pct_change().dropna()
            
            # Métricas básicas
            avg_volume = data['volume'].mean()
            price_return = (data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0]
            volatility = returns.std() * np.sqrt(252)
            
            # Calcular Sharpe Ratio
            excess_returns = (price_return - self.config.risk_free_rate)
            sharpe = excess_returns / volatility if volatility != 0 else 0
            
            # Calcular Momentum (retorno de los últimos 30 días)
            momentum = (data['close'].iloc[-1] - data['close'].iloc[-30]) / data['close'].iloc[-30] \
                if len(data) >= 30 else price_return
            
            metrics[symbol] = {
                'sharpe': sharpe,
                'volume': avg_volume,
                'momentum': momentum,
                'return': price_return,
                'volatility': volatility
            }
        
        # Crear DataFrame y normalizar métricas
        metrics_df = pd.DataFrame.from_dict(metrics, orient='index')
        for column in metrics_df.columns:
            if column != 'volatility':
                metrics_df[f'{column}_score'] = (metrics_df[column] - metrics_df[column].min()) / \
                    (metrics_df[column].max() - metrics_df[column].min())
            else:
                # Para volatilidad, menor es mejor
                metrics_df[f'{column}_score'] = 1 - (metrics_df[column] - metrics_df[column].min()) / \
                    (metrics_df[column].max() - metrics_df[column].min())
        
        # Calcular score total ponderado
        metrics_df['total_score'] = (
            self.config.weight_sharpe * metrics_df['sharpe_score'] +
            self.config.weight_volume * metrics_df['volume_score'] +
            self.config.weight_momentum * metrics_df['momentum_score'] +
            self.config.weight_return * metrics_df['return_score'] +
            self.config.weight_volatility * metrics_df['volatility_score']
        )
        
        return metrics_df

    def optimize_portfolio(self, weekly_investment: float) -> Tuple[Dict, pd.DataFrame]:
        """
        Optimiza la distribución del portafolio priorizando los activos existentes
        y evaluando la incorporación de nuevos activos de manera estratégica.
        """
        # Definir activos existentes y nuevos
        existing_symbols = ["BTCUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT", "DOGEUSDT"]
        available_symbols = [symbol for symbol in self.symbols if symbol in self.historical_data]
        new_symbols = [symbol for symbol in available_symbols if symbol not in existing_symbols]
        
        logger.info("\nOptimizando portafolio con activos existentes...")
        
        # 1. Optimización inicial con activos existentes
        metrics_df = self.calculate_asset_metrics()
        existing_metrics = metrics_df.loc[existing_symbols]
        
        # Normalizar scores solo para activos existentes
        existing_scores = existing_metrics['total_score']
        initial_weights = existing_scores / existing_scores.sum()
        
        # Calcular métricas del portafolio inicial
        initial_portfolio = {symbol: {'weight': weight} for symbol, weight in initial_weights.items()}
        initial_metrics = self.calculate_portfolio_metrics(weekly_investment, dict(initial_weights))
        
        best_portfolio = initial_metrics
        best_weights = dict(initial_weights)
        
        logger.info("\nEvaluando incorporación de nuevos activos...")
        
        # 2. Evaluar incorporación de nuevos activos
        for new_symbol in new_symbols:
            # Verificar correlaciones con activos existentes
            correlations = [abs(self.correlation_matrix.loc[new_symbol, existing]) 
                          for existing in existing_symbols]
            
            # Solo considerar activos con baja correlación
            if max(correlations) >= self.config.correlation_threshold:
                continue
                
            # Añadir el nuevo activo al conjunto
            current_symbols = existing_symbols + [new_symbol]
            current_metrics = metrics_df.loc[current_symbols]
            
            # Recalcular pesos incluyendo el nuevo activo
            current_scores = current_metrics['total_score']
            current_weights = current_scores / current_scores.sum()
            
            # Asegurar peso mínimo para activos existentes
            min_existing_weight = 0.1  # 10% mínimo para cada activo existente
            for existing in existing_symbols:
                if current_weights[existing] < min_existing_weight:
                    current_weights[existing] = min_existing_weight
            
            # Normalizar pesos
            current_weights = current_weights / current_weights.sum()
            
            # Calcular métricas del nuevo portafolio
            current_portfolio = self.calculate_portfolio_metrics(weekly_investment, dict(current_weights))
            
            # Evaluar si el nuevo portafolio es mejor
            if (current_portfolio['portfolio']['sharpe_ratio'] > best_portfolio['portfolio']['sharpe_ratio'] and
                current_portfolio['portfolio']['max_drawdown'] > best_portfolio['portfolio']['max_drawdown']):
                
                logger.info(f"\nMejora encontrada al añadir {new_symbol}:")
                logger.info(f"Sharpe Ratio: {current_portfolio['portfolio']['sharpe_ratio']:.2f} vs {best_portfolio['portfolio']['sharpe_ratio']:.2f}")
                logger.info(f"Max Drawdown: {current_portfolio['portfolio']['max_drawdown']:.2f}% vs {best_portfolio['portfolio']['max_drawdown']:.2f}%")
                
                best_portfolio = current_portfolio
                best_weights = dict(current_weights)
        
        return best_portfolio, metrics_df

    def calculate_portfolio_metrics(self, investment_amount: float, portfolio_weights: Dict[str, float]) -> Dict:
        """Calcula métricas detalladas del portafolio"""
        results = {}
        portfolio_value = 0
        portfolio_investment = 0
        
        for symbol, weight in portfolio_weights.items():
            if symbol in self.historical_data:
                prices = self.historical_data[symbol]['close']
                
                symbol_investment = investment_amount * weight
                coins_bought = symbol_investment / prices.iloc[0]
                final_value = coins_bought * prices.iloc[-1]
                
                daily_returns = prices.pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252) * 100
                roi = (final_value - symbol_investment) / symbol_investment * 100
                
                # Calcular métricas adicionales
                max_drawdown = ((prices / prices.expanding().max()) - 1).min() * 100
                sortino_ratio = self._calculate_sortino_ratio(daily_returns)
                
                results[symbol] = {
                    'weight': weight,
                    'investment': symbol_investment,
                    'final_value': final_value,
                    'roi': roi,
                    'volatility': volatility,
                    'max_drawdown': max_drawdown,
                    'sortino_ratio': sortino_ratio
                }
                
                portfolio_value += final_value
                portfolio_investment += symbol_investment
        
        if portfolio_investment > 0:
            # Calcular métricas del portafolio completo
            portfolio_roi = (portfolio_value - portfolio_investment) / portfolio_investment * 100
            
            portfolio_returns = pd.Series(0.0, index=self.historical_data[list(self.historical_data.keys())[0]]['close'].index)
            for symbol, weight in portfolio_weights.items():
                if symbol in self.historical_data:
                    symbol_returns = self.historical_data[symbol]['close'].pct_change()
                    portfolio_returns += symbol_returns * weight
            
            portfolio_volatility = portfolio_returns.std() * np.sqrt(252) * 100
            portfolio_sharpe = self._calculate_sharpe_ratio(portfolio_returns)
            portfolio_sortino = self._calculate_sortino_ratio(portfolio_returns)
            portfolio_max_drawdown = ((1 + portfolio_returns).cumprod() / (1 + portfolio_returns).cumprod().expanding().max() - 1).min() * 100
            
            results['portfolio'] = {
                'total_investment': portfolio_investment,
                'final_value': portfolio_value,
                'roi': portfolio_roi,
                'volatility': portfolio_volatility,
                'sharpe_ratio': portfolio_sharpe,
                'sortino_ratio': portfolio_sortino,
                'max_drawdown': portfolio_max_drawdown
            }
        
        return results

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calcula el Ratio de Sharpe anualizado"""
        if returns.empty or returns.std() == 0:
            return 0
        
        excess_returns = returns.mean() * 252 - self.config.risk_free_rate
        return excess_returns / (returns.std() * np.sqrt(252))

    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calcula el Ratio de Sortino anualizado"""
        if returns.empty:
            return 0
        
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0 or negative_returns.std() == 0:
            return 0
        
        excess_returns = returns.mean() * 252 - self.config.risk_free_rate
        downside_std = negative_returns.std() * np.sqrt(252)
        return excess_returns / downside_std

    def plot_portfolio_analysis(self, portfolio_metrics: Dict, metrics_df: pd.DataFrame):
        """
        Genera visualizaciones detalladas del análisis del portafolio incluyendo:
        - Distribución de activos
        - Métricas de rendimiento
        - Matriz de correlación
        - Factores de asignación
        """
        plt.style.use('seaborn')
        fig = plt.figure(figsize=(20, 15))
        
        # 1. Distribución del portafolio
        ax1 = plt.subplot2grid((3, 3), (0, 0))
        symbols = [k for k in portfolio_metrics.keys() if k != 'portfolio']
        weights = [portfolio_metrics[k]['weight'] for k in symbols]
        ax1.pie(weights, labels=symbols, autopct='%1.1f%%')
        ax1.set_title('Distribución del Portafolio')
        
        # 2. Métricas de rendimiento
        ax2 = plt.subplot2grid((3, 3), (0, 1))
        metrics = ['roi', 'volatility', 'max_drawdown']
        for symbol in symbols:
            values = [portfolio_metrics[symbol][metric] for metric in metrics]
            ax2.bar(metrics, values, alpha=0.5, label=symbol)
        ax2.set_title('Métricas por Activo')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 3. Matriz de correlación
        ax3 = plt.subplot2grid((3, 3), (1, 0), colspan=2)
        sns.heatmap(self.correlation_matrix, annot=True, cmap='RdYlGn', center=0, ax=ax3)
        ax3.set_title('Matriz de Correlación')
        
        # 4. Factores de asignación
        ax4 = plt.subplot2grid((3, 3), (2, 0), colspan=2)
        factor_cols = ['sharpe_score', 'volume_score', 'momentum_score', 'return_score', 'volatility_score']
        selected_metrics = metrics_df.loc[symbols, factor_cols]
        sns.heatmap(selected_metrics, annot=True, cmap='YlGnBu', ax=ax4)
        ax4.set_title('Factores de Asignación')
        
        plt.tight_layout()
        return fig

def main():
    try:
        # Cargar configuración
        config = {
            'symbols': [
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
            ],
            'start_date': '2024-07-17',
            'end_date': '2025-01-17',
            'weekly_investment': 100,
            'weight_sharpe': 0.25,
            'weight_volume': 0.20,
            'weight_momentum': 0.20,
            'weight_return': 0.20,
            'weight_volatility': 0.15,
            'correlation_threshold': 0.7,
            'min_assets': 3,
            'max_assets': 10
        }
        
        start_date = datetime.strptime(config['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(config['end_date'], '%Y-%m-%d')
        weekly_investment = config['weekly_investment']
        
        print(f"\nPeríodo de análisis (últimos 6 meses de datos históricos):")
        print(f"Fecha de inicio: {start_date.strftime('%d/%m/%Y')}")
        print(f"Fecha de fin: {end_date.strftime('%d/%m/%Y')}")
        print(f"Duración: 6 meses\n")

        # Configurar optimizador
        optimization_config = OptimizationConfig(
            weight_sharpe=config['weight_sharpe'],
            weight_volume=config['weight_volume'],
            weight_momentum=config['weight_momentum'],
            weight_return=config['weight_return'],
            weight_volatility=config['weight_volatility'],
            correlation_threshold=config['correlation_threshold'],
            min_assets=config['min_assets'],
            max_assets=config['max_assets']
        )
        
        logger.info(f"Iniciando optimización para el período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
        
        # Crear y ejecutar el optimizador
        optimizer = EnhancedDCAOptimizer(symbols, start_date, end_date, optimization_config)
        portfolio_metrics, metrics_df = optimizer.optimize_portfolio(weekly_investment)
        
        if portfolio_metrics:
            logger.info("\nResultados del Portafolio Optimizado:")
            
            print("\nDistribución del portafolio:")
            for symbol, metrics in portfolio_metrics.items():
                if symbol != 'portfolio':
                    print(f"{symbol}: {metrics['weight']*100:.2f}% - Inversión semanal: {metrics['investment']:.2f} EUR")
            
            print("\nMétricas del portafolio:")
            portfolio = portfolio_metrics['portfolio']
            print(f"ROI total: {portfolio['roi']:.2f}%")
            print(f"Volatilidad: {portfolio['volatility']:.2f}%")
            print(f"Ratio de Sharpe: {portfolio['sharpe_ratio']:.2f}")
            print(f"Ratio de Sortino: {portfolio['sortino_ratio']:.2f}")
            print(f"Máximo Drawdown: {portfolio['max_drawdown']:.2f}%")
            
            # Generar y guardar visualizaciones
            fig = optimizer.plot_portfolio_analysis(portfolio_metrics, metrics_df)
            fig.savefig('portfolio_analysis.png', bbox_inches='tight', dpi=300)
            plt.close(fig)
            
            # Guardar resultados en JSON
            results = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'portfolio_metrics': portfolio_metrics,
                'optimization_metrics': metrics_df.to_dict()
            }
            
            with open('optimization_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info("Análisis completado. Resultados guardados en 'optimization_results.json' y 'portfolio_analysis.png'")
        else:
            logger.error("No se pudo encontrar una estrategia óptima.")
            
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")

if __name__ == "__main__":
    main() 