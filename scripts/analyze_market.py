import logging
from datetime import datetime
from src.market_analysis import MarketAnalyzer
from src.dca_optimizer_enhanced import EnhancedDCAOptimizer
from src.report_generator import ReportGenerator
from scripts.get_historical_data import CoinCodexDataCollector
from tqdm import tqdm
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Iniciando análisis de mercado usando CoinCodex...")
        
        # Inicializar colector de datos
        data_collector = CoinCodexDataCollector()
        
        # Obtener top 500 criptomonedas
        top_coins = data_collector.get_top_coins(limit=500)
        logger.info(f"Obtenidos datos de {len(top_coins)} criptomonedas")
        
        # Obtener datos de mercado para cada moneda con barra de progreso
        market_data = {}
        for coin in tqdm(top_coins, desc="Obteniendo datos de mercado"):
            symbol = coin['symbol']
            data = data_collector.get_market_data(symbol)
            if not data.empty:
                market_data[symbol] = data
                
        logger.info(f"Datos obtenidos para {len(market_data)} criptomonedas")
        
        # Analizar mercado
        analyzer = MarketAnalyzer()
        analysis = analyzer.analyze_market(market_data)
        
        # Optimizar DCA
        optimizer = EnhancedDCAOptimizer()
        optimization = optimizer.optimize_portfolio(market_data)
        
        # Generar reporte detallado
        report_gen = ReportGenerator(market_data)
        report_gen.generate_unified_report()
        
        # Guardar datos crudos para análisis posterior
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'data/market_data_{timestamp}.json', 'w') as f:
            json.dump(market_data, f)
        
        logger.info("Análisis completado. Revisa los reportes en la carpeta reports/")
        
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")

if __name__ == "__main__":
    main() 