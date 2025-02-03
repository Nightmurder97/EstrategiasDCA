import logging
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dca_optimizer_enhanced import EnhancedDCAOptimizer

def plot_portfolio_analysis(portfolio_metrics, metrics_df, correlation_matrix):
    """Genera visualizaciones del análisis del portafolio"""
    # Configurar estilo
    plt.style.use('default')
    sns.set_theme(style="whitegrid")
    
    # Crear figura con subplots
    fig = plt.figure(figsize=(15, 12))
    
    # 1. Gráfico de distribución del portafolio (pie chart)
    plt.subplot(2, 2, 1)
    weights = {k: v['weight'] for k, v in portfolio_metrics.items() if isinstance(v, dict)}
    plt.pie(weights.values(), labels=weights.keys(), autopct='%1.1f%%')
    plt.title('Distribución del Portafolio')
    
    # 2. Métricas principales
    plt.subplot(2, 2, 2)
    metrics = {
        'roi': portfolio_metrics['roi'],
        'volatility': portfolio_metrics['volatility'],
        'sharpe_ratio': portfolio_metrics['sharpe_ratio'] * 100,  # Escalar para visualización
        'max_drawdown': abs(portfolio_metrics['max_drawdown'])
    }
    bars = plt.bar(metrics.keys(), metrics.values())
    plt.title('Métricas Principales del Portafolio')
    plt.xticks(rotation=45)
    
    # Añadir valores encima de las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom')
    
    # 3. Matriz de correlación
    plt.subplot(2, 1, 2)
    selected_symbols = list(weights.keys())
    selected_corr = correlation_matrix.loc[selected_symbols, selected_symbols]
    sns.heatmap(selected_corr, 
                cmap='RdYlBu_r', 
                center=0, 
                annot=True, 
                fmt='.2f',
                square=True,
                cbar_kws={'label': 'Correlación'})
    plt.title('Matriz de Correlación del Portafolio')
    
    # Ajustar layout
    plt.tight_layout()
    
    # Guardar gráfico
    plt.savefig('portfolio_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Gráfico adicional de métricas por activo
    plt.figure(figsize=(15, 6))
    metrics_to_plot = ['price_return', 'volatility', 'sharpe', 'sortino']
    
    # Filtrar y preparar datos
    plot_data = metrics_df.loc[selected_symbols][metrics_to_plot]
    
    # Crear gráfico de barras agrupadas
    x = np.arange(len(selected_symbols))
    width = 0.2
    
    for i, metric in enumerate(metrics_to_plot):
        plt.bar(x + i*width, plot_data[metric], width, label=metric)
    
    plt.xlabel('Símbolos')
    plt.ylabel('Valor')
    plt.title('Métricas por Activo')
    plt.xticks(x + width*1.5, selected_symbols, rotation=45)
    plt.legend()
    plt.tight_layout()
    
    # Guardar segundo gráfico
    plt.savefig('metrics_by_asset.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    try:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logger = logging.getLogger(__name__)
        
        # Inversión semanal (en USD)
        weekly_investment = 100.0
        
        logger.info("Iniciando optimización de portafolio DCA...")
        
        # Crear instancia del optimizador
        optimizer = EnhancedDCAOptimizer()
        
        # Ejecutar optimización
        portfolio_metrics, metrics_df = optimizer.optimize_portfolio(weekly_investment)
        
        if not portfolio_metrics:
            logger.error("No se pudo encontrar una estrategia óptima.")
            return
        
        # Generar visualizaciones
        plot_portfolio_analysis(
            portfolio_metrics, 
            metrics_df,
            optimizer.correlation_matrix
        )
        
        # Mostrar resultados
        logger.info("\nResultados de la optimización:")
        logger.info(f"ROI esperado: {portfolio_metrics['roi']:.2f}%")
        logger.info(f"Volatilidad: {portfolio_metrics['volatility']:.2f}%")
        logger.info(f"Ratio de Sharpe: {portfolio_metrics['sharpe_ratio']:.2f}")
        logger.info(f"Máximo drawdown: {portfolio_metrics['max_drawdown']:.2f}%")
        
        logger.info("\nDistribución del portafolio:")
        for symbol, data in portfolio_metrics.items():
            if isinstance(data, dict) and 'weight' in data:
                logger.info(f"{symbol}: {data['weight']:.2f}% (${data['weekly_investment']:.2f} semanal)")
        
        # Mostrar resumen de datos cargados
        logger.info("\nResumen de datos cargados:")
        logger.info(f"Total de criptomonedas analizadas: {len(metrics_df)}")
        logger.info(f"Criterios de selección:")
        logger.info(f"- Market Cap mínimo: ${optimizer.config.min_market_cap:,.2f}")
        logger.info(f"- Volumen 24h mínimo: ${optimizer.config.min_volume_24h:,.2f}")
        logger.info(f"- Correlación máxima: {optimizer.config.correlation_threshold:.2f}")
        
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 