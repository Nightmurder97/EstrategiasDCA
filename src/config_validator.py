from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import Dict, Optional, Tuple
from datetime import time
import os
import re

# Regex para validación de email y API keys (case-insensitive para Binance)
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
CMC_API_KEY_REGEX = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
BINANCE_API_KEY_REGEX = r'(?i)^[A-Z0-9]{64}$'  # Case insensitive
BINANCE_SECRET_REGEX = r'(?i)^[A-Z0-9]{64}$'   # Case insensitive

# URLs de documentación
CMC_API_DOCS = "https://coinmarketcap.com/api/documentation/v1/"
BINANCE_API_DOCS = "https://binance-docs.github.io/apidocs/"

class RiskConfig(BaseModel):
    max_drawdown: float = Field(
        0.25, 
        ge=0, 
        le=0.5,
        description="Máximo drawdown permitido (0-50%)"
    )
    max_position_size: float = Field(
        0.30, 
        ge=0, 
        le=0.4,
        description="Tamaño máximo por posición (0-40%)"
    )
    volatility_threshold: float = Field(
        0.50, 
        ge=0, 
        le=1.0,
        description="Volatilidad máxima anualizada (0-100%)"
    )
    correlation_threshold: float = Field(
        0.75, 
        ge=0, 
        le=1,
        description="Correlación máxima entre activos (0-100%)"
    )
    min_liquidity: float = Field(
        1000000, 
        ge=0,
        description="Volumen mínimo diario en USD"
    )

    @field_validator('max_drawdown', 'max_position_size', 'volatility_threshold')
    @classmethod
    def validate_risk_params(cls, v: float, info) -> float:
        field_name = info.field_name
        if field_name == 'max_drawdown' and v > 0.5:
            raise ValueError(
                "El máximo drawdown permitido es 50%. "
                "Un valor mayor podría resultar en pérdidas excesivas."
            )
        if field_name == 'max_position_size' and v > 0.4:
            raise ValueError(
                "El tamaño máximo de posición permitido es 40%. "
                "Un valor mayor comprometería la diversificación del portfolio."
            )
        if field_name == 'volatility_threshold' and v > 1.0:
            raise ValueError(
                "El umbral de volatilidad máximo es 100%. "
                "Un valor mayor indicaría un riesgo excesivo."
            )
        return v

class TradingConfig(BaseModel):
    weekly_investment: float = Field(
        100.0, 
        gt=0,
        le=1000,
        description="Inversión semanal en EUR (1-1000€)"
    )
    lookback_period: int = Field(
        90, 
        ge=1,
        le=365,
        description="Período para análisis histórico (1-365 días)"
    )
    min_volume_percentile: float = Field(
        25, 
        ge=0, 
        le=100,
        description="Percentil mínimo de volumen (0-100)"
    )
    max_position_size: float = Field(
        0.30, 
        ge=0, 
        le=1,
        description="Tamaño máximo de posición (0-100%)"
    )
    rebalance_threshold: float = Field(
        0.05, 
        ge=0, 
        le=1,
        description="Umbral de rebalanceo (0-100%)"
    )

    @field_validator('weekly_investment')
    @classmethod
    def validate_investment(cls, v: float) -> float:
        if v > 1000:
            raise ValueError(
                "La inversión semanal no debe exceder 1000€. "
                "Este límite está establecido por razones de seguridad."
            )
        return v

class APIConfig(BaseSettings):
    cmc_api_key: str = Field(
        ..., 
        pattern=CMC_API_KEY_REGEX,
        env='CMC_API_KEY',
        description=f"API Key de CoinMarketCap (formato UUID v4). "
                   f"Obtener en: {CMC_API_DOCS}"
    )
    binance_api_key: Optional[str] = Field(
        None, 
        pattern=BINANCE_API_KEY_REGEX,
        env='BINANCE_API_KEY',
        description=f"API Key de Binance (64 caracteres alfanuméricos). "
                   f"Obtener en: {BINANCE_API_DOCS}"
    )
    binance_api_secret: Optional[str] = Field(
        None, 
        pattern=BINANCE_SECRET_REGEX,
        env='BINANCE_API_SECRET',
        description=f"API Secret de Binance (64 caracteres alfanuméricos). "
                   f"Obtener en: {BINANCE_API_DOCS}"
    )

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        validate_assignment = True
        case_sensitive = False  # Permitir variables de entorno case-insensitive

    @model_validator(mode='before')
    @classmethod
    def validate_api_keys_format(cls, values: Dict) -> Dict:
        """Valida el formato de las API keys antes de la validación principal"""
        cmc_key = values.get('cmc_api_key')
        if cmc_key and not re.match(CMC_API_KEY_REGEX, cmc_key, re.IGNORECASE):
            raise ValueError(
                "La API Key de CoinMarketCap debe tener el formato UUID v4. "
                "Ejemplo: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\n"
                f"Obtener una nueva key en: {CMC_API_DOCS}"
            )
        
        binance_key = values.get('binance_api_key')
        binance_secret = values.get('binance_api_secret')
        
        if binance_key and not re.match(BINANCE_API_KEY_REGEX, binance_key, re.IGNORECASE):
            raise ValueError(
                "La API Key de Binance debe tener 64 caracteres alfanuméricos.\n"
                f"Obtener una nueva key en: {BINANCE_API_DOCS}"
            )
        
        if binance_secret and not re.match(BINANCE_SECRET_REGEX, binance_secret, re.IGNORECASE):
            raise ValueError(
                "El API Secret de Binance debe tener 64 caracteres alfanuméricos.\n"
                f"Obtener un nuevo secret en: {BINANCE_API_DOCS}"
            )
        
        return values

    @model_validator(mode='after')
    def validate_binance_credentials(self) -> 'APIConfig':
        """Valida que las credenciales de Binance estén completas o ausentes"""
        if bool(self.binance_api_key) != bool(self.binance_api_secret):
            raise ValueError(
                "Las credenciales de Binance deben estar ambas presentes o ausentes. "
                "Por favor, proporcione tanto API_KEY como API_SECRET."
            )
        return self

