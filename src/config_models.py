"""
Configuración centralizada usando Pydantic para el sistema DCA
"""
import os
from typing import Dict, List, Optional
from datetime import time
from pydantic import BaseModel, Field, SecretStr, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- API Configuration Models ---
class BaseAPIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False)
    api_key: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    enabled: bool = True

class BinanceAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='BINANCE_') # type: ignore
    base_url: HttpUrl = "https://api.binance.com"
    api_secret: Optional[SecretStr] = None

    @model_validator(mode='after')
    def validate_creds(self) -> 'BinanceAPIConfig':
        if self.enabled and (bool(self.api_key) != bool(self.api_secret)):
            raise ValueError("Binance APIKey y APISecret deben estar ambos presentes o ausentes si está habilitado.")
        return self

class CoinMarketCapAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='CMC_') # type: ignore
    base_url: HttpUrl = "https://pro-api.coinmarketcap.com/v1"
    listings_endpoint: str = "/v1/cryptocurrency/listings/latest"
    quotes_endpoint: str = "/v1/cryptocurrency/quotes/latest"
    info_endpoint: str = "/v1/cryptocurrency/info"
    global_metrics_endpoint: str = "/v1/global-metrics/quotes/latest"

class EtherscanAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='ETHERSCAN_') # type: ignore
    base_url: HttpUrl = "https://api.etherscan.io"
    gas_oracle_endpoint: str = "/api?module=gastracker&action=gasoracle"
    latest_block_endpoint: str = "/api?module=proxy&action=eth_blockNumber"

class BscScanAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='BSCSCAN_') # type: ignore
    base_url: HttpUrl = "https://api.bscscan.com"
    gas_oracle_endpoint: str = "/api?module=gastracker&action=gasoracle"

class SolscanAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='SOLSCAN_') # type: ignore
    base_url: HttpUrl = "https://public-api.solscan.io"
    chain_info_endpoint: str = "/chaininfo"

class CoinGeckoAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='COINGECKO_') # type: ignore
    base_url: HttpUrl = "https://api.coingecko.com/api/v3"
    coins_markets_endpoint: str = "/coins/markets"
    coin_data_endpoint_template: str = "/coins/{id}"

class DefiLlamaAPIConfig(BaseAPIConfig):
    base_url: HttpUrl = "https://api.llama.fi"
    chains_endpoint: str = "/chains"
    protocols_endpoint: str = "/protocols"

class DeepSeekAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='DEEPSEEK_') # type: ignore
    base_url: HttpUrl = "https://api.deepseek.com/v1"

class LiveCoinWatchAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='LIVECOINWATCH_') # type: ignore
    base_url: HttpUrl = "https://api.livecoinwatch.com"

# --- Other Parameter Models ---
class RiskConfig(BaseModel):
    max_drawdown: float = Field(0.25, ge=0.01, le=0.5, description="Máximo drawdown permitido (1-50%)")
    max_position_size: float = Field(0.20, ge=0.01, le=0.4, description="Tamaño máximo por posición como % del portfolio (1-40%)")
    volatility_threshold: float = Field(0.50, ge=0.01, le=1.0, description="Volatilidad máxima anualizada permitida (1-100%)")
    portfolio_correlation_threshold: float = Field(0.75, ge=0, le=1.0, description="Correlación máxima permitida entre activos (0-100%)")
    min_liquidity: int = Field(5000000, ge=0, description="Volumen mínimo diario en USD requerido para un activo")

    @field_validator('max_drawdown')
    def validate_max_drawdown(cls, v: float) -> float:
        if not (0.01 <= v <= 0.5):
            raise ValueError("max_drawdown debe estar entre 0.01 (1%) y 0.5 (50%).")
        return v

    @field_validator('max_position_size')
    def validate_max_position_size(cls, v: float) -> float:
        if not (0.01 <= v <= 0.4):
            raise ValueError("max_position_size debe estar entre 0.01 (1%) y 0.4 (40%).")
        return v

    @field_validator('volatility_threshold')
    def validate_volatility_threshold(cls, v: float) -> float:
        if not (0.01 <= v <= 1.0):
            raise ValueError("volatility_threshold debe estar entre 0.01 (1%) y 1.0 (100%).")
        return v

class TradingConfig(BaseModel):
    weekly_investment: float = Field(100.0, gt=0, le=10000, description="Inversión semanal en EUR (ej: 100.0)")
    lookback_period: int = Field(90, ge=7, le=365, description="Período en días para análisis histórico (ej: 90)")
    min_volume_percentile: float = Field(25.0, ge=0, le=100, description="Percentil mínimo de volumen para considerar un activo (ej: 25.0)")
    rebalance_threshold: float = Field(0.05, ge=0.01, le=0.5, description="Umbral de desviación para rebalanceo (ej: 0.05 para 5%)")
    daily_execution_time: time = Field(time(16, 0), description="Hora de ejecución diaria (16:00)")

    @field_validator('weekly_investment')
    def validate_weekly_investment(cls, v: float) -> float:
        if v > 10000:
            raise ValueError("La inversión semanal no debe exceder 10000 EUR. Ajuste si es necesario.")
        return v

class EmailSettings(BaseModel):
    email: Optional[str] = Field(None, description="Email del remitente")
    password: Optional[SecretStr] = Field(None, description="Contraseña del email")
    notification_email: Optional[str] = Field(None, description="Email de notificaciones")

    @field_validator('email', 'password', 'notification_email')
    def validate_email_completeness(cls, v, info):
        """Si se proporciona un email, todos los campos deben estar presentes"""
        values = info.data
        if any([values.get('email'), values.get('password'), values.get('notification_email')]):
            if not all([values.get('email'), values.get('password'), values.get('notification_email')]):
                raise ValueError("Si se configura email, todos los campos (email, password, notification_email) son requeridos")
        return v

