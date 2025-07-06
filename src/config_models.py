from datetime import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- API Configuration Models ---
class BaseAPIConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False)
    api_key: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    enabled: bool = True
    # timeout: int = 30 # Add iteratively
    # retry_count: int = 3 # Add iteratively

class BinanceAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='BINANCE_') # type: ignore
    base_url: HttpUrl = "https://api.binance.com"
    api_secret: Optional[str] = None

    @model_validator(mode='after')
    def validate_creds(self) -> 'BinanceAPIConfig':
        if self.enabled and (bool(self.api_key) != bool(self.api_secret)):
            raise ValueError("Binance APIKey and APISecret must be both present or absent if enabled.")
        return self

class CoinMarketCapAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='CMC_') # type: ignore
    base_url: HttpUrl = "https://pro-api.coinmarketcap.com"
    # api_key field inherited
    listings_endpoint: str = "/v1/cryptocurrency/listings/latest"
    quotes_endpoint: str = "/v1/cryptocurrency/quotes/latest"
    info_endpoint: str = "/v1/cryptocurrency/info"
    global_metrics_endpoint: str = "/v1/global-metrics/quotes/latest"
    # Add more endpoints as needed

# Add other specific API Configs (Etherscan, Solscan, etc.) iteratively
class EtherscanAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='ETHERSCAN_') # type: ignore
    base_url: HttpUrl = "https://api.etherscan.io"
    gas_oracle_endpoint: str = "/api?module=gastracker&action=gasoracle"
    latest_block_endpoint: str = "/api?module=proxy&action=eth_blockNumber"
    # Add more endpoints as needed

class BscScanAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='BSCSCAN_') # type: ignore
    base_url: HttpUrl = "https://api.bscscan.com"
    gas_oracle_endpoint: str = "/api?module=gastracker&action=gasoracle"
    # Add more endpoints as needed

class SolscanAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='SOLSCAN_') # type: ignore
    base_url: HttpUrl = "https://public-api.solscan.io"
    chain_info_endpoint: str = "/chaininfo"
    # Add more endpoints as needed

class CoinGeckoAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='COINGECKO_') # type: ignore
    base_url: HttpUrl = "https://api.coingecko.com/api/v3" # Public API base
    coins_markets_endpoint: str = "/coins/markets"
    coin_data_endpoint_template: str = "/coins/{id}" # Using {id} for templating
    # Add more endpoints as needed

class DefiLlamaAPIConfig(BaseAPIConfig):
    # No env_prefix needed as no API key is typically used
    base_url: HttpUrl = "https://api.llama.fi"
    chains_endpoint: str = "/chains"
    protocols_endpoint: str = "/protocols"
    # Add more endpoints as needed

class DeepSeekAPIConfig(BaseAPIConfig):
    model_config = SettingsConfigDict(env_prefix='DEEPSEEK_') # type: ignore
    base_url: HttpUrl = "https://api.deepseek.com/v1"
    # Define specific endpoints if known, e.g., from analysis_config.py
    # analysis_endpoint: str = "/analysis"
    # For now, leave specific endpoints to be added if DEEPSEEK_CONFIG from analysis_config.py is fully migrated.

class AllAPIsConfig(BaseModel):
    binance: BinanceAPIConfig = Field(default_factory=BinanceAPIConfig)
    coinmarketcap: CoinMarketCapAPIConfig = Field(default_factory=CoinMarketCapAPIConfig)
    etherscan: EtherscanAPIConfig = Field(default_factory=EtherscanAPIConfig)
    bscscan: BscScanAPIConfig = Field(default_factory=BscScanAPIConfig)
    solscan: SolscanAPIConfig = Field(default_factory=SolscanAPIConfig)
    coingecko: CoinGeckoAPIConfig = Field(default_factory=CoinGeckoAPIConfig)
    defillama: DefiLlamaAPIConfig = Field(default_factory=DefiLlamaAPIConfig)
    deepseek: DeepSeekAPIConfig = Field(default_factory=DeepSeekAPIConfig)
    # Add other APIs here

