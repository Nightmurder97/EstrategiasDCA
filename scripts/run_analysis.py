import sys
import os

# Obtener la ruta absoluta al directorio del proyecto
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Añadir el directorio del proyecto al sys.path
sys.path.insert(0, project_dir)

from src.market_analysis import MarketAnalyzer
from src.report_generator import ReportGenerator
from src.config_models import load_config

def main():
    config = load_config()
    print("🚀 Iniciando análisis del mercado...")
    
    # Configurar analizador de mercado
    market_data_config = {
        'lookback_period': config.trading.lookback_period,
        'min_volume_percentile': config.trading.min_volume_percentile,
        'portfolio_weights': config.portfolio_weights,
        'binance_api_key': config.binance.api_key,
        'binance_api_secret': config.binance.api_secret.get_secret_value() if config.binance.api_secret else None
    }
    
    print("📊 Configuración cargada exitosamente")
    print(f"   - Periodo de análisis: {config.trading.lookback_period} días")
    print(f"   - Percentil de volumen mínimo: {config.trading.min_volume_percentile}%")
    print(f"   - Número de criptomonedas en portafolio: {len(config.portfolio_weights)}")
    
    # Inicializar analizador
    analyzer = MarketAnalyzer(market_data_config)
    print("✅ Analizador de mercado inicializado")
    
    # Analizar mercado actual
    print("🔍 Analizando mercado...")
    market_analysis = analyzer.analyze_market()
    print("✅ Análisis de mercado completado")
    
    # Generar reporte
    print("📄 Generando reporte...")
    report_gen = ReportGenerator(market_analysis)
    report_gen.generate_unified_report()
    print("✅ Reporte generado exitosamente")

if __name__ == "__main__":
    main()
