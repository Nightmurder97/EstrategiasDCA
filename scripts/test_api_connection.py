import requests
import logging
from datetime import datetime
import pandas as pd
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_apis():
    logger.info("Iniciando pruebas de conexión...")
    
    # Probar CoinCodex
    try:
        # Probar lista de monedas
        url = "https://coincodex.com/api/v1/coins"
        response = requests.get(url)
        coins = response.json()
        logger.info(f"CoinCodex: OK - {len(coins)} monedas obtenidas")
        
        # Probar datos históricos de BTC
        hist_url = "https://coincodex.com/api/v1/get_coin/BTC"
        hist_response = requests.get(hist_url)
        hist_data = hist_response.json()
        logger.info("CoinCodex histórico: OK")
        
        # Guardar ejemplo
        df = pd.DataFrame([hist_data])
        os.makedirs('data/test', exist_ok=True)
        df.to_csv('data/test/btc_test.csv')
        logger.info("Datos de prueba guardados en data/test/btc_test.csv")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en pruebas: {str(e)}")
        return False

if __name__ == "__main__":
    test_apis() 