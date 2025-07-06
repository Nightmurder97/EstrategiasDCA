import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import datetime
import logging
import matplotlib.pyplot as plt
from src.config_models import load_config
import os

class PortfolioVisualizer:
    def __init__(self, config=None):
        self.config = config or load_config()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def visualize_portfolio(self, market_data, output_path="portfolio_visualization.png"):
        """Visualizes the portfolio and saves the visualization to a file."""
        if not market_data:
            logging.error("No market data to visualize.")
            return
        try:
            symbols = list(market_data.keys())
            prices = [data.get("adjusted_price") for data in market_data.values()]
            if not all(prices):
                logging.error("Could not visualize portfolio, missing price data.")
                return
            
            plt.figure(figsize=(10, 6))
            plt.bar(symbols, prices, color='skyblue')
            plt.xlabel("Symbols")
            plt.ylabel("Adjusted Prices")
            plt.title("Portfolio Visualization")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path)
            plt.close()
            logging.info(f"Portfolio visualization saved to {output_path}")
        except Exception as e:
            logging.error(f"Error visualizing portfolio: {e}")

def test_portfolio_visualizer():
    """Basic test function for PortfolioVisualizer."""
    visualizer = PortfolioVisualizer()
    test_data = {
        "TEST1": {"adjusted_price": 150, "adjusted_volume": 1000},
        "TEST2": {"adjusted_price": 50, "adjusted_volume": 100},
    }
    visualizer.visualize_portfolio(test_data, "images/test_visualization.png")

if __name__ == "__main__":
    test_portfolio_visualizer()
