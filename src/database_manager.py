import logging
from typing import Dict, List, Optional
from datetime import datetime
import traceback
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sqlalchemy.orm import declarative_base

Base = declarative_base()
Base = declarative_base()

class PortfolioState(Base):
    __tablename__ = 'portfolio_states'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    total_value = Column(Float, nullable=False)
    positions = Column(JSON, nullable=False)
    weights = Column(JSON, nullable=False)
    metrics = Column(JSON)  # Métricas adicionales
    
class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'buy' o 'sell'
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    
class MarketData(Base):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    market_cap = Column(Float)
    rsi = Column(Float)  # RSI
    macd = Column(Float)  # MACD
    macd_signal = Column(Float)  # Señal MACD
    bb_upper = Column(Float)  # Banda superior de Bollinger
    bb_lower = Column(Float)  # Banda inferior de Bollinger
    volatility = Column(Float)  # Volatilidad
    momentum = Column(Float)  # Momentum

class DatabaseManager:
    def __init__(self, config: Optional[Dict] = None):
        db_url = os.getenv('DATABASE_URL', 'sqlite:///dca_trading.db')
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Store configuration if provided
        self.config = config or {}
        if self.config.get('email_notifications', False):
            self._setup_email_notifications()
            
    def _setup_email_notifications(self):
        """Configure email notifications if enabled"""
        if not self.config.get('email_config'):
            logger.warning("Email notifications enabled but no email config provided")
            return
            
        # Setup email notification system
        try:
            from src.email_notifier import EmailNotifier
            self.email_notifier = EmailNotifier(self.config['email_config'])
            logger.info("Email notifications configured")
        except ImportError:
            logger.warning("Email notification module not available")
    
    def save_portfolio_state(self, total_value: float, positions: Dict[str, float], 
                           weights: Dict[str, float]):
        """Guarda el estado actual del portfolio"""
        try:
            session = self.Session()
            state = PortfolioState(
                timestamp=datetime.now(),
                total_value=total_value,
                positions=positions,
                weights=weights
            )
            session.add(state)
            session.commit()
            logger.info("Estado del portfolio guardado exitosamente")
        except Exception as e:
            logger.error(f"Error guardando estado del portfolio: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def record_transaction(self, symbol: str, type_: str, amount: float, price: float):
        """Registra una transacción"""
        try:
            session = self.Session()
            transaction = Transaction(
                timestamp=datetime.now(),
                symbol=symbol,
                type=type_,
                amount=amount,
                price=price
            )
            session.add(transaction)
            session.commit()
            logger.info(f"Transacción registrada: {symbol} {type_} {amount} @ {price}")
        except Exception as e:
            logger.error(f"Error registrando transacción: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def save_market_data(self, symbol: str, price: float, volume: float, 
                        market_cap: Optional[float] = None):
        """Guarda datos de mercado"""
        try:
            session = self.Session()
            market_data = MarketData(
                timestamp=datetime.now(),
                symbol=symbol,
                price=price,
                volume=volume,
                market_cap=market_cap
            )
            session.add(market_data)
            session.commit()
        except Exception as e:
            logger.error(f"Error guardando datos de mercado: {str(e)}")
            session.rollback()
        finally:
            session.close()
            
    def save_market_data_bulk(self, data_list: List[Dict]):
        """Guarda múltiples datos de mercado de forma eficiente"""
        try:
            session = self.Session()
            session.bulk_insert_mappings(MarketData, data_list)
            session.commit()
            logger.info(f"Guardados {len(data_list)} registros de mercado")
        except Exception as e:
            logger.error(f"Error guardando datos de mercado en bulk: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()
            
    def save_portfolio_state_with_metrics(self, total_value: float, positions: Dict[str, float], 
                                        weights: Dict[str, float], metrics: Dict[str, Dict]):
        """Guarda el estado del portfolio con métricas adicionales"""
        try:
            session = self.Session()
            state = PortfolioState(
                timestamp=datetime.now(),
                total_value=total_value if total_value is not None else 0.0,
                positions=positions if positions else {},
                weights=weights if weights else {},
                metrics=metrics if metrics else {}
            )
            session.add(state)
            session.commit()
            logger.info("Estado del portfolio guardado con métricas")
        except Exception as e:
            logger.error(f"Error guardando estado del portfolio: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_portfolio_history(self, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Obtiene el historial del portfolio"""
        try:
            query = "SELECT * FROM portfolio_states"
            if start_date and end_date:
                query += f" WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'"
            elif start_date:
                query += f" WHERE timestamp >= '{start_date}'"
            elif end_date:
                query += f" WHERE timestamp <= '{end_date}'"
            
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            logger.error(f"Error obteniendo historial del portfolio: {str(e)}")
            return pd.DataFrame()
    
    def get_transaction_history(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """Obtiene el historial de transacciones"""
        try:
            query = "SELECT * FROM transactions"
            if symbol:
                query += f" WHERE symbol = '{symbol}'"
            
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            logger.error(f"Error obteniendo historial de transacciones: {str(e)}")
            return pd.DataFrame()
    
    def get_market_data_history(self, symbol: str, 
                              start_date: Optional[datetime] = None) -> pd.DataFrame:
        """Obtiene el historial de datos de mercado"""
        try:
            query = f"SELECT * FROM market_data WHERE symbol = '{symbol}'"
            if start_date:
                query += f" AND timestamp >= '{start_date}'"
            
            df = pd.read_sql(query, self.engine)
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos de mercado: {str(e)}")
            return pd.DataFrame()
            
    def close(self):
        """Cierra la conexión a la base de datos"""
        try:
            self.engine.dispose()
            logger.info("Conexión a la base de datos cerrada exitosamente")
        except Exception as e:
            logger.error(f"Error al cerrar la conexión a la base de datos: {str(e)}")
            
    async def log_trading_session(self, market_analysis: Dict, risk_assessment: Dict):
        """Log trading session results"""
        try:
            session = self.Session()
            
            # Save portfolio state
            portfolio_state = {
                'total_value': risk_assessment.get('portfolio_value'),
                'positions': risk_assessment.get('positions'),
                'weights': risk_assessment.get('weights'),
                'metrics': {
                    'risk_score': risk_assessment.get('risk_score'),
                    'market_conditions': market_analysis.get('market_conditions')
                }
            }
            self.save_portfolio_state_with_metrics(**portfolio_state)
            
            # Save market data
            for symbol, data in market_analysis.get('symbol_data', {}).items():
                self.save_market_data(
                    symbol=symbol,
                    price=data.get('price'),
                    volume=data.get('volume'),
                    market_cap=data.get('market_cap')
                )
                
            session.commit()
            logger.info("Sesión de trading registrada exitosamente")
            
        except Exception as e:
            logger.error(f"Error registrando sesión de trading: {str(e)}")
            session.rollback()
            raise
        finally:
    def import_from_exchange(self, file_path: str, exchange: str):
        """Importa datos desde un archivo CSV de una bolsa de criptomonedas y actualiza el portafolio y transacciones."""
        try:
            import pandas as pd
            
            # Leer el archivo CSV
            df = pd.read_csv(file_path)
            
            # Procesar cada fila
            for _, row in df.iterrows():
                # Extraer información de la transacción
                symbol = row['symbol'].upper()
                amount = float(row['amount'])
                price = float(row['price'])
                date = row['date']
                
                # Registrar transacción
                self.record_transaction(symbol, 'buy', amount, price)
                
                # Actualizar estado del portafolio
                portfolio_state = {
                    'total_value': float(row['total'] or 0),
                    'positions': {symbol: amount},
                    'weights': {symbol: (amount * price) / float(row['total'] or 0)}
                }
                self.save_portfolio_state_with_metrics(**portfolio_state)
            
            logger.info(f"Se han importado {len(df)} transacciones de {exchange} correctamente")
        except Exception as e:
            logger.error(f"Error al importar datos de {exchange}: {str(e)}")
            raise
    def import_from_exchange(self, file_path: str, exchange: str):
        """Importa datos desde un archivo CSV de una bolsa de criptomonedas y actualiza el portafolio y transacciones."""
        try:
            import pandas as pd
            
            # Leer el archivo CSV
            df = pd.read_csv(file_path)
            
            # Procesar cada fila
            for _, row in df.iterrows():
                # Extraer información de la transacción
                symbol = row['symbol'].upper()
                amount = float(row['amount'])
                price = float(row['price'])
                date = row['date']
                
                # Registrar transacción
                self.record_transaction(symbol, 'buy', amount, price)
                
                # Actualizar estado del portafolio
                portfolio_state = {
                    'total_value': float(row['total'] or 0),
                    'positions': {symbol: amount},
                    'weights': {symbol: (amount * price) / float(row['total'] or 0)}
                }
                self.save_portfolio_state_with_metrics(**portfolio_state)
            
            logger.info(f"Se han importado {len(df)} transacciones de {exchange} correctamente")
        except Exception as e:
            logger.error(f"Error al importar datos de {exchange}: {str(e)}")
            raise
    def import_from_exchange(self, file_path: str, exchange: str):
        """Importa datos desde un archivo CSV de una bolsa de criptomonedas y actualiza el portafolio y transacciones."""
        try:
            import pandas as pd
            
            # Leer el archivo CSV
            df = pd.read_csv(file_path)
            
            # Procesar cada fila
            for _, row in df.iterrows():
                # Extraer información de la transacción
                symbol = row['symbol'].upper()
                amount = float(row['amount'])
                price = float(row['price'])
                date = row['date']
                
                # Registrar transacción
                self.record_transaction(symbol, 'buy', amount, price)
                
                # Actualizar estado del portafolio
                portfolio_state = {
                    'total_value': float(row['total'] or 0),
                    'positions': {symbol: amount},
                    'weights': {symbol: (amount * price) / float(row['total'] or 0)}
                }
                self.save_portfolio_state_with_metrics(**portfolio_state)
            
            logger.info(f"Se han importado {len(df)} transacciones de {exchange} correctamente")
        except Exception as e:
            logger.error(f"Error al importar datos de {exchange}: {str(e)}")
            raise
    def import_from_exchange(self, file_path: str, exchange: str):
        """Importa datos desde un archivo CSV de una bolsa de criptomonedas y actualiza el portafolio y transacciones."""
        try:
            import pandas as pd
            
            # Leer el archivo CSV
            df = pd.read_csv(file_path)
            
            # Procesar cada fila
            for _, row in df.iterrows():
                # Extraer información de la transacción
                symbol = row['symbol'].upper()
                amount = float(row['amount'])
                price = float(row['price'])
                date = row['date']
                
                # Registrar transacción
                self.record_transaction(symbol, 'buy', amount, price)
                
                # Actualizar estado del portafolio
                portfolio_state = {
                    'total_value': float(row['total'] or 0),
                    'positions': {symbol: amount},
                    'weights': {symbol: (amount * price) / float(row['total'] or 0)}
                }
                self.save_portfolio_state_with_metrics(**portfolio_state)
            
            logger.info(f"Se han importado {len(df)} transacciones de {exchange} correctamente")
        except Exception as e:
            logger.error(f"Error al importar datos de {exchange}: {str(e)}")
            raise
    def import_from_exchange(self, file_path: str, exchange: str):
        """Importa datos desde un archivo CSV de una bolsa de criptomonedas y actualiza el portafolio y transacciones."""
        try:
            import pandas as pd
            
            # Leer el archivo CSV
            df = pd.read_csv(file_path)
            
            # Procesar cada fila
            for _, row in df.iterrows():
                # Extraer información de la transacción
                symbol = row['symbol'].upper()
                amount = float(row['amount'])
                price = float(row['price'])
                date = row['date']
                
                # Registrar transacción
                self.record_transaction(symbol, 'buy', amount, price)
                
                # Actualizar estado del portafolio
                portfolio_state = {
                    'total_value': float(row['total'] or 0),
                    'positions': {symbol: amount},
                    'weights': {symbol: (amount * price) / float(row['total'] or 0)}
                }
                self.save_portfolio_state_with_metrics(**portfolio_state)
            
            logger.info(f"Se han importado {len(df)} transacciones de {exchange} correctamente")
        except Exception as e:
            logger.error(f"Error al importar datos de {exchange}: {str(e)}")
            raise
            session.close()

    def import_from_excel(self, file_path: str):
        """Importa datos desde un archivo Excel y actualiza el portafolio y transacciones."""
        try:
            import pandas as pd
            
            # Leer el archivo Excel
            df = pd.read_excel(file_path)
            
            # Procesar cada fila
            for _, row in df.iterrows():
                # Extraer información de la transacción
                symbol = row['symbol'].upper()
                amount = float(row['amount'])
                price = float(row['price'])
                date = row['date']
                
                # Registrar transacción
                self.record_transaction(symbol, 'buy', amount, price)
                
                # Actualizar estado del portafolio
                portfolio_state = {
                    'total_value': float(row['total'] or 0),
                    'positions': {symbol: amount},
                    'weights': {symbol: (amount * price) / float(row['total'] or 0)}
                }
                self.save_portfolio_state_with_metrics(**portfolio_state)
            
            logger.info(f"Se han importado {len(df)} transacciones correctamente")
        except Exception as e:
            logger.error(f"Error al importar datos desde Excel: {str(e)}")
            raise