class EmailConfig(BaseSettings):
    email_address: Optional[str] = Field(
        None, 
        pattern=EMAIL_REGEX,
        env='DCA_EMAIL',
        description="Dirección de email para envío"
    )
    email_password: Optional[str] = Field(
        None, 
        min_length=8,
        env='DCA_EMAIL_PASSWORD',
        description="Contraseña del email"
    )
    notification_email: Optional[str] = Field(
        None, 
        pattern=EMAIL_REGEX,
        env='DCA_NOTIFICATION_EMAIL',
        description="Dirección de email para notificaciones"
    )

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignorar campos adicionales

    @model_validator(mode='after')
    def validate_email_config(self) -> 'EmailConfig':
        """Valida que la configuración de email esté completa o ausente"""
        if any([self.email_address, self.email_password, self.notification_email]) and \
           not all([self.email_address, self.email_password, self.notification_email]):
            raise ValueError(
                "La configuración de email debe estar completa. "
                "Por favor, proporcione DCA_EMAIL, DCA_EMAIL_PASSWORD y DCA_NOTIFICATION_EMAIL."
            )
        return self

class SystemConfig(BaseModel):
    risk_params: RiskConfig
    trading_params: TradingConfig
    api_config: APIConfig
    email_config: EmailConfig
    daily_execution_time: time = Field(
        default=time(16, 0),
        description="Hora de ejecución diaria (formato HH:MM)"
    )
    run_on_start: bool = Field(
        default=True,
        description="Ejecutar al iniciar el sistema"
    )
    portfolio_weights: Dict[str, float] = Field(
        ...,
        description="Pesos de los activos en el portfolio"
    )
    backup_enabled: bool = Field(
        default=True,
        description="Habilitar backup automático"
    )
    email_notifications: bool = Field(
        default=True,
        description="Habilitar notificaciones por email"
    )

    @field_validator('portfolio_weights')
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Valida los pesos del portfolio"""
        if not v:
            raise ValueError(
                "El portfolio debe contener al menos un activo"
            )
        
        total = sum(v.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(
                f"Los pesos del portfolio deben sumar 1 (suma actual: {total:.4f}). "
                "Ajuste los pesos para que sumen exactamente 100%."
            )
        
        # Validar símbolos
        invalid_symbols = [
            symbol for symbol in v.keys() 
            if not symbol.endswith('USDT')
        ]
        if invalid_symbols:
            raise ValueError(
                f"Los siguientes símbolos son inválidos: {', '.join(invalid_symbols)}. "
                "Todos los símbolos deben terminar en USDT."
            )
        
        return v

    @model_validator(mode='after')
    def validate_email_notifications(self) -> 'SystemConfig':
        """Valida que las notificaciones por email tengan configuración válida"""
        if self.email_notifications:
            if not self.email_config or not all([
                self.email_config.email_address,
                self.email_config.email_password,
                self.email_config.notification_email
            ]):
                raise ValueError(
                    "Las notificaciones por email están habilitadas pero la configuración "
                    "de email está incompleta. Por favor, complete la configuración de email "
                    "o deshabilite las notificaciones."
                )
        return self

def load_and_validate_config(config_module) -> SystemConfig:
    """Carga y valida la configuración del sistema"""
    try:
        # Cargar configuración de APIs y email desde variables de entorno
        api_config = APIConfig()
        email_config = EmailConfig()

        # Crear configuración del sistema
        system_config = SystemConfig(
            risk_params=RiskConfig(**config_module.RISK_PARAMS),
            trading_params=TradingConfig(
                weekly_investment=config_module.WEEKLY_INVESTMENT,
                lookback_period=config_module.LOOKBACK_PERIOD,
                min_volume_percentile=config_module.MIN_VOLUME_PERCENTILE,
                max_position_size=config_module.MAX_POSITION_SIZE,
                rebalance_threshold=config_module.REBALANCE_THRESHOLD
            ),
            api_config=api_config,
            email_config=email_config,
            daily_execution_time=config_module.DAILY_EXECUTION_TIME,
            run_on_start=config_module.RUN_ON_START,
            portfolio_weights=config_module.PORTFOLIO_WEIGHTS,
            backup_enabled=config_module.BACKUP_ENABLED,
            email_notifications=config_module.EMAIL_NOTIFICATIONS
        )
        
        return system_config
    except Exception as e:
        raise ValueError(
            f"Error validando configuración: {str(e)}. "
            "Por favor, revise los valores en config.py y .env"
        ) 