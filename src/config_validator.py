import os
import re
from datetime import time
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, field_validator, model_validator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict # Asegúrate que pydantic-settings está instalado
from dotenv import load_dotenv

# Importar modelos Pydantic desde el nuevo archivo src.config_models
from src.config_models import (
    RiskConfig as RiskParams, # Renombrar para evitar colisión si es necesario, o usar directamente
    TradingConfig as TradingParams,
    AllAPIsConfig as APIsConfig, # Renombrar para claridad
    EmailSettings,
    AnalysisParamsConfig,
    ReportParamsConfig,
    # Asegúrate que todas las clases de config_models.py que necesites estén aquí
    # Por ejemplo, AssetDetailConfig, BlockTimeValidationConfig si se usan directamente en SystemConfig
)

# Cargar variables de entorno del archivo .env al inicio del módulo
# Esto permite que las clases BaseSettings las encuentren automáticamente.
load_dotenv()

# --- Main System Configuration Model ---
# Esta clase ahora orquesta todas las demás configuraciones importadas.
class SystemConfig(BaseModel):
    app_name: str = Field("EstrategiasDCA", description="Nombre de la aplicación.")
    version: str = Field("1.0.0", description="Versión de la aplicación.")

    database_url: str = Field(
        default="sqlite:///data/dca_trading.db",
        env="DATABASE_URL", # Permitir que se configure desde .env
        description="URL de conexión a la base de datos. Ejemplo: 'postgresql://user:pass@host:port/db'"
    )

    # Usar las clases importadas de config_models
    # default_factory se usa para instanciar modelos Pydantic anidados
    risk_params: RiskParams = Field(default_factory=RiskParams)
    trading_params: TradingParams = Field(default_factory=TradingParams)
    apis: APIsConfig = Field(default_factory=APIsConfig) # Contendrá todas las configuraciones de API individuales
    email_settings: EmailSettings = Field(default_factory=EmailSettings) # Cargará desde DCA_* env vars
    analysis_params: AnalysisParamsConfig = Field(default_factory=AnalysisParamsConfig)
    report_params: ReportParamsConfig = Field(default_factory=ReportParamsConfig)

    # Parámetros que estaban en la antigua clase Config de src/config.py
    # y algunos de la original SystemConfig de este archivo.
    daily_execution_time: time = Field(
        default=time(16, 0), # Mantener el valor por defecto original
        description="Hora de ejecución diaria (formato HH:MM UTC)."
    )
    run_on_start: bool = Field(
        default=True, # Mantener el valor por defecto original
        description="Ejecutar un ciclo de la estrategia al iniciar el sistema."
    )

    # Portfolio weights: Hacerlo más flexible en el futuro (cargar desde JSON/YAML).
    # Por ahora, un default razonable.
    portfolio_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            'BTCUSDT': 0.5,
            'ETHUSDT': 0.3,
            'ADAUSDT': 0.2
            # Estos eran los defaults en el .env.template, ajusta según los de src/config.py si eran diferentes
        },
        description="Pesos de los activos en el portfolio. Deben sumar 1.0."
    )

    backup_enabled: bool = Field(
        default=True, # Mantener el valor por defecto original
        description="Habilitar backups automáticos del sistema."
    )

    email_notifications_enabled: bool = Field( # Renombrado de 'email_notifications'
        default=True, # Mantener el valor por defecto original
        description="Habilitar el envío de notificaciones por email."
    )

    # --- Validadores ---
    @field_validator('portfolio_weights')
    @classmethod
    def validate_portfolio_weights_sum_and_format(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Valida que los pesos del portfolio sumen 1 y los símbolos sean correctos."""
        if not v:
            raise ValueError("El diccionario de pesos del portfolio no puede estar vacío.")
        
        total_weight = sum(v.values())
        if not (0.999 <= total_weight <= 1.001): # Usar una pequeña tolerancia para floats
            raise ValueError(
                f"Los pesos del portfolio deben sumar aproximadamente 1.0 (suma actual: {total_weight:.4f}). "
                "Ajuste los pesos para que sumen exactamente 100%."
            )
        
        for symbol, weight in v.items():
            if not isinstance(symbol, str) or not symbol.endswith('USDT'): # Ejemplo de validación de formato
                raise ValueError(f"Símbolo inválido: '{symbol}'. Debe ser un string terminado en 'USDT'.")
            if not (0 < weight <= 1):
                 raise ValueError(f"Peso inválido para {symbol}: {weight}. Debe ser > 0 y <= 1.")
        return v

    @model_validator(mode='after')
    def validate_email_notifications_dependencies(self) -> 'SystemConfig':
        """Si las notificaciones por email están habilitadas, asegurar que la configuración de email esté completa."""
        if self.email_notifications_enabled:
            # EmailSettings carga desde variables de entorno (DCA_EMAIL, DCA_EMAIL_PASSWORD, etc.)
            # Solo necesitamos verificar que estén presentes si la funcionalidad está habilitada.
            if not self.email_settings or not all([
                self.email_settings.email,
                self.email_settings.password,
                self.email_settings.notification_email
            ]):
                raise ValueError(
                    "Las notificaciones por email están habilitadas ('email_notifications_enabled' = True), "
                    "pero la configuración de email (DCA_EMAIL, DCA_EMAIL_PASSWORD, DCA_NOTIFICATION_EMAIL en .env) "
                    "está incompleta. Por favor, complete la configuración de email o deshabilite las notificaciones."
                )
        return self

    @classmethod
    def load(cls) -> 'SystemConfig':
        """
        Carga y valida la configuración completa del sistema.
        Las clases anidadas que heredan de BaseSettings (como EmailSettings y las XxxAPIConfig)
        cargarán automáticamente sus valores desde las variables de entorno gracias a Pydantic-Settings.
        """
        try:
            # Aquí se podrían añadir lógicas para cargar configuraciones desde archivos YAML/JSON
            # si se decide no usar solo variables de entorno o valores por defecto para todo.
            # Por ejemplo, para portfolio_weights o main_assets.
            # Para este refactor inicial, nos basamos en defaults y carga de env de BaseSettings.

            instance = cls()

            # Validaciones adicionales post-inicialización si fueran necesarias
            # (aunque Pydantic maneja la mayoría con @field_validator y @model_validator)

            print("SystemConfig loaded successfully using internal models and .env variables.")
            return instance
        except Exception as e:
            # En una aplicación real, usar un logger configurado.
            print(f"CRITICAL: Error al cargar o validar la configuración del sistema: {e}")
            # Se podría querer propagar la excepción para detener la aplicación si la config es inválida.
            raise

# --- Punto de entrada para probar la carga de configuración ---
if __name__ == '__main__':
    print("Intentando cargar la configuración del sistema (SystemConfig.load())...")
    # Asegúrate de tener un archivo .env en la raíz del proyecto con las variables necesarias,
    # especialmente las requeridas por XxxAPIConfig (ej: CMC_API_KEY) y EmailSettings.
    try:
        app_config = SystemConfig.load()
        print("\n¡Configuración cargada exitosamente!")
        print(f"Nombre de la App: {app_config.app_name}, Versión: {app_config.version}")
        print(f"URL Base de Datos: {app_config.database_url}")

        # Probar acceso a configuraciones anidadas
        print(f"\nParámetros de Riesgo: Drawdown Máx. = {app_config.risk_params.max_drawdown * 100}%")
        print(f"Parámetros de Trading: Inversión Semanal = {app_config.trading_params.weekly_investment} EUR")
        
        # Probar API Config (Binance como ejemplo)
        if app_config.apis.binance.enabled:
            print(f"\nAPI de Binance HABILITADA.")
            print(f"  URL Base Binance: {app_config.apis.binance.base_url}")
            if app_config.apis.binance.api_key:
                print(f"  Clave API Binance (primeros 5 chars): {app_config.apis.binance.api_key[:5]}...")
            else:
                print("  Clave API Binance: No configurada (pero la API está habilitada).")
        else:
            print("\nAPI de Binance DESHABILITADA.")

        # Probar Email Settings
        if app_config.email_notifications_enabled:
            print("\nNotificaciones por Email HABILITADAS.")
            print(f"  Email de envío: {app_config.email_settings.email or 'No configurado'}")
            print(f"  Email de notificación: {app_config.email_settings.notification_email or 'No configurado'}")
        else:
            print("\nNotificaciones por Email DESHABILITADAS.")

        print(f"\nPesos del Portfolio: {app_config.portfolio_weights}")
        print(f"Periodo Análisis de Tendencia: {app_config.analysis_params.trend_analysis_period} días")

    except ValueError as ve:
        print(f"\nError de Validación al cargar la configuración: {ve}")
    except Exception as ex:
        print(f"\nError Inesperado al cargar la configuración: {ex}")