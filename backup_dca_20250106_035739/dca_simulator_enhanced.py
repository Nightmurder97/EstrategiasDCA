import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from tqdm import tqdm
from binance.client import Client
import json
from dataclasses import dataclass
import os
from concurrent.futures import ThreadPoolExecutor
import warnings

warnings.filterwarnings('ignore')

@dataclass
class SimulationParameters:
    """Parámetros para la simulación de DCA"""
    daily_investment: float = 100.0  # Inversión diaria en EUR
    lookback_period: int = 30  # Período para calcular métricas
    min_volume_percentile: float = 0.2  # Percentil mínimo de volumen
    max_position_size: float = 0.3  # Tamaño máximo de posición (30%)
    rebalance_threshold: float = 0.1  # Umbral de rebalanceo (10%)


class EnhancedDCASimulator:
    """Simulador avanzado de estrategia DCA con análisis y optimización"""
    
    def __init__(self, params: SimulationParameters):
        self.params = params
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
            'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT',
            'MATICUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'ETCUSDT',
            'FILUSDT', 'XLMUSDT', 'ALGOUSDT', 'VETUSDT', 'THETAUSDT',
            'MANAUSDT', 'AAVEUSDT', 'GRTUSDT', 'MKRUSDT', 'COMPUSDT',
            'SNXUSDT', 'YFIUSDT', 'SUSHIUSDT', 'RENUSDT', '1INCHUSDT'
        ]
        self.reference_indices = ['BTCUSDT', 'ETHUSDT']  # Índices de referencia
        self.portfolio_history = self._load_portfolio_history()
        self.client = Client(None, None)  # Cliente de Binance en modo público
        
    def _load_portfolio_history(self) -> Dict:
        """Carga el historial del portafolio desde un archivo JSON"""
        if os.path.exists('portfolio_history.json'):
            with open('portfolio_history.json', 'r') as f:
                return json.load(f)
        return {
            'positions': {},
            'transactions': [],
            'daily_performance': [],
            'total_invested': 0,
            'last_update': None
        }
    
    def _save_portfolio_history(self):
        """Guarda el historial del portafolio en un archivo JSON"""
        with open('portfolio_history.json', 'w') as f:
            json.dump(self.portfolio_history, f, indent=4)
    
    def _fetch_market_data(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Obtiene datos históricos de mercado usando Binance"""
        print("Obteniendo datos de mercado...")
        market_data = {}
        
        # Convertir fechas a timestamps en milisegundos
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            def fetch_symbol(symbol):
                try:
                    # Obtener klines (velas) de Binance
                    klines = self.client.get_historical_klines(
                        symbol,
                        Client.KLINE_INTERVAL_1DAY,
                        start_ts,
                        end_ts
                    )
                    
                    if klines:
                        # Convertir klines a DataFrame
                        df = pd.DataFrame(klines, columns=[
                            'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                            'taker_buy_quote', 'ignored'
                        ])
                        
                        # Convertir tipos de datos
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        df.set_index('timestamp', inplace=True)
                        return symbol, df
                        
                except Exception as e:
                    print(f"Error al obtener datos para {symbol}: {str(e)}")
                return None
            
            futures = [executor.submit(fetch_symbol, symbol) for symbol in self.symbols]
            for future in tqdm(futures, desc="Progreso", unit="símbolo"):
                result = future.result()
                if result:
                    symbol, data = result
                    market_data[symbol] = data
        
        return market_data
    
    def _calculate_daily_metrics(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        """Calcula métricas diarias para cada activo"""
        metrics = {}
        for symbol, data in market_data.items():
            returns = data['Close'].pct_change()
            metrics[symbol] = {
                'daily_return': returns.iloc[-1] if not returns.empty else 0,
                'volatility': returns.std() * np.sqrt(252) if not returns.empty else 0,
                'volume': data['Volume'].iloc[-1] if 'Volume' in data else 0
            }
        return metrics
    
    def _generate_training_data(self, market_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Genera datos de entrenamiento para el modelo de Gemini"""
        training_data = []
        
        for symbol, data in market_data.items():
            # Calcular métricas técnicas
            returns = data['Close'].pct_change()
            volatility = returns.rolling(window=30).std() * np.sqrt(252)
            rsi = self._calculate_rsi(data['Close'])
            volume_ma = data['Volume'].rolling(window=30).mean()
            
            # Crear registros de entrenamiento
            for i in range(30, len(data)):
                record = {
                    'symbol': symbol,
                    'date': data.index[i].strftime('%Y-%m-%d'),
                    'price': data['Close'].iloc[i],
                    'return_30d': returns.iloc[i-30:i].mean() * 100,
                    'volatility': volatility.iloc[i],
                    'rsi': rsi.iloc[i],
                    'volume_ratio': data['Volume'].iloc[i] / volume_ma.iloc[i],
                    'next_return': returns.iloc[i+1] if i+1 < len(data) else None
                }
                training_data.append(record)
        
        return pd.DataFrame(training_data)
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula el RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _export_training_data(self, training_data: pd.DataFrame):
        """Exporta los datos de entrenamiento en formatos CSV y JSONL"""
        # Exportar a CSV
        training_data.to_csv('gemini_training_data.csv', index=False)
        
        # Exportar a JSONL para fine-tuning
        with open('gemini_tuning_data.jsonl', 'w') as f:
            for _, row in training_data.iterrows():
                prompt = f"Analizar {row['symbol']} con precio {row['price']:.2f}, RSI {row['rsi']:.2f}, " \
                        f"volatilidad {row['volatility']:.2f}%, ratio de volumen {row['volume_ratio']:.2f}"
                completion = f"El retorno en el siguiente día fue {row['next_return']:.2f}%"
                json_record = {
                    "prompt": prompt,
                    "completion": completion
                }
                f.write(json.dumps(json_record) + '\n')
        
        print("Datos de entrenamiento exportados a:")
        print("- gemini_training_data.csv")
        print("- gemini_tuning_data.jsonl")

    def calculate_optimal_allocation(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calcula la asignación óptima del portafolio basada en múltiples factores"""
        metrics = {}
        
        print("Analizando activos...")
        for symbol, data in tqdm(market_data.items(), desc="Progreso", unit="símbolo"):
            # Calcular retornos y métricas
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            avg_return = returns.mean() * 252
            sharpe = avg_return / volatility if volatility != 0 else 0
            
            # Calcular métricas de volumen
            volume_trend = data['Volume'].rolling(window=7).mean() / data['Volume'].rolling(window=30).mean()
            volume_score = volume_trend.iloc[-1] if not volume_trend.empty else 0
            
            # Calcular momentum
            price_sma_ratio = data['Close'].iloc[-1] / data['Close'].rolling(window=30).mean().iloc[-1]
            
            metrics[symbol] = {
                'sharpe': sharpe,
                'volatility': volatility,
                'volume_score': volume_score,
                'momentum': price_sma_ratio,
                'avg_return': avg_return
            }
        
        # Generar heatmap de los factores
        self.plot_allocation_heatmap(metrics)
        
        # Filtrar por volumen mínimo
        filtered_symbols = [
            symbol for symbol, m in metrics.items()
            if m['volume_score'] >= 0.5  # Reducir el umbral de volumen para incluir más activos
        ]
        
        if len(filtered_symbols) < 5:
            filtered_symbols = list(metrics.keys())[:5]
        
        # Calcular score compuesto
        scores = {}
        for symbol in filtered_symbols:
            m = metrics[symbol]
            # Score compuesto ajustado:
            # 30% Sharpe + 25% Volumen + 25% Momentum + 20% Retorno ajustado por volatilidad
            scores[symbol] = (
                0.3 * max(0, m['sharpe']) +
                0.25 * m['volume_score'] +
                0.25 * m['momentum'] +
                0.2 * (m['avg_return'] / m['volatility'] if m['volatility'] != 0 else 0)
            )
        
        # Seleccionar mínimo 5 activos
        top_symbols = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:8]
        
        # Calcular pesos iniciales
        weights = {}
        total_score = sum(score for _, score in top_symbols)
        
        for symbol, score in top_symbols:
            # Peso base según score
            weight = score / total_score if total_score > 0 else 0.125
            
            # Ajustar por volatilidad (menor peso a mayor volatilidad)
            vol_adjustment = 1 - (metrics[symbol]['volatility'] / max(m['volatility'] for m in metrics.values()))
            weight = weight * (0.7 + 0.3 * vol_adjustment)
            
            # Aplicar límites mínimos y máximos
            weight = max(0.05, min(weight, self.params.max_position_size))
            weights[symbol] = weight
        
        # Normalizar pesos finales
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        # Imprimir explicación de los pesos
        print("\nJustificación de los pesos asignados:")
        for symbol, weight in weights.items():
            m = metrics[symbol]
            print(f"\n{symbol}:")
            print(f"  Peso asignado: {weight*100:.2f}%")
            print(f"  Ratio de Sharpe: {m['sharpe']:.2f}")
            print(f"  Volatilidad anual: {m['volatility']*100:.2f}%")
            print(f"  Score de volumen: {m['volume_score']:.2f}")
            print(f"  Momentum: {m['momentum']:.2f}")
            print(f"  Retorno promedio anual: {m['avg_return']*100:.2f}%")
        
        return weights

    def plot_allocation_heatmap(self, metrics: Dict[str, Dict[str, float]]):
        """Genera un heatmap de los factores de asignación óptima"""
        try:
            plt.figure(figsize=(20, 12))
            
            # Preparar datos para el heatmap
            data = []
            symbols = []
            factors = ['sharpe', 'volume_score', 'momentum', 'avg_return', 'volatility']
            
            for symbol, metric in metrics.items():
                symbols.append(symbol)
                data.append([
                    metric['sharpe'],
                    metric['volume_score'],
                    metric['momentum'],
                    metric['avg_return'],
                    metric['volatility']
                ])
            
            # Crear DataFrame
            df_heatmap = pd.DataFrame(data, columns=factors, index=symbols)
            
            # Normalizar los datos para mejor visualización
            df_normalized = (df_heatmap - df_heatmap.mean()) / df_heatmap.std()
            
            # Ajustar el tamaño de la figura según la cantidad de activos
            plt.figure(figsize=(15, len(symbols) * 0.4))
            
            # Crear heatmap con etiquetas más grandes
            sns.heatmap(df_normalized, 
                       annot=True, 
                       cmap='RdYlGn',
                       center=0,
                       fmt='.2f',
                       cbar_kws={'label': 'Z-Score'},
                       annot_kws={'size': 8},
                       yticklabels=symbols,
                       xticklabels=factors)
            
            plt.title('Factores de Asignación Óptima (Normalizado)', pad=20)
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            
            # Guardar el heatmap en un archivo
            plt.savefig('allocation_heatmap.png', dpi=300, bbox_inches='tight')
            print("Heatmap guardado como 'allocation_heatmap.png'")
            
            plt.close()  # Cerrar la figura para liberar memoria
            
        except Exception as e:
            print(f"Error al generar el heatmap: {str(e)}")
            import traceback
            traceback.print_exc()

    def plot_enhanced_analysis(self, market_data: Dict[str, pd.DataFrame]):
        """Genera gráficos avanzados de análisis"""
        plt.style.use('bmh')  # Usar un estilo incorporado en matplotlib
        fig = plt.figure(figsize=(20, 15))
        
        print("Generando visualizaciones...")
        
        # 1. Evolución del valor del portafolio
        ax1 = plt.subplot(3, 2, 1)
        if self.portfolio_history['daily_performance']:
            daily_perf = pd.DataFrame(self.portfolio_history['daily_performance'])
            if 'timestamp' in daily_perf.columns:
                daily_perf['date'] = pd.to_datetime(daily_perf['timestamp'])
            elif 'date' in daily_perf.columns:
                daily_perf['date'] = pd.to_datetime(daily_perf['date'])
            else:
                # Si no hay fechas, crear un índice temporal
                daily_perf['date'] = pd.date_range(
                    end=datetime.now(),
                    periods=len(daily_perf),
                    freq='D'
                )
            
            plt.plot(daily_perf['date'], daily_perf['value'], label='Valor del Portafolio')
            plt.title('Evolución del Valor del Portafolio')
            plt.xticks(rotation=45)
            plt.legend()
        
        # 2. Comparación con índices de referencia
        ax2 = plt.subplot(3, 2, 2)
        if self.portfolio_history['daily_performance']:
            portfolio_returns = daily_perf['return'] if 'return' in daily_perf.columns else pd.Series([0])
            for symbol in self.reference_indices:
                if symbol in market_data:
                    returns = market_data[symbol]['Close'].pct_change() * 100
                    plt.plot(returns.index, returns.cumsum(), label=symbol)
            plt.plot(daily_perf['date'], portfolio_returns.cumsum(), label='Portfolio')
            plt.title('Rendimiento Acumulado vs Índices')
            plt.xticks(rotation=45)
            plt.legend()
        
        # 3. Distribución de retornos
        ax3 = plt.subplot(3, 2, 3)
        if self.portfolio_history['daily_performance']:
            if 'return' in daily_perf.columns:
                sns.histplot(daily_perf['return'].dropna(), kde=True)
            plt.title('Distribución de Retornos Diarios')
        
        # 4. Composición actual del portafolio
        ax4 = plt.subplot(3, 2, 4)
        current_values = {}
        current_prices = {symbol: data['Close'].iloc[-1] for symbol, data in market_data.items()}
        for symbol, position in self.portfolio_history['positions'].items():
            if symbol in current_prices:
                current_values[symbol] = position['coins'] * current_prices[symbol]
        
        if current_values:
            plt.pie(current_values.values(), labels=current_values.keys(), autopct='%1.1f%%')
            plt.title('Composición Actual del Portafolio')
        
        # 5. Correlación entre activos
        ax5 = plt.subplot(3, 2, (5, 6))
        returns_data = pd.DataFrame()
        for symbol in self.symbols:
            if symbol in market_data:
                returns_data[symbol] = market_data[symbol]['Close'].pct_change()
        
        if not returns_data.empty:
            sns.heatmap(returns_data.corr(), annot=True, cmap='coolwarm', center=0)
            plt.title('Matriz de Correlación')
        
        plt.tight_layout()
        plt.savefig('portfolio_analysis.png')
        print("Análisis del portafolio guardado como 'portfolio_analysis.png'")
        plt.close()

    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calcula el valor actual del portafolio"""
        total_value = 0
        for symbol, position in self.portfolio_history['positions'].items():
            if symbol in current_prices:
                total_value += position['coins'] * current_prices[symbol]
        return total_value

    def update_portfolio(self, trades: Dict[str, float], current_prices: Dict[str, float]):
        """Actualiza el portafolio con nuevas operaciones"""
        timestamp = datetime.now().isoformat()
        
        for symbol, amount in trades.items():
            price = current_prices[symbol]
            coins = amount / price
            
            if symbol not in self.portfolio_history['positions']:
                self.portfolio_history['positions'][symbol] = {
                    'coins': 0,
                    'total_invested': 0
                }
            
            self.portfolio_history['positions'][symbol]['coins'] += coins
            self.portfolio_history['positions'][symbol]['total_invested'] += amount
            
            self.portfolio_history['transactions'].append({
                'timestamp': timestamp,
                'symbol': symbol,
                'type': 'buy',
                'amount': amount,
                'price': price,
                'coins': coins
            })
        
        self.portfolio_history['total_invested'] += sum(trades.values())
        self.portfolio_history['last_update'] = timestamp
        
        self._save_portfolio_history()

    def calculate_max_drawdown(self) -> float:
        """Calcula el máximo drawdown del portafolio"""
        if not self.portfolio_history['daily_performance']:
            return 0.0
        
        values = pd.Series([p['value'] for p in self.portfolio_history['daily_performance']])
        peak = values.expanding(min_periods=1).max()
        drawdown = (values - peak) / peak
        return abs(drawdown.min()) * 100

    def calculate_sharpe_ratio(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """Calcula el ratio de Sharpe del portafolio"""
        if not self.portfolio_history['daily_performance']:
            return 0.0
        
        returns = pd.Series([p['return'] for p in self.portfolio_history['daily_performance']])
        if returns.empty:
            return 0.0
        
        risk_free_rate = 0.02  # Tasa libre de riesgo anual (2%)
        daily_rf = (1 + risk_free_rate) ** (1/252) - 1
        
        excess_returns = returns - daily_rf
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        return sharpe

    def calculate_success_rate(self) -> float:
        """Calcula la tasa de éxito de las operaciones"""
        if not self.portfolio_history['daily_performance']:
            return 0.0
        
        returns = pd.Series([p['return'] for p in self.portfolio_history['daily_performance']])
        if returns.empty:
            return 0.0
        
        success_count = len(returns[returns > 0])
        total_count = len(returns)
        
        return (success_count / total_count * 100) if total_count > 0 else 0.0 

def main():
    """Función principal para ejecutar el simulador"""
    # Configurar parámetros
    params = SimulationParameters(
        daily_investment=100.0/7,  # 100€ semanales divididos por 7 días
        lookback_period=30,
        min_volume_percentile=0.2,
        max_position_size=0.25,  # Máximo 25% por activo
        rebalance_threshold=0.1
    )
    
    # Crear instancia del simulador
    simulator = EnhancedDCASimulator(params)
    
    # Definir fechas para el análisis
    target_date = datetime(2025, 1, 6)  # Fecha actual: 06/01/2025
    
    # Usar datos históricos de los últimos 6 meses
    historical_end = target_date
    historical_start = historical_end - timedelta(days=180)
    
    print(f"\nPeríodo de análisis histórico:")
    print(f"Desde: {historical_start.strftime('%d/%m/%Y')}")
    print(f"Hasta: {historical_end.strftime('%d/%m/%Y')}")
    print(f"Fecha actual: {target_date.strftime('%d/%m/%Y')}")
    
    try:
        # Obtener datos de mercado históricos
        market_data = simulator._fetch_market_data(
            start_date=historical_start.strftime('%Y-%m-%d'),
            end_date=historical_end.strftime('%Y-%m-%d')
        )
        
        if not market_data:
            print("No se pudieron obtener datos de mercado. Verificar la conexión y los símbolos.")
            return
        
        # Filtrar activos sin datos
        valid_market_data = {
            symbol: data for symbol, data in market_data.items()
            if not data.empty and len(data) > 0
        }
        
        if not valid_market_data:
            print("No se encontraron datos válidos para ningún activo.")
            return
        
        print(f"\nActivos con datos válidos: {len(valid_market_data)}")
        for symbol, data in valid_market_data.items():
            print(f"- {symbol}:")
            print(f"  Registros: {len(data)}")
            print(f"  Primer fecha: {data.index[0].strftime('%d/%m/%Y')}")
            print(f"  Última fecha: {data.index[-1].strftime('%d/%m/%Y')}")
            print(f"  Último precio: {data['Close'].iloc[-1]:.2f} USDT")
            print(f"  Volumen promedio: {data['Volume'].mean():.2f} USDT")
        
        # Calcular asignación óptima
        print("\nCalculando asignación óptima...")
        weights = simulator.calculate_optimal_allocation(valid_market_data)
        
        if not weights:
            print("No se pudo calcular la asignación óptima.")
            return
        
        print("\nPesos calculados:")
        for symbol, weight in weights.items():
            print(f"- {symbol}: {weight*100:.2f}%")
        
        # Simular inversiones diarias
        daily_investment = params.daily_investment
        current_prices = {
            symbol: data['Close'].iloc[-1] 
            for symbol, data in valid_market_data.items()
        }
        
        # Calcular montos de inversión por activo
        trades = {}
        print("\nDistribución de la inversión diaria:")
        for symbol, weight in weights.items():
            amount = daily_investment * weight
            trades[symbol] = amount
            print(f"- {symbol}: {amount:.2f}€")
        
        # Actualizar portafolio
        print("\nActualizando portafolio...")
        simulator.update_portfolio(trades, current_prices)
        
        # Calcular y mostrar métricas
        portfolio_value = simulator.calculate_portfolio_value(current_prices)
        max_drawdown = simulator.calculate_max_drawdown()
        sharpe_ratio = simulator.calculate_sharpe_ratio(valid_market_data)
        success_rate = simulator.calculate_success_rate()
        
        print("\nResumen del portafolio:")
        print(f"Valor total: {portfolio_value:.2f}€")
        print(f"Inversión total: {simulator.portfolio_history['total_invested']:.2f}€")
        print(f"Máximo drawdown: {max_drawdown:.2f}%")
        print(f"Ratio de Sharpe: {sharpe_ratio:.2f}")
        print(f"Tasa de éxito: {success_rate:.2f}%")
        
        # Generar visualizaciones
        print("\nGenerando visualizaciones...")
        simulator.plot_enhanced_analysis(valid_market_data)
        
        # Generar datos de entrenamiento para Gemini
        print("\nGenerando datos de entrenamiento...")
        training_data = simulator._generate_training_data(valid_market_data)
        simulator._export_training_data(training_data)
        
        # Calcular días hasta la fecha objetivo
        days_to_target = (target_date - historical_end).days
        print(f"\nDías hasta la fecha objetivo: {days_to_target}")
        print("\nNota: Los resultados se basan en datos históricos de un año atrás.")
        print("      Las proyecciones futuras son simuladas y no garantizan resultados reales.")
        
    except Exception as e:
        print(f"\nError durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 