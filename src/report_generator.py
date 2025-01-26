import os
import logging
logger = logging.getLogger(__name__)
from src.market_analysis import MarketAnalyzer
from pathlib import Path

class ReportGenerator:
    def __init__(self, market_data):
        self.market_data = market_data
        self.reports_dir = Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def generate_market_analysis_report(self):
        """Generates a market analysis report."""
        if not self.market_data:
            logger.error("No market data available.")
            return False
        market_analysis = MarketAnalyzer(self.market_data)
        report_content = market_analysis.generate_report()
        report_path = self.reports_dir / "market_analysis_report.md"
        try:
            with open(report_path, "w") as f:
                f.write(report_content)
            logger.debug(f"Market analysis report generated: {report_path}")
            return True
        except Exception as e:
            logger.error(f"Error generating market analysis report: {e}")
            return False

    def generate_portfolio_report(self):
        """Generates a portfolio report."""
        # Implement portfolio report generation here
        pass

    def generate_unified_report(self):
        """Generates a unified report."""
        # Implement unified report generation here
        pass

async def generate_daily_reports(self, market_analysis, risk_assessment):
    """Generates daily reports."""
    try:
        # Generate market analysis report
        self.generate_market_analysis_report()

        # Generate portfolio report
        self.generate_portfolio_report()

        # Generate unified report
        self.generate_unified_report()

        logger.debug("Daily reports generated successfully")
    except Exception as e:
        logger.error(f"Error generating daily reports: {e}")
