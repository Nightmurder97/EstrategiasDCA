import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')


@dataclass
class DCAParameters:
    base_investment: float
    rsi_period: int = 14
    price_drop_threshold: float = 0.15
    max_correlation: float = 0.7
    min_volume_percentile: float = 25


class FastDCAOptimizer:
    def __init__(self, symbols: List[str], start_date: datetime, end_date: datetime, params: DCAParameters):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.params = params
        self.historical_data = {}
        self._load_historical_data_parallel()

    def _get_binance_data(self, symbol: str) -> pd.DataFrame:
        """Obtiene datos históricos de Binance de forma eficiente"""
        base_url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": int(self.start_date.timestamp() * 1000),
            "endTime": int(self.end_date.timestamp() * 1000),
            "limit": 1000
        }
        
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if isinstance(data, list):
                df = pd.DataFrame(data)[[0, 4, 5]]  # Solo timestamp, close, volume
                df.columns = ['timestamp', 'close', 'volume']
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(float)
                return df.set_index('timestamp')
            return pd.DataFrame()
        except:
            return pd.DataFrame()

    def _load_single_symbol(self, symbol: str):
        """Carga datos para un símbolo individual"""
        print(f"Cargando datos para {symbol}...")
        data = self._get_binance_data(symbol)
        if not data.empty:
            self.historical_data[symbol] = data
            print(f"Datos cargados exitosamente para {symbol}")
        return symbol, data

    def _load_historical_data_parallel(self):
        """Carga datos históricos en paralelo"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._load_single_symbol, symbol) for symbol in self.symbols]
            self.historical_data = {
                symbol: data for symbol, data in [future.result() for future in futures]
                if not data.empty
            }

    def _calculate_metrics(self, data: pd.DataFrame) -> Dict:
        """Calcula métricas básicas de forma eficiente"""
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        sharpe = returns.mean() / volatility if volatility != 0 else 0
        volume_rank = data['volume'].rank(pct=True).mean()
        
        return {
            'sharpe': sharpe,
            'volatility': volatility,
            'volume_rank': volume_rank
        }

    def optimize_portfolio(self) -> Dict:
        """Optimiza el portafolio de forma eficiente"""
        # Calcular métricas iniciales
        metrics = {
            symbol: self._calculate_metrics(data)
            for symbol, data in self.historical_data.items()
        }
        
        # Filtrar por volumen
        filtered_symbols = [
            symbol for symbol, m in metrics.items()
            if m['volume_rank'] >= (self.params.min_volume_percentile / 100)
        ]
        
        # Seleccionar top 5 por Sharpe ratio
        top_symbols = sorted(
            filtered_symbols,
            key=lambda s: metrics[s]['sharpe'],
            reverse=True
        )[:5]
        
        # Calcular pesos
        total_sharpe = sum(metrics[s]['sharpe'] for s in top_symbols)
        weights = {
            s: max(0.1, metrics[s]['sharpe'] / total_sharpe)
            for s in top_symbols
        }
        
        # Normalizar pesos
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        # Simular inversiones
        results = {}
        weekly_investment = {s: w * self.params.base_investment for s, w in weights.items()}
        
        for symbol in top_symbols:
            data = self.historical_data[symbol]
            prices = data['close']
            
            # Calcular inversiones semanales
            dates = pd.date_range(start=prices.index[0], end=prices.index[-1], freq='W')
            investments = pd.Series(weekly_investment[symbol], index=dates)
            
            # Calcular compras
            valid_investments = investments[investments.index.isin(prices.index)]
            coins_bought = valid_investments / prices[valid_investments.index]
            
            total_investment = valid_investments.sum()
            total_coins = coins_bought.sum()
            
            if total_investment > 0:
                final_value = total_coins * prices.iloc[-1]
                roi = (final_value - total_investment) / total_investment * 100
                
                results[symbol] = {
                    'weight': weights[symbol],
                    'weekly_investment': weekly_investment[symbol],
                    'total_investment': total_investment,
                    'final_value': final_value,
                    'roi': roi,
                    'volatility': metrics[symbol]['volatility'] * 100,
                    'sharpe': metrics[symbol]['sharpe'],
                    'volume_rank': metrics[symbol]['volume_rank'],
                    'avg_price': total_investment / total_coins,
                    'total_coins': total_coins
                }
        
        return results

    def plot_results(self, results: Dict):
        """Visualiza los resultados de forma eficiente"""
        if not results:
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Distribución del portafolio
        weights = [m['weight'] for m in results.values()]
        axes[0,0].pie(weights, labels=results.keys(), autopct='%1.1f%%')
        axes[0,0].set_title('Distribución del Portafolio')
        
        # 2. ROI vs Volatilidad
        rois = [m['roi'] for m in results.values()]
        vols = [m['volatility'] for m in results.values()]
        axes[0,1].scatter(vols, rois)
        for i, symbol in enumerate(results.keys()):
            axes[0,1].annotate(symbol, (vols[i], rois[i]))
        axes[0,1].set_xlabel('Volatilidad (%)')
        axes[0,1].set_ylabel('ROI (%)')
        axes[0,1].set_title('Riesgo vs Rendimiento')
        
        # 3. Inversión vs Valor Final
        inv = [m['total_investment'] for m in results.values()]
        val = [m['final_value'] for m in results.values()]
        x = range(len(results))
        axes[1,0].bar(x, inv, width=0.35, label='Inversión')
        axes[1,0].bar([i+0.35 for i in x], val, width=0.35, label='Valor Final')
        axes[1,0].set_xticks([i+0.175 for i in x])
        axes[1,0].set_xticklabels(results.keys(), rotation=45)
        axes[1,0].legend()
        axes[1,0].set_title('Inversión vs Valor Final')
        
        # 4. Sharpe Ratio
        sharpes = [m['sharpe'] for m in results.values()]
        axes[1,1].bar(results.keys(), sharpes)
        axes[1,1].set_xticklabels(results.keys(), rotation=45)
        axes[1,1].set_title('Ratio de Sharpe')
        
        plt.tight_layout()
        plt.show()


def main():
    # Configuración
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
    
    end_date = datetime(2025, 1, 17)
    start_date = datetime(2024, 7, 17)
    
    print(f"\nPeríodo de análisis:")
    print(f"Fecha de inicio: {start_date.strftime('%d/%m/%Y')}")
    print(f"Fecha de fin: {end_date.strftime('%d/%m/%Y')}")
    print(f"Duración: 6 meses\n")
    
    params = DCAParameters(
        base_investment=100,  # 100€ semanales
        rsi_period=14,
        price_drop_threshold=0.15,
        max_correlation=0.7,
        min_volume_percentile=25
    )
    
    optimizer = FastDCAOptimizer(symbols, start_date, end_date, params)
    results = optimizer.optimize_portfolio()
    
    if results:
        print("\nResultados del Portafolio Optimizado:")
        print("\nDistribución semanal de 100€:")
        
        total_value = sum(r['final_value'] for r in results.values())
        total_investment = sum(r['total_investment'] for r in results.values())
        
        for symbol, metrics in results.items():
            print(f"\n{symbol}:")
            print(f"  Inversión semanal: {metrics['weekly_investment']:.2f} EUR")
            print(f"  Inversión total: {metrics['total_investment']:.2f} EUR")
            print(f"  Valor final: {metrics['final_value']:.2f} EUR")
            print(f"  ROI: {metrics['roi']:.2f}%")
            print(f"  Volatilidad: {metrics['volatility']:.2f}%")
            print(f"  Ratio de Sharpe: {metrics['sharpe']:.2f}")
        
        print(f"\nMétricas del portafolio:")
        print(f"Inversión total: {total_investment:.2f} EUR")
        print(f"Valor final: {total_value:.2f} EUR")
        print(f"ROI total: {((total_value - total_investment) / total_investment * 100):.2f}%")
        
        optimizer.plot_results(results)


if __name__ == "__main__":
    main() 