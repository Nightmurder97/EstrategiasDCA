import sqlite3
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Dict, Any, List

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = 'dca_trading.db'

class DataMarketAgent:
    def __init__(self, db_path: str = DB_PATH):
        """
        Inicializa el Agente de Inteligencia de Mercado.
        - Establece la conexión a la base de datos.
        - Inicializa la tabla de insights si no existe.
        - Configura el scheduler para las tareas de recolección.
        """
        self.db_path = db_path
        self.conn = self._create_connection()
        self._initialize_db()
        
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.run_collection_cycle, 'interval', minutes=15, id='market_intel_cycle')

    def _create_connection(self):
        """Crea y retorna una conexión a la base de datos SQLite."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            logger.info(f"Conexión a la base de datos en '{self.db_path}' establecida.")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error al conectar con la base de datos: {e}")
            raise

    def _initialize_db(self):
        """
        Asegura que la tabla 'market_insights' exista en la base de datos.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    insight_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sentiment_score REAL,
                    relevance_score REAL,
                    url TEXT,
                    tags TEXT,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()
            logger.info("Tabla 'market_insights' inicializada correctamente.")
        except sqlite3.Error as e:
            logger.error(f"Error al inicializar la tabla 'market_insights': {e}")
            
    def start(self):
        """Inicia el scheduler del agente."""
        logger.info("Iniciando el Agente de Inteligencia de Mercado...")
        self.scheduler.start()

    def stop(self):
        """Detiene el scheduler del agente."""
        logger.info("Deteniendo el Agente de Inteligencia de Mercado...")
        self.scheduler.shutdown()

    def run_collection_cycle(self):
        """
        Ciclo principal de recolección y procesamiento.
        Este método será el orquestador de todas las tareas.
        """
        logger.info("Iniciando ciclo de recolección de inteligencia de mercado...")
        # Aquí llamaremos a los colectores y procesadores
        # Ejemplo:
        # news = self.collect_crypto_news()
        # insights = self.process_news(news)
        # self.store_insights(insights)
        pass # Por ahora no hace nada

    # --- Métodos de Recolección (Web Scraping, APIs) ---
    # (Se implementarán en el Paso 2)

    # --- Métodos de Procesamiento (IA, Análisis de Sentimiento) ---
    # (Se implementarán en el Paso 3)

    def store_insights(self, insights: List[Dict[str, Any]]):
        """
        Almacena una lista de insights en la base de datos.
        """
        try:
            cursor = self.conn.cursor()
            for insight in insights:
                cursor.execute("""
                    INSERT INTO market_insights (source, insight_type, content, sentiment_score, relevance_score, url, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    insight.get('source'),
                    insight.get('insight_type'),
                    insight.get('content'),
                    insight.get('sentiment_score'),
                    insight.get('relevance_score'),
                    insight.get('url'),
                    ",".join(insight.get('tags', [])) if insight.get('tags') else None
                ))
            self.conn.commit()
            logger.info(f"{len(insights)} nuevos insights almacenados en la base de datos.")
        except sqlite3.Error as e:
            logger.error(f"Error al almacenar insights: {e}")

if __name__ == '__main__':
    # Ejemplo de uso y prueba
    agent = DataMarketAgent()
    
    # Simular la adición de un insight
    sample_insights = [
        {
            'source': 'Test',
            'insight_type': 'news_summary',
            'content': 'Bitcoin podría alcanzar un nuevo máximo histórico la próxima semana según análisis.',
            'sentiment_score': 0.85,
            'relevance_score': 0.9,
            'url': 'http://example.com/news1',
            'tags': ['bitcoin', 'ATH', 'prediction']
        }
    ]
    agent.store_insights(sample_insights)
    
    # Para probar el ciclo de fondo, se podría usar:
    # agent.start()
    # import time
    # try:
    #     while True:
    #         time.sleep(2)
    # except (KeyboardInterrupt, SystemExit):
    #     agent.stop()

    logger.info("Prueba del agente completada.") 