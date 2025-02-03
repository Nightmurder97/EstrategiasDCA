import sys
import os

# Obtener la ruta absoluta al directorio 'src'
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Añadir el directorio 'src' al sys.path
sys.path.insert(0, src_dir)

from market_analysis import MarketAnalyzer
from dca_optimizer_enhanced import EnhancedDCAOptimizer
from report_generator import ReportGenerator
from config import config

def main():
    market_data_config = {
        'lookback_period': config.trading_params.lookback_period,
        'min_volume_percentile': config.trading_params.min_volume_percentile,
        'portfolio_weights': config.portfolio_weights,
        'binance_api_key': config.binance_api_key,
        'binance_api_secret': config.binance_api_secret
    }
    analyzer = MarketAnalyzer(market_data_config)
    
    # Analizar mercado actual
    market_analysis = analyzer.analyze_market()
    
    # Optimizar estrategia DCA
    optimizer = EnhancedDCAOptimizer()
    optimization_results = optimizer.optimize_portfolio(100)
    
    # Generar reporte
    report_gen = ReportGenerator(market_analysis)
    report_gen.generate_unified_report()

if __name__ == "__main__":
    main()
