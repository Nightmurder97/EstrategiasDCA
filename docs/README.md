# Estrategia DCA (Dollar Cost Averaging) para Criptomonedas

Este proyecto implementa una estrategia de inversión DCA (Dollar Cost Averaging) automatizada para criptomonedas, con ajustes dinámicos basados en análisis técnico y movimientos de precio.

## Características Principales

- **Inversión Periódica**: Inversión semanal automática distribuida entre múltiples criptomonedas
- **Análisis Técnico**: Evaluación de tendencias usando medias móviles (MA7, MA25, MA99)
- **Ajuste Dinámico**: Modificación de pesos de inversión basada en:
  - Caídas de precio
  - Tendencias técnicas
  - Volatilidad
  - Volumen de trading
- **Copias de Seguridad**: Respaldo automático del historial del portafolio
- **Gestión de Riesgos**: Sistema de control de riesgos con parámetros configurables
- **Notificaciones por Email**: Sistema de alertas y reportes automáticos

## Portfolio Actual (574.09€ total)

### Activos Principales (>10%)
- XRPUSDT (Ripple): 44.3% (254.50€)
- ADAUSDT (Cardano): 13.3% (76.66€)
- DOGEUSDT (Dogecoin): 8.8% (50.51€)

### Activos Secundarios (5-10%)
- PHAUSDT (Phala): 6.6% (37.62€)
- BTCUSDT (Bitcoin): 4.5% (26.03€)
- USDCUSDT (USD Coin): 3.6% (20.59€)
- PEPEUSDT (Pepe): 3.4% (19.52€)

### Activos de Menor Peso (<5%)
- DOTUSDT (Polkadot): 2.8% (15.96€)
- HBARUSDT (Hedera): 2.3% (13.42€)
- BABYDOGEUSDT: 2.0% (11.44€)
- VETUSDT (VeChain): 1.8% (10.42€)
- AGLDUSDT (Adventure Gold): 1.4% (7.81€)
- RSRUSDT (Reserve Rights): 1.0% (5.53€)
- TRXUSDT (TRON): 0.9% (5.40€)
- GALAUSDT (Gala): 0.8% (4.53€)
- BONKUSDT (Bonk): 0.7% (4.02€)
- SUSDT (SiennaToken): 0.7% (3.87€)
- NEIROUSDT (Neiro): 0.6% (3.64€)
- BIOUSDT (BioPassport): 0.4% (2.48€)
- USDTUSDT (Tether): 0.01% (0.05€)
- FLOKIUSDT (Floki): 0.01% (0.03€)

## Estructura del Programa

### Archivos Principales
- `dca_scheduler.py`: Programa principal que gestiona la ejecución periódica
- `dca_live_trader.py`: Implementación de la estrategia DCA en tiempo real
- `market_analysis.py`: Análisis de mercado y generación de reportes
- `risk_manager.py`: Sistema de gestión de riesgos
- `portfolio_history.json`: Almacena el historial del portafolio y transacciones
- `session_summary.json`: Resumen de la última sesión y estado actual
- `simulation_results.xlsx`: Resultados de simulaciones históricas

### Archivos de Configuración
- `config.json`: Configuración general del programa
- `.env`: Variables de entorno (API keys, configuraciones privadas)

## Parámetros de Riesgo

### RiskParameters
- `max_drawdown`: 25% máximo drawdown permitido
- `max_position_size`: 30% tamaño máximo por posición
- `volatility_threshold`: 50% volatilidad máxima anualizada
- `correlation_threshold`: 75% correlación máxima entre activos
- `min_liquidity`: 1,000,000 USD volumen mínimo diario

### LiveTradingParameters
- `weekly_investment`: 100.0€ inversión semanal
- `lookback_period`: 90 días para métricas
- `min_volume_percentile`: 25% percentil mínimo de volumen
- `max_position_size`: 30% tamaño máximo de posición
- `rebalance_threshold`: 5% umbral de rebalanceo

## Funcionamiento Detallado

### 1. Análisis de Mercado
- Obtiene datos históricos de Binance (90 días por defecto)
- Calcula métricas técnicas:
  - Cambios de precio diarios
  - Medias móviles
  - Volatilidad
  - Ratio de Sharpe
  - Ranking de volumen

### 2. Gestión de Riesgos
- Monitoreo de volatilidad
- Control de correlaciones entre activos
- Verificación de liquidez
- Límites de exposición por activo

### 3. Gestión del Portafolio
- Monitoreo diario del rendimiento
- Rebalanceo semanal (martes 16:00)
- Límites de exposición por activo
- Tracking de rendimiento

### 4. Sistema de Notificaciones
- Alertas por email de ejecuciones
- Reportes de rendimiento
- Notificaciones de riesgo
- Resúmenes de operaciones

## Requisitos y Dependencias

```
pandas
numpy
matplotlib
requests
tqdm
seaborn
schedule
python-dotenv
```

## Instalación

1. Crear entorno virtual:
```bash
python -m venv trading-env
```

2. Activar entorno virtual:
```bash
# En Windows:
trading-env\Scripts\activate

# En macOS/Linux:
source trading-env/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
# Crear archivo .env
CMC_API_KEY=tu_api_key_aqui
DCA_EMAIL=tu_email
DCA_EMAIL_PASSWORD=tu_password
DCA_NOTIFICATION_EMAIL=email_destino
```

## Uso del Programa

### Comandos Principales
```bash
# Ejecutar el scheduler
python src/dca_scheduler.py

# Ver análisis de mercado
python src/market_analysis.py

# Ejecutar trader manualmente
python src/dca_live_trader.py
```

### Horarios de Operación

#### Horarios Críticos
1. 16:00: Análisis principal y ejecución (martes)
2. 18:00: Análisis diario y monitoreo
3. 21:00: Revisión de cierre (opcional)

### Monitoreo
1. Revisar reportes en `reports/`
2. Verificar logs en `dca_trader.log`
3. Consultar histórico en `portfolio_history.json`

## Notas de Seguridad

1. El programa no realiza operaciones automáticas en exchange
2. Todas las operaciones requieren confirmación manual
3. Los datos se obtienen de la API pública de Binance
4. API keys almacenadas en variables de entorno
5. Copias de seguridad automáticas diarias
6. Sistema de gestión de riesgos activo 