class AssetDetails(BaseModel):
    name: str = Field(..., description="Nombre del activo")
    category: str = Field(..., description="Categoría del activo")
    weight: float = Field(..., description="Peso en el portafolio")

    @field_validator('weight')
    def validate_weight(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("El peso debe estar entre 0 y 1")
        return v

class AnalysisParamsConfig(BaseModel):
    main_assets: Dict[str, AssetDetails] = Field(
        default={
            'BTC': AssetDetails(name='Bitcoin', category='Store of Value'),
            'ETH': AssetDetails(name='Ethereum', category='Smart Contract Platform'),
            'BNB': AssetDetails(name='BNB', category='Exchange Token'),
            'SOL': AssetDetails(name='Solana', category='Smart Contract Platform'),
            'ADA': AssetDetails(name='Cardano', category='Smart Contract Platform')
        },
        description="Activos principales para análisis"
    )
    asset_categories: Dict[str, List[str]] = Field(
        default={
            'Store of Value': ['BTC'],
            'Smart Contract Platform': ['ETH', 'SOL', 'ADA'],
            'Exchange Token': ['BNB'],
            'DeFi': [],
            'Gaming': [],
            'Infrastructure': []
        },
        description="Categorías de activos y sus miembros"
    )
    lookback_period: int = Field(90, description="Período de análisis en días")
    rsi_period: int = Field(14, description="Período para cálculo de RSI")
    volume_ma_period: int = Field(20, description="Período para media móvil de volumen")
    min_market_cap: int = Field(100_000_000, description="Market cap mínimo ($100M)")
    min_volume_24h: int = Field(1_000_000, description="Volumen 24h mínimo ($1M)")
    trend_analysis_period: int = Field(30, description="Período de análisis de tendencia (días)")
    analysis_correlation_threshold: float = Field(0.7, description="Umbral de correlación para análisis")
    volume_ratio_threshold: float = Field(2.0, description="Umbral de ratio de volumen")

class BlockTimeValidationDetail(BaseModel):
    min_time: float
    max_time: float

class ReportParamsConfig(BaseModel):
    block_sample_size: Dict[str, int] = Field(
        default={
            'ethereum': 100,
            'bsc': 100,
            'solana': 1440
        },
        description="Tamaño de muestra de bloques por cadena"
    )
    block_time_validation: Dict[str, BlockTimeValidationDetail] = Field(
        default={
            'ethereum': BlockTimeValidationDetail(min_time=10, max_time=20),
            'bsc': BlockTimeValidationDetail(min_time=2, max_time=5),
            'solana': BlockTimeValidationDetail(min_time=0.4, max_time=1.0)
        },
        description="Validación de tiempos de bloque por cadena"
    )

class DatabaseConfig(BaseModel):
    url: str = Field("sqlite:///dca_trading.db", description="URL de la base de datos")
    echo: bool = Field(False, description="Si mostrar logs de SQL")

class DCAConfig(BaseSettings):
    # APIs
    all_apis: AllAPIsConfig = Field(default_factory=AllAPIsConfig)
    
    # Configuraciones de sistema
    risk: RiskConfig = Field(default_factory=RiskConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    email: EmailSettings = Field(default_factory=EmailSettings)
    analysis: AnalysisParamsConfig = Field(default_factory=AnalysisParamsConfig)
    reports: ReportParamsConfig = Field(default_factory=ReportParamsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Configuraciones de ejecución
    run_on_start: bool = Field(True, description="Ejecutar al iniciar")
    backup_enabled: bool = Field(True, description="Backup habilitado")
    
    # Portafolio
    portfolio_weights: Dict[str, float] = Field(
        default={
            'WBTCUSDT': 0.10, 'BTCUSDT': 0.10, 'APTUSDT': 0.10, 'BCHUSDT': 0.10,
            'BNSOLUSDT': 0.10, 'BONKUSDT': 0.10, 'FLOKIUSDT': 0.10, 'MKRUSDT': 0.10,
            'SEIUSDT': 0.10, 'SOLUSDT': 0.10
        },
        description="Pesos del portafolio DCA"
    )
    
    # Assets del portafolio personal
    portfolio_assets: Dict[str, float] = Field(
        default={
            'XRP': 162.8723621, 'DOGE': 436.2181809, 'ADA': 87.73678816,
            'BTC': 0.00074945, 'VET': 315.5911201, 'DOT': 2.25790476,
            'SOL': 0.04004547, 'GALA': 117.8849052, 'XCN': 7478.1641,
            'TEL': 14923, 'RUNE': 19.9385, 'HBAR': 86.9489, 'PENGU': 1187,
            'TON': 1.74166884, 'WIN': 47754.0626
        },
        description="Assets del portafolio personal actual"
    )

    @field_validator('portfolio_weights')
    def validate_portfolio_weights(cls, v):
        """Validar que los pesos del portafolio sumen 1"""
        total = sum(v.values())
        if abs(total - 1.0) > 0.0001:
            raise ValueError(f"Los pesos del portafolio deben sumar 1, suma actual: {total}")
        return v

    @property
    def email_notifications_enabled(self) -> bool:
        """Verificar si las notificaciones por email están habilitadas"""
        return all([
            self.email.email,
            self.email.password,
            self.email.notification_email
        ])

    class Config(SettingsConfigDict):
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "allow"

# Función para cargar la configuración
def load_config() -> DCAConfig:
    """Cargar configuración desde variables de entorno y archivos .env"""
    return DCAConfig()

# Instancia global de configuración
config = load_config()