# --- Other Parameter Models ---
class RiskConfig(BaseModel):
    max_drawdown: float = Field(0.25, ge=0.01, le=0.5, description="Máximo drawdown permitido (1-50%)")
    max_position_size_pct: float = Field(0.20, ge=0.01, le=0.4, description="Tamaño máximo por posición como % del portfolio (1-40%)")
    volatility_threshold: float = Field(0.50, ge=0.01, le=1.0, description="Volatilidad máxima anualizada permitida (1-100%)")
    correlation_threshold: float = Field(0.75, ge=0, le=1.0, description="Correlación máxima permitida entre activos (0-100%)") # Similar field in AnalysisParamsConfig
    min_liquidity_usd: float = Field(5000000, ge=0, description="Volumen mínimo diario en USD requerido para un activo")

    @field_validator('max_drawdown')
    @classmethod
    def validate_max_drawdown(cls, v: float) -> float:
        if not (0.01 <= v <= 0.5):
            raise ValueError("max_drawdown debe estar entre 0.01 (1%) y 0.5 (50%).")
        return v

    @field_validator('max_position_size_pct')
    @classmethod
    def validate_max_position_size_pct(cls, v: float) -> float:
        if not (0.01 <= v <= 0.4):
            raise ValueError("max_position_size_pct debe estar entre 0.01 (1%) y 0.4 (40%).")
        return v

    @field_validator('volatility_threshold')
    @classmethod
    def validate_volatility_threshold(cls, v: float) -> float:
        if not (0.01 <= v <= 1.0):
            raise ValueError("volatility_threshold debe estar entre 0.01 (1%) y 1.0 (100%).")
        return v

class TradingConfig(BaseModel):
    weekly_investment: float = Field(100.0, gt=0, le=10000, description="Inversión semanal en EUR (ej: 100.0)")
    lookback_period: int = Field(90, ge=7, le=365, description="Período en días para análisis histórico (ej: 90)")
    min_volume_percentile: float = Field(25.0, ge=0, le=100, description="Percentil mínimo de volumen para considerar un activo (ej: 25.0)")
    rebalance_threshold: float = Field(0.05, ge=0.01, le=0.5, description="Umbral de desviación para rebalanceo (ej: 0.05 para 5%)")

    @field_validator('weekly_investment')
    @classmethod
    def validate_weekly_investment(cls, v: float) -> float:
        if v > 10000: # Límite de seguridad
            raise ValueError("La inversión semanal no debe exceder 10000 EUR. Ajuste si es necesario.")
        return v

class EmailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False, env_prefix='DCA_')
    email: Optional[str] = None
    password: Optional[str] = None # Consider SecretStr for passwords
    notification_email: Optional[str] = None

    @model_validator(mode='after')
    def validate_email_completeness(self) -> 'EmailSettings':
        if any([self.email, self.password, self.notification_email]) and \
           not all([self.email, self.password, self.notification_email]):
            raise ValueError("EmailSettings: 'email', 'password', and 'notification_email' must all be provided if any one is set.")
        return self

# RiskConfig should be independent
# class RiskConfig(BaseModel): # This was defined earlier, ensure it's correct
#    max_drawdown: float = 0.25
#    max_position_size_pct: float = 0.20
#    volatility_threshold: float = 0.50
#    correlation_threshold: float = 0.75
#    min_liquidity_usd: float = 5000000

# TradingConfig was defined earlier, ensure it's correct
# class TradingConfig(BaseModel):
#    weekly_investment: float = 100.0
#    lookback_period: int = 90
#    min_volume_percentile: float = 25
#    rebalance_threshold: float = 0.05

class AssetDetailConfig(BaseModel): # From analysis_config.MAIN_ASSETS structure
    name: str
    category: str

class AnalysisParamsConfig(BaseModel):
    # Defaults from analysis_config.py
    main_assets: Dict[str, AssetDetailConfig] = {
        'BTC': AssetDetailConfig(name='Bitcoin', category='Store of Value'),
        'ETH': AssetDetailConfig(name='Ethereum', category='Smart Contract Platform'),
        'BNB': AssetDetailConfig(name='BNB', category='Exchange Token'),
        'SOL': AssetDetailConfig(name='Solana', category='Smart Contract Platform'),
        'ADA': AssetDetailConfig(name='Cardano', category='Smart Contract Platform')
    }
    asset_categories: Dict[str, List[str]] = {
        'Store of Value': ['BTC'],
        'Smart Contract Platform': ['ETH', 'SOL', 'ADA'],
        'Exchange Token': ['BNB'],
        'DeFi': [], # Assuming empty lists are intentional defaults
        'Gaming': [],
        'Infrastructure': []
    }
    trend_analysis_period: int = 30  # days
    correlation_threshold: float = 0.7 # This was also in original RiskConfig, ensure consistency or decide where it belongs
    volume_ratio_threshold: float = 2.0

class BlockTimeValidationDetail(BaseModel): # From analysis_config.REPORT_CONFIG
    min_time: float
    max_time: float

class ReportParamsConfig(BaseModel):
    # Defaults from analysis_config.py REPORT_CONFIG
    block_sample_size: Dict[str, int] = {
        'ethereum': 100,
        'bsc': 100,
        'solana': 1440
    }
    block_time_validation: Dict[str, BlockTimeValidationDetail] = {
        'ethereum': BlockTimeValidationDetail(min_time=10, max_time=20),
        'bsc': BlockTimeValidationDetail(min_time=2, max_time=5),
        'solana': BlockTimeValidationDetail(min_time=0.4, max_time=1.0)
    }
