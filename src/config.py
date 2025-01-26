import os
import logging
from datetime import time
from dotenv import load_dotenv
from typing import Dict, Optional
from dataclasses import dataclass
from pydantic import BaseModel, field_validator

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EmailConfig(BaseModel):
    """Configuración de email"""
    email: Optional[str] = None
    password: Optional[str] = None
    notification_email: Optional[str] = None

class RiskConfig(BaseModel):
    """Configuración de parámetros de riesgo"""
    max_drawdown: float = 0.25        # 25% máximo drawdown permitido
    max_position_size: float = 0.20   # 20% tamaño máximo por posición
    volatility_threshold: float = 0.50 # 50% volatilidad máxima anualizada
    correlation_threshold: float = 0.75 # 75% correlación máxima entre activos
    min_liquidity: int = 5000000      # Volumen mínimo diario en USD

    @field_validator('max_drawdown')
    def validate_max_drawdown(cls, v):
        if not 0 < v <= 0.5:
            raise ValueError("max_drawdown debe estar entre 0 y 0.5")
        return v

    @field_validator('max_position_size')
    def validate_max_position_size(cls, v):
        if not 0 < v <= 0.65:
            raise ValueError("max_position_size debe estar entre 0 y 0.65")
        return v

    @field_validator('volatility_threshold')
    def validate_volatility_threshold(cls, v):
        if not 0 < v <= 1.0:
            raise ValueError("volatility_threshold debe estar entre 0 y 1.0")
        return v

class TradingConfig(BaseModel):
    """Configuración de parámetros de trading"""
    weekly_investment: float = 100.0   # Inversión semanal en EUR
    lookback_period: int = 90         # Período para análisis histórico
    min_volume_percentile: int = 25   # Percentil mínimo de volumen
    max_position_size: float = 0.20   # Tamaño máximo de posición
    rebalance_threshold: float = 0.05 # Umbral de rebalanceo

class Config:
    """Configuración global del sistema"""
    def __init__(self):
        try:
            # Cargar variables de entorno
            load_dotenv()

            # Configuración de email
            self.email_config = EmailConfig(
                email=os.getenv('DCA_EMAIL'),
                password=os.getenv('DCA_EMAIL_PASSWORD'),
                notification_email=os.getenv('DCA_NOTIFICATION_EMAIL')
            )

            # Credenciales de Binance
            self.binance_api_key = os.getenv('BINANCE_API_KEY', 'Tro2UZTWPSwkV7v5RJvnOg3qJ9FSrrrW9BH8G4Qn0IumJGdM9LV73T1wF69h4PeA')
            self.binance_api_secret = os.getenv('BINANCE_API_SECRET', 'J5wpTFzo86NmljBUeOvBwYwLiAPlzFTwIRgfrErbhCIpu2C1yvCDpY83kmNPD243')

            # Parámetros de riesgo
            self.risk_params = RiskConfig()

            # Parámetros de trading
            self.trading_params = TradingConfig()

            # Pesos del portfolio
            self.portfolio_weights = {
                'WBTCUSDT': 0.10,  # 10%
                'BTCUSDT': 0.10,  # 10%
                'APTUSDT': 0.10,  # 10%
                'BCHUSDT': 0.10,  # 10%
                'BNSOLUSDT': 0.10,  # 10%
                'BONKUSDT': 0.10,  # 10%
                'FLOKIUSDT': 0.10,  # 10%
                'MKRUSDT': 0.10,  # 10%
                'SEIUSDT': 0.10,  # 10%
                'SOLUSDT': 0.10  # 10%
            }

            # Validar pesos del portfolio
            if abs(sum(self.portfolio_weights.values()) - 1.0) > 0.0001:
                raise ValueError("Los pesos del portfolio deben sumar 1")

            # Configuración de ejecución
            self.daily_execution_time = time(16, 0)  # 16:00
            self.run_on_start = True
            self.backup_enabled = True
            self.email_notifications = all([
                self.email_config.email,
                self.email_config.password,
                self.email_config.notification_email
            ])

        except Exception as e:
            logger.error(f"Error validando configuración: {str(e)}")
            raise ValueError(f"Error validando configuración: {str(e)}. Por favor, revise los valores en config.py y .env")

# Crear instancia global de configuración
config = Config()
