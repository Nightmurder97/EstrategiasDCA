import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple, List
import logging
import json
import traceback
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TradingViewOptimizer:
    def __init__(self):
        self.tecnicos_df = None
        self.direcciones_df = None
        self.pnl_df = None
        self.portfolio = {}
        
        # Configuración de criterios
        self.min_market_cap = 100_000_000  # 100M USD
        self.min_profit_ratio = 50  # Al menos 50% de direcciones en beneficio
        self.max_correlation = 0.7
        self.max_assets = 15
        self.min_assets = 5
        
        # Pesos para el scoring
        self.weights = {
            'market_cap': 0.25,
            'profit_ratio': 0.25,
            'technical_score': 0.20,
            'rank': 0.15,
            'active_addresses': 0.15
        }
        
    def load_data(self):
        """Carga los datos de TradingView y otros archivos"""
        try:
            # Cargar datos de TradingView
            self.tecnicos_df = pd.read_csv('TradingViewData/Analizador de criptomonedas_2025-02-03-Datostecnicos.csv')
            self.direcciones_df = pd.read_csv('TradingViewData/Analizador de criptomonedas_2025-02-03-Direcciones.csv')
            self.pnl_df = pd.read_csv('TradingViewData/Analizador de criptomonedas_2025-02-03-PerdidasyGanancias.csv')
            
            # Mostrar columnas disponibles
            logger.info("Columnas en tecnicos_df:")
            logger.info(self.tecnicos_df.columns.tolist())
            logger.info("\nColumnas en direcciones_df:")
            logger.info(self.direcciones_df.columns.tolist())
            logger.info("\nColumnas en pnl_df:")
            logger.info(self.pnl_df.columns.tolist())
            
            logger.info(f"Datos cargados: {len(self.tecnicos_df)} criptomonedas")
            
        except Exception as e:
            logger.error(f"Error cargando datos: {str(e)}")
            raise
            
    def calculate_technical_score(self, row):
        """Calcula score técnico basado en indicadores"""
        score = 0
        
        # Rating técnico
        if 'Compra fuerte' in str(row['Rating técnico 1 día']):
            score += 2
        elif 'Comprar' in str(row['Rating técnico 1 día']):
            score += 1
        elif 'Venta fuerte' in str(row['Rating técnico 1 día']):
            score -= 2
        elif 'Vender' in str(row['Rating técnico 1 día']):
            score -= 1
            
        # RSI
        rsi = float(row['Índice de fuerza relativa (14) 1 día'])
        if 40 <= rsi <= 60:
            score += 1
        elif rsi > 70 or rsi < 30:
            score -= 1
            
        # Momentum
        momentum = float(row['Momentum (10) 1 día'])
        if momentum > 0:
            score += 1
        else:
            score -= 1
            
        return score
            
    def calculate_metrics(self) -> pd.DataFrame:
        """Calcula métricas para cada activo"""
        try:
            # Empezar con datos técnicos
            metrics = self.tecnicos_df.copy()
            
            # Añadir datos de direcciones
            metrics = pd.merge(
                metrics,
                self.direcciones_df[[
                    'Moneda', 
                    'Capitalización de mercado',
                    'Direcciones activas diarias'
                ]],
                on='Moneda',
                how='left'
            )
            
            # Añadir datos de PnL
            metrics = pd.merge(
                metrics,
                self.pnl_df[['Moneda', 'Direcciones de beneficios %']],
                on='Moneda',
                how='left'
            )
            
            # Limpiar y convertir market cap
            metrics['market_cap_clean'] = metrics['Capitalización de mercado'].apply(
                lambda x: float(str(x).replace(',', '')) if pd.notnull(x) and str(x).strip() != '' else 0
            )
            
            # Normalizar market cap
            max_cap = metrics['market_cap_clean'].max()
            min_cap = metrics['market_cap_clean'].min()
            if max_cap > min_cap:
                metrics['market_cap_score'] = (metrics['market_cap_clean'] - min_cap) / (max_cap - min_cap)
            else:
                metrics['market_cap_score'] = 0
            
            # Convertir profit ratio
            metrics['profit_score'] = pd.to_numeric(
                metrics['Direcciones de beneficios %'].fillna(0), 
                errors='coerce'
            ) / 100
            
            # Extraer ranking del número en la descripción
            metrics['rank_num'] = metrics.index + 1  # Usar el índice como ranking
            metrics['rank_score'] = 1 - (metrics['rank_num'] / len(metrics))
            
            # Score técnico
            metrics['technical_score'] = metrics.apply(self.calculate_technical_score, axis=1)
            max_tech = metrics['technical_score'].max()
            min_tech = metrics['technical_score'].min()
            if max_tech > min_tech:
                metrics['technical_score'] = (metrics['technical_score'] - min_tech) / (max_tech - min_tech)
            else:
                metrics['technical_score'] = 0
            
            # Score de direcciones activas
            metrics['active_addresses'] = pd.to_numeric(
                metrics['Direcciones activas diarias'].fillna(0), 
                errors='coerce'
            )
            max_addr = metrics['active_addresses'].max()
            min_addr = metrics['active_addresses'].min()
            if max_addr > min_addr:
                metrics['active_addresses_score'] = (metrics['active_addresses'] - min_addr) / (max_addr - min_addr)
            else:
                metrics['active_addresses_score'] = 0
            
            # Score total ponderado
            metrics['total_score'] = (
                metrics['market_cap_score'] * self.weights['market_cap'] +
                metrics['profit_score'] * self.weights['profit_ratio'] +
                metrics['technical_score'] * self.weights['technical_score'] +
                metrics['rank_score'] * self.weights['rank'] +
                metrics['active_addresses_score'] * self.weights['active_addresses']
            ).fillna(0)
            
            # Mostrar resumen de métricas
            logger.info("\nResumen de métricas:")
            logger.info(f"Total de activos: {len(metrics)}")
            logger.info(f"Activos con market cap > {self.min_market_cap:,.0f}: {(metrics['market_cap_clean'] > self.min_market_cap).sum()}")
            logger.info(f"Activos con profit ratio > {self.min_profit_ratio}%: {(metrics['profit_score'] * 100 > self.min_profit_ratio).sum()}")
            
            return metrics.sort_values('total_score', ascending=False)
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {str(e)}")
            logger.error("Columnas disponibles:")
            logger.error(metrics.columns.tolist())
            raise

    def optimize_portfolio(self, investment: float = 100.0) -> Tuple[Dict, pd.DataFrame]:
        """Optimiza el portafolio basado en las métricas"""
        try:
            metrics_df = self.calculate_metrics()
            
            # Filtrar por criterios mínimos
            valid_assets = metrics_df[
                (metrics_df['profit_score'] * 100 > self.min_profit_ratio) &
                (metrics_df['market_cap_clean'] > self.min_market_cap) &
                (metrics_df['rank_num'] < 500)  # Solo top 500
            ].copy()
            
            logger.info(f"Activos que cumplen criterios: {len(valid_assets)}")
            logger.info("Top 10 activos por score total:")
            logger.info(valid_assets[['Moneda', 'total_score', 'market_cap_clean', 'profit_score']].head(10))
            
            if len(valid_assets) < self.min_assets:
                logger.warning(f"Solo {len(valid_assets)} activos cumplen los criterios (mínimo {self.min_assets})")
                return {}, pd.DataFrame()
            
            # Seleccionar mejores activos y resetear índice
            selected = valid_assets.head(self.max_assets).reset_index(drop=True)
            
            # Calcular pesos basados en el score
            total_score = selected['total_score'].sum()
            selected['weight'] = selected['total_score'] / total_score
            
            # Crear portafolio usando iterrows
            portfolio = {}
            for _, row in selected.iterrows():
                try:
                    portfolio[row['Moneda']] = {
                        'weight': row['weight'] * 100,
                        'weekly_investment': row['weight'] * investment,
                        'market_cap': row['Capitalización de mercado'],
                        'profit_ratio': row['profit_score'] * 100,
                        'rank': int(row['rank_num']),
                        'technical_rating': row['Rating técnico 1 día'],
                        'rsi': float(row['Índice de fuerza relativa (14) 1 día']),
                        'active_addresses': row['Direcciones activas diarias']
                    }
                except Exception as e:
                    logger.error(f"Error procesando {row['Moneda']}: {str(e)}")
                    logger.error(f"Datos de la fila: {row.to_dict()}")
                    continue
            
            logger.info(f"Portafolio creado con {len(portfolio)} activos")
            
            # Verificar que tenemos suficientes activos
            if len(portfolio) < self.min_assets:
                logger.error(f"No se pudieron procesar suficientes activos (mínimo {self.min_assets})")
                return {}, pd.DataFrame()
            
            return portfolio, selected
            
        except Exception as e:
            logger.error(f"Error optimizando portafolio: {str(e)}")
            logger.error("Estado actual:")
            logger.error(f"Métricas disponibles: {len(metrics_df) if 'metrics_df' in locals() else 'No calculadas'}")
            logger.error(f"Activos válidos: {len(valid_assets) if 'valid_assets' in locals() else 'No filtrados'}")
            logger.error(f"Activos seleccionados: {len(selected) if 'selected' in locals() else 'No seleccionados'}")
            raise

    def plot_analysis(self, portfolio: Dict, metrics_df: pd.DataFrame):
        """Genera visualizaciones del análisis"""
        try:
            # Crear directorio para gráficos
            output_dir = 'analisis/graficos'
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Directorio creado: {output_dir}")
            
            # Verificar rutas absolutas
            current_dir = os.getcwd()
            portfolio_path = os.path.join(current_dir, output_dir, 'analisis_portafolio.png')
            metrics_path = os.path.join(current_dir, output_dir, 'metricas_detalladas.png')
            summary_path = os.path.join(current_dir, output_dir, 'resumen_portfolio.json')
            
            logger.info(f"Directorio actual: {current_dir}")
            logger.info("Rutas absolutas de archivos:")
            logger.info(f"- Portfolio: {portfolio_path}")
            logger.info(f"- Métricas: {metrics_path}")
            logger.info(f"- Resumen: {summary_path}")
            
            # Verificar permisos de escritura
            if not os.access(output_dir, os.W_OK):
                logger.error(f"No hay permisos de escritura en {output_dir}")
                return
            
            # Configurar estilo de matplotlib
            plt.style.use('default')  # Usar estilo default en lugar de seaborn
            
            # Crear figura principal con subplots
            fig = plt.figure(figsize=(20, 15))
            
            # 1. Distribución del portafolio (pie chart)
            ax1 = plt.subplot(2, 2, 1)
            weights = {k: v['weight'] for k, v in portfolio.items()}
            wedges, texts, autotexts = ax1.pie(
                list(weights.values()), 
                labels=list(weights.keys()), 
                autopct='%1.1f%%',
                textprops={'fontsize': 8}
            )
            plt.setp(autotexts, size=7)
            plt.title('Distribución del Portafolio', pad=20, fontsize=12)
            
            # 2. Métricas por activo (barras)
            ax2 = plt.subplot(2, 2, 2)
            selected_assets = list(portfolio.keys())
            metrics = metrics_df[metrics_df['Moneda'].isin(selected_assets)].copy()
            
            x = np.arange(len(selected_assets))
            width = 0.2
            
            metrics_to_plot = ['market_cap_score', 'profit_score', 'technical_score', 'active_addresses_score']
            labels = ['Market Cap', 'Beneficios', 'Técnico', 'Direcciones']
            
            for i, (metric, label) in enumerate(zip(metrics_to_plot, labels)):
                plt.bar(x + i*width - width*1.5, metrics[metric], width, label=label)
            
            plt.xlabel('Activos')
            plt.ylabel('Score')
            plt.title('Métricas por Activo')
            plt.xticks(x, selected_assets, rotation=45, ha='right')
            plt.legend()
            
            # 3. RSI y niveles técnicos
            ax3 = plt.subplot(2, 2, 3)
            rsi_values = [portfolio[k]['rsi'] for k in selected_assets]
            bars = ax3.bar(selected_assets, rsi_values)
            
            # Colorear barras según nivel RSI
            for bar, rsi in zip(bars, rsi_values):
                if rsi > 70:
                    bar.set_color('red')
                elif rsi < 30:
                    bar.set_color('green')
                else:
                    bar.set_color('blue')
            
            plt.axhline(y=70, color='r', linestyle='--', label='Sobrecompra')
            plt.axhline(y=30, color='g', linestyle='--', label='Sobreventa')
            plt.title('RSI por Activo')
            plt.xticks(rotation=45, ha='right')
            plt.legend()
            
            # 4. Ratio de beneficios
            ax4 = plt.subplot(2, 2, 4)
            profit_ratios = [portfolio[k]['profit_ratio'] for k in selected_assets]
            bars = ax4.bar(selected_assets, profit_ratios)
            
            plt.axhline(y=50, color='r', linestyle='--', label='Mínimo requerido')
            plt.title('Ratio de Beneficios (%)')
            plt.xticks(rotation=45, ha='right')
            plt.legend()
            
            # Ajustar layout y guardar
            plt.tight_layout(pad=3.0)
            plt.savefig(portfolio_path, dpi=300, bbox_inches='tight')
            logger.info(f"Guardado: {portfolio_path}")
            plt.close()
            
            # Guardar resumen en JSON
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'portfolio': portfolio,
                    'metricas': {
                        'num_activos': len(portfolio),
                        'inversion_semanal': sum(v['weekly_investment'] for v in portfolio.values()),
                        'promedio_beneficios': np.mean([v['profit_ratio'] for v in portfolio.values()]),
                        'promedio_rsi': np.mean([v['rsi'] for v in portfolio.values()]),
                    }
                }, f, indent=4, ensure_ascii=False)
            logger.info(f"Guardado: {summary_path}")
            
            # Verificación final
            for path in [portfolio_path, metrics_path, summary_path]:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    logger.info(f"Archivo creado: {path} ({size} bytes)")
                else:
                    logger.error(f"No se pudo crear: {path}")
            
        except Exception as e:
            logger.error(f"Error generando visualizaciones: {str(e)}")
            logger.error(f"Directorio actual: {os.getcwd()}")
            traceback.print_exc()

def main():
    try:
        weekly_investment = 100.0
        
        logger.info("Iniciando optimización con datos de TradingView...")
        
        optimizer = TradingViewOptimizer()
        optimizer.load_data()
        
        portfolio, metrics = optimizer.optimize_portfolio(weekly_investment)
        
        if not portfolio:
            logger.error("No se pudo generar un portafolio óptimo")
            return
            
        optimizer.plot_analysis(portfolio, metrics)
        
        logger.info("\nPortafolio optimizado:")
        for symbol, data in portfolio.items():
            logger.info(f"\n{symbol}:")
            logger.info(f"  Peso: {data['weight']:.2f}% (${data['weekly_investment']:.2f} semanal)")
            logger.info(f"  Market Cap: {data['market_cap']}")
            logger.info(f"  Ratio de Beneficios: {data['profit_ratio']:.2f}%")
            logger.info(f"  Rating Técnico: {data['technical_rating']}")
            logger.info(f"  RSI: {data['rsi']:.2f}")
            logger.info(f"  Direcciones Activas: {data['active_addresses']}")
            
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 