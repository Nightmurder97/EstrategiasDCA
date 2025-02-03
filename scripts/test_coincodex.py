import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_coincodex_api():
    logger.info("Probando conexión con CoinCodex API...")
    
    # Probar endpoint de lista de monedas
    try:
        url = "https://coincodex.com/api/v1/coins"
        logger.info(f"Consultando {url}")
        response = requests.get(url)
        data = response.json()
        logger.info(f"Obtenidas {len(data)} monedas")
        
        # Mostrar primeras 5 monedas
        for coin in data[:5]:
            logger.info(f"Moneda: {coin['symbol']} - {coin.get('name', 'N/A')}")
            
        return True
    except Exception as e:
        logger.error(f"Error conectando con CoinCodex: {str(e)}")
        return False

if __name__ == "__main__":
    test_coincodex_api() 