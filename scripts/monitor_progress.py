import logging
from datetime import datetime
from tqdm import tqdm
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_data_collection():
    logger.info("Monitoreando recolección de datos...")
    data_dir = 'data/historical'
    
    # Crear directorio si no existe
    os.makedirs(data_dir, exist_ok=True)
    
    # Monitorear progreso
    with tqdm(total=500, desc="Recolectando datos") as pbar:
        previous_count = 0
        while True:
            files = [f for f in os.listdir(data_dir) if f.endswith('_historical_data.csv')]
            current_count = len(files)
            if current_count > previous_count:
                pbar.update(current_count - previous_count)
                previous_count = current_count
            if current_count >= 500:
                break

if __name__ == "__main__":
    monitor_data_collection() 