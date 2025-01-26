import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from src.config import config
from src.dca_live_trader import LiveDCATrader as DCALiveTrader
from src.market_analysis import MarketAnalyzer
from src.risk_manager import RiskManager
from src.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DCAScheduler:
    def __init__(self):
        self.analyzer = None
        self.risk_manager = None
        self.trader = None
        self.db_manager = None

    async def initialize_components(self):
        """Initialize all system components"""
        initialization_tasks = [
            self._initialize_risk_manager(),
            self._initialize_trader(),
            self._initialize_market_analyzer(),
            self._initialize_db_manager()
        ]

        await asyncio.gather(*initialization_tasks)
        logger.info("Todos los componentes inicializados")

    async def _initialize_risk_manager(self):
        """Initialize risk manager component"""
        self.risk_manager = RiskManager()
        logger.info("Gestor de riesgos inicializado")

    async def _initialize_trader(self):
        """Initialize trader component"""
        trading_params = {
            'weekly_investment': config.trading_params.weekly_investment,
            'portfolio_weights': config.portfolio_weights,
            'max_position_size': config.trading_params.max_position_size,
            'rebalance_threshold': config.trading_params.rebalance_threshold
        }
        self.trader = DCALiveTrader(trading_params)
        logger.info("Trader inicializado")

    async def _initialize_market_analyzer(self):
        """Initialize market analyzer component"""
        market_data_config = {
            'lookback_period': config.trading_params.lookback_period,
            'min_volume_percentile': config.trading_params.min_volume_percentile,
            'portfolio_weights': config.portfolio_weights,
            'binance_api_key': config.binance_api_key,
            'binance_api_secret': config.binance_api_secret
        }
        self.analyzer = MarketAnalyzer(market_data_config)
        logger.info("Market analyzer inicializado")

    async def _initialize_db_manager(self):
        """Initialize database manager component"""
        db_config = {
            'backup_enabled': config.backup_enabled,
            'email_notifications': config.email_notifications,
            'email_config': config.email_config.model_dump()
        }
        self.db_manager = DatabaseManager(db_config)
        logger.info("Gestor de base de datos inicializado")

    async def run(self):
        """Main execution loop"""
        logger.debug("Iniciando el bucle principal")
        try:
            while True:
                try:
                    # Check market conditions
                    market_analysis = await self.analyzer.analyze_market()

                    if market_analysis.get('market_conditions') == 'error':
                        logger.error(f"Market analysis error: {market_analysis.get('error')}")
                        await asyncio.sleep(600)  # Wait 10 minutes before retrying
                        continue

                    # Evaluate risk parameters
                    risk_assessment = await self.risk_manager.evaluate_risk(market_analysis)

                    if risk_assessment.get('error'):
                        logger.error(f"Risk assessment error: {risk_assessment.get('error')}")
                        await asyncio.sleep(600)  # Wait 10 minutes before retrying
                        continue

                    # Execute trades if conditions are met
                    if risk_assessment.get('should_trade', False):
                        logger.info("Market conditions favorable - executing trades")
                        trade_result = await self.trader.execute_trades(market_analysis)

                        if trade_result.get('error'):
                            logger.error(f"Trade execution error: {trade_result.get('error')}")
                        else:
                            logger.info(f"Trades executed successfully: {trade_result}")
                    else:
                        logger.info("Market conditions not favorable - skipping trades")

                    # Log results
                    await self.db_manager.log_trading_session(market_analysis, risk_assessment)

                    # Print market analysis and risk assessment to terminal
                    print("\n=== ANÁLISIS DE MERCADO ===")
                    print(f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d')}")
                    print(f"Total activos analizados: {len(market_analysis.get('assets', []))}")
                    print(f"Recomendaciones generadas: {len(risk_assessment.get('recommendations', []))}")
                    print(f"Portafolio actual: {risk_assessment.get('portfolio_summary', {}).get('total_value', 0):.2f}€")
                    print(f"Rendimiento diario: {risk_assessment.get('portfolio_summary', {}).get('daily_performance', 0):.2f}%")
                    print("Condiciones de mercado:")
                    for asset, conditions in market_analysis.get('market_conditions', {}).items():
                        print(f"  {asset}: {conditions}")
                    print("Evaluación de riesgos:")
                    for recommendation in risk_assessment.get('recommendations', []):
                        print(f"  {recommendation}")
                    print("===============================\n")

                    # Wait for next cycle
                    await asyncio.sleep(3600)  # Sleep for 1 hour between cycles

                except Exception as e:
                    logger.error(f"Error in trading cycle: {e}")
                    await asyncio.sleep(600)  # Wait 10 minutes before retrying

        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
            raise

async def main():
    """Main entry point"""
    try:
        # Initialize scheduler
        scheduler = DCAScheduler()
        await scheduler.initialize_components()

        # Start main loop
        await scheduler.run()

    except Exception as e:
        logger.error(f"Error fatal en el sistema: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())
