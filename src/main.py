from market_analysis import MarketAnalysis
from datetime import datetime

def main():
    # Crear instancia de MarketAnalysis
    analysis = MarketAnalysis()
    
    # Usar los datos de prueba de test_market_analysis.py
    detailed_analysis = {
        "BTC": {
            "score_tendencia": 1.5,
            "metricas": {
                "precio_actual": 93801.84,
                "precio_max": 97268.65,
                "precio_min": 92500.90,
                "cambio_24h": -2.49
            },
            "rsi": 35,
            "bandas_bollinger": {"posicion": 0.2},
            "macd": {"cruce": "Alcista"},
            "oportunidad_compra": {
                "señales": [
                    {"tipo": "RSI", "descripcion": "Sobreventa", "contribucion": 0.8},
                    {"tipo": "BB", "descripcion": "Cerca de la banda inferior", "contribucion": 0.5},
                    {"tipo": "MACD", "descripcion": "Cruce alcista", "contribucion": 0.7}
                ]
            },
            "analisis_tendencia": [
                "Soporte en zona de acumulación",
                "Volumen creciente en velas alcistas"
            ]
        },
        "ETH": {
            "score_tendencia": -0.5,
            "metricas": {
                "precio_actual": 3268.31,
                "precio_max": 3500,
                "precio_min": 3200,
                "cambio_24h": -1.8
            },
            "rsi": 65,
            "bandas_bollinger": {"posicion": 0.8},
            "macd": {"cruce": "Bajista"},
            "oportunidad_compra": {"señales": []},
            "analisis_tendencia": [
                "Resistencia en máximos anteriores",
                "Divergencia bajista en RSI"
            ]
        },
        "BNB": {
            "score_tendencia": 0.8,
            "metricas": {
                "precio_actual": 687.42,
                "precio_max": 700,
                "precio_min": 680,
                "cambio_24h": 0.5
            },
            "rsi": 50,
            "bandas_bollinger": {"posicion": 0.5},
            "macd": {"cruce": "Neutral"},
            "oportunidad_compra": {
                "señales": [
                    {"tipo": "Cruce MA", "descripcion": "Posible cruce alcista", "contribucion": 0.3}
                ]
            },
            "analisis_tendencia": [
                "Consolidación en rango estrecho",
                "Acumulación gradual"
            ]
        },
        "XRP": {
            "score_tendencia": 1.2,
            "metricas": {
                "precio_actual": 2.2979,
                "precio_max": 2.35,
                "precio_min": 2.25,
                "cambio_24h": 2.1
            },
            "rsi": 40,
            "bandas_bollinger": {"posicion": 0.3},
            "macd": {"cruce": "Alcista"},
            "oportunidad_compra": {
                "señales": [
                    {"tipo": "Tendencia", "descripcion": "Momentum alcista", "contribucion": 0.6}
                ]
            },
            "analisis_tendencia": [
                "Ruptura de resistencia clave",
                "Aumento de volumen institucional"
            ]
        },
        "ADA": {
            "score_tendencia": -1.2,
            "metricas": {
                "precio_actual": 0.9104,
                "precio_max": 0.95,
                "precio_min": 0.90,
                "cambio_24h": -3.2
            },
            "rsi": 28,
            "bandas_bollinger": {"posicion": 0.1},
            "macd": {"cruce": "Bajista"},
            "oportunidad_compra": {
                "señales": [
                    {"tipo": "RSI", "descripcion": "Sobreventa extrema", "contribucion": 1.0},
                    {"tipo": "BB", "descripcion": "Soporte en banda inferior", "contribucion": 0.8}
                ]
            },
            "analisis_tendencia": [
                "Test de soporte histórico",
                "Divergencia alcista en MACD"
            ]
        },
        "DOGE": {
            "score_tendencia": 0.5,
            "metricas": {
                "precio_actual": 0.3335,
                "precio_max": 0.35,
                "precio_min": 0.32,
                "cambio_24h": 1.2
            },
            "rsi": 72,
            "bandas_bollinger": {"posicion": 0.9},
            "macd": {"cruce": "Alcista"},
            "oportunidad_compra": {"señales": []},
            "analisis_tendencia": [
                "Resistencia en zona de distribución",
                "Volumen decreciente en máximos"
            ]
        },
        "SOL": {
            "score_tendencia": 0.2,
            "metricas": {
                "precio_actual": 193.80,
                "precio_max": 200,
                "precio_min": 190,
                "cambio_24h": 0.8
            },
            "rsi": 55,
            "bandas_bollinger": {"posicion": 0.6},
            "macd": {"cruce": "Bajista"},
            "oportunidad_compra": {
                "señales": [
                    {"tipo": "Volumen", "descripcion": "Incremento significativo", "contribucion": 0.4}
                ]
            },
            "analisis_tendencia": [
                "Consolidación en tendencia alcista",
                "Soporte en media móvil de 50 días"
            ]
        }
    }
    
    # Generar oportunidades y alertas de ejemplo
    opportunities = [
        {
            "activo": "BTC",
            "motivo": "Confluencia Técnica",
            "detalles": "RSI en sobreventa, precio en soporte y MACD alcista",
            "score": 2.25
        },
        {
            "activo": "ADA",
            "motivo": "RSI Bajo",
            "detalles": "RSI en zona de sobreventa extrema (28)",
            "score": 1.8
        },
        {
            "activo": "XRP",
            "motivo": "Tendencia",
            "detalles": "Momentum alcista con soporte en MA50",
            "score": 1.5
        }
    ]
    
    alerts = [
        {
            "tipo": "Precio",
            "activo": "BTC",
            "mensaje": "Caída significativa de -6.5% en las últimas 24 horas",
            "severidad": "Alta"
        },
        {
            "tipo": "RSI",
            "activo": "ADA",
            "mensaje": "RSI en zona de sobreventa extrema (28)",
            "severidad": "Media"
        },
        {
            "tipo": "Volumen",
            "activo": "SOL",
            "mensaje": "Incremento notable del volumen (+50%)",
            "severidad": "Media"
        }
    ]
    
    # Datos de ejemplo para métricas on-chain
    onchain_metrics = {
        "Ethereum": {
            "TPS": "15.8",
            "Gas (gwei)": "25",
            "TVL": "$45.2B",
            "Validators": "945,323"
        },
        "Binance Smart Chain": {
            "TPS": "35.2",
            "Gas (gwei)": "5",
            "TVL": "$8.1B",
            "Validators": "21"
        },
        "Solana": {
            "TPS": "2,457",
            "Fee": "0.00025 SOL",
            "TVL": "$1.2B",
            "Validators": "1,875"
        }
    }
    
    # Recomendación de ejemplo
    recommendation = """
    Basado en el análisis actual, se recomienda:
    
    1. **Bitcoin (BTC)**: Considerar compras parciales aprovechando la zona de soporte actual.
    2. **Cardano (ADA)**: Monitorear para posible entrada si se confirma la divergencia alcista.
    3. **XRP**: Esperar confirmación de la ruptura antes de tomar posiciones.
    
    Mantener una gestión de riesgo conservadora dado el contexto macro actual.
    """
    
    # Generar el informe
    analysis.generate_report(
        market_trend=None,  # No usado en esta versión
        onchain_metrics=onchain_metrics,
        opportunities=opportunities,
        alerts=alerts,
        recommendation=recommendation,
        last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        detailed_analysis=detailed_analysis,
        page_size=3  # 3 activos por página para probar la paginación
    )

if __name__ == "__main__":
    main() 