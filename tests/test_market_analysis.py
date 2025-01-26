import unittest
from unittest.mock import patch, MagicMock
from market_analysis import MarketAnalysis
from datetime import datetime
import os

class TestAlertsAndOpportunities(unittest.TestCase):
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.analysis = MarketAnalysis()
        
        # Datos de prueba para análisis detallado
        self.detailed_analysis = {
            "BTC": {
                "score_tendencia": 1.5,
                "metricas": {
                    "precio_actual": 93801.84,  # Precio actual de Binance
                    "precio_max": 97268.65,     # Máximo 24h según la imagen
                    "precio_min": 92500.90      # Mínimo 24h según la imagen
                },
                "rsi": 35,  # Ligeramente sobrevendido
                "bandas_bollinger": {"posicion": 0.2},  # Cerca de la banda inferior
                "macd": {"cruce": "Alcista"},
                "oportunidad_compra": {
                    "señales": [
                        {"tipo": "RSI", "descripcion": "Sobreventa", "contribucion": 0.8},
                        {"tipo": "BB", "descripcion": "Cerca de la banda inferior", "contribucion": 0.5},
                        {"tipo": "MACD", "descripcion": "Cruce alcista", "contribucion": 0.7}
                    ]
                }
            },
            "ETH": {
                "score_tendencia": -0.5,  # Tendencia ligeramente bajista
                "metricas": {
                    "precio_actual": 3268.31,   # Precio actual de Binance
                    "precio_max": 3500,
                    "precio_min": 3200
                },
                "rsi": 65,  # Ligeramente sobrecomprado
                "bandas_bollinger": {"posicion": 0.8},  # Cerca de la banda superior
                "macd": {"cruce": "Bajista"},
                "oportunidad_compra": {
                    "señales": []  # Sin oportunidades claras
                }
            },
            "BNB": {
                "score_tendencia": 0.8,  # Tendencia neutral/ligeramente alcista
                "metricas": {
                    "precio_actual": 687.42,    # Precio actual de Binance
                    "precio_max": 700,
                    "precio_min": 680
                },
                "rsi": 50,  # Neutral
                "bandas_bollinger": {"posicion": 0.5},  # En la media móvil
                "macd": {"cruce": "Neutral"},
                "oportunidad_compra": {
                    "señales": [
                        {"tipo": "Cruce MA", "descripcion": "Posible cruce alcista", "contribucion": 0.3}
                    ]
                }
            },
            "XRP": {
                "score_tendencia": 1.2,
                "metricas": {
                    "precio_actual": 2.2979,    # Precio actual de Binance
                    "precio_max": 2.35,
                    "precio_min": 2.25
                },
                "rsi": 40,  # Neutral/Ligeramente sobrevendido
                "bandas_bollinger": {"posicion": 0.3},  # Por debajo de la media
                "macd": {"cruce": "Alcista"},
                "oportunidad_compra": {
                    "señales": [
                        {"tipo": "Tendencia", "descripcion": "Momentum alcista", "contribucion": 0.6}
                    ]
                }
            },
            "ADA": {
                "score_tendencia": -1.2,  # Tendencia bajista
                "metricas": {
                    "precio_actual": 0.9104,    # Precio actual de Binance
                    "precio_max": 0.95,
                    "precio_min": 0.90
                },
                "rsi": 28,  # Sobreventa
                "bandas_bollinger": {"posicion": 0.1},  # Muy cerca de la banda inferior
                "macd": {"cruce": "Bajista"},
                "oportunidad_compra": {
                    "señales": [
                        {"tipo": "RSI", "descripcion": "Sobreventa extrema", "contribucion": 1.0},
                        {"tipo": "BB", "descripcion": "Soporte en banda inferior", "contribucion": 0.8}
                    ]
                }
            },
            "DOGE": {
                "score_tendencia": 0.5,
                "metricas": {
                    "precio_actual": 0.33348,   # Precio actual de Binance
                    "precio_max": 0.35,
                    "precio_min": 0.32
                },
                "rsi": 72,  # Sobrecompra
                "bandas_bollinger": {"posicion": 0.9},  # Muy cerca de la banda superior
                "macd": {"cruce": "Alcista"},
                "oportunidad_compra": {
                    "señales": []  # No hay oportunidades por sobrecompra
                }
            },
            "SOL": {
                "score_tendencia": 0.2,  # Tendencia neutral
                "metricas": {
                    "precio_actual": 193.80,    # Precio actual de Binance
                    "precio_max": 200,
                    "precio_min": 190
                },
                "rsi": 55,  # Neutral
                "bandas_bollinger": {"posicion": 0.6},  # Ligeramente por encima de la media
                "macd": {"cruce": "Bajista"},
                "oportunidad_compra": {
                    "señales": [
                        {"tipo": "Volumen", "descripcion": "Incremento significativo", "contribucion": 0.4}
                    ]
                }
            }
        }
        
        # Datos de prueba para movimientos significativos
        self.significant_moves = {
            "significant_moves": [
                {"symbol": "BTC", "price_change": -6.5, "volume_change": 15.0},   # Movimiento bajista con volumen alto
                {"symbol": "ETH", "price_change": 2.8, "volume_change": -5.0},    # Movimiento alcista con volumen bajo
                {"symbol": "BNB", "price_change": 0.5, "volume_change": 3.0},     # Movimiento lateral con volumen moderado
                {"symbol": "XRP", "price_change": -1.2, "volume_change": 8.0},    # Bajista moderado con volumen alto
                {"symbol": "ADA", "price_change": 7.2, "volume_change": 12.0},    # Movimiento alcista con volumen alto
                {"symbol": "DOGE", "price_change": -0.8, "volume_change": -2.0},  # Movimiento bajista con volumen bajo
                {"symbol": "SOL", "price_change": 5.5, "volume_change": 6.0}      # Alcista moderado con volumen moderado
            ]
        }
    
    def test_generate_alerts_basic(self):
        """Prueba la generación básica de alertas."""
        alerts = self.analysis._generate_alerts(self.detailed_analysis, self.significant_moves)
        self.assertTrue(len(alerts) > 0)
        self.assertIn('Precio', [alert['tipo'] for alert in alerts])
        self.assertIn('Volumen', [alert['tipo'] for alert in alerts])
    
    def test_generate_alerts_technical(self):
        """Prueba la generación de alertas técnicas."""
        alerts = self.analysis._generate_alerts(self.detailed_analysis, self.significant_moves)
        alert_types = [alert['tipo'] for alert in alerts]
        self.assertTrue(set(['RSI', 'Bollinger', 'MACD']).intersection(set(alert_types)))
    
    def test_generate_alerts_severity(self):
        """Prueba la severidad de las alertas."""
        alerts = self.analysis._generate_alerts(self.detailed_analysis, self.significant_moves)
        severities = [alert['severidad'] for alert in alerts]
        self.assertTrue(set(['Alta', 'Media']).intersection(set(severities)))
        
        # Verificar orden por severidad
        high_severity_indices = [i for i, alert in enumerate(alerts) if alert['severidad'] == 'Alta']
        if high_severity_indices:
            self.assertTrue(all(idx < len(alerts)/2 for idx in high_severity_indices))
    
    def test_identify_opportunities_basic(self):
        """Prueba la identificación básica de oportunidades."""
        opportunities = self.analysis._identify_opportunities(self.detailed_analysis)
        self.assertTrue(len(opportunities) > 0)
        
        # Verificar que se identifican oportunidades por tendencia y señales técnicas
        motivos = [opp['motivo'] for opp in opportunities]
        self.assertTrue(any('RSI' in motivo for motivo in motivos))  # ADA tiene RSI de 28
        self.assertTrue(any('Bollinger' in motivo for motivo in motivos))  # BTC y ADA cerca de banda inferior
        self.assertTrue(any('MACD' in motivo for motivo in motivos))  # BTC y BNB tienen señales MACD
        self.assertTrue(any('Tendencia' in motivo for motivo in motivos))  # XRP tiene momentum alcista

        # Verificar que las oportunidades tienen los campos requeridos
        for opp in opportunities:
            self.assertIn('activo', opp)
            self.assertIn('motivo', opp)
            self.assertIn('detalles', opp)
            self.assertIn('score', opp)
            self.assertTrue(isinstance(opp['score'], (int, float)))
            self.assertTrue(opp['score'] >= 0)
            
        # Verificar que ADA está en las oportunidades por RSI bajo
        ada_opportunities = [opp for opp in opportunities if opp['activo'] == 'ADA']
        self.assertTrue(len(ada_opportunities) > 0)
        self.assertTrue(any('RSI' in opp['motivo'] for opp in ada_opportunities))
        
        # Verificar que BTC está en las oportunidades por múltiples señales
        btc_opportunities = [opp for opp in opportunities if opp['activo'] == 'BTC']
        self.assertTrue(len(btc_opportunities) > 0)
        btc_signals = sum(1 for opp in btc_opportunities if any(signal in opp['motivo'] for signal in ['RSI', 'BB', 'MACD']))
        self.assertTrue(btc_signals >= 2)  # Al menos 2 señales diferentes
    
    def test_identify_opportunities_scoring(self):
        """Prueba el sistema de scoring de oportunidades."""
        opportunities = self.analysis._identify_opportunities(self.detailed_analysis)
        scores = [opp['score'] for opp in opportunities]
        self.assertTrue(all(isinstance(score, (int, float)) for score in scores))
        self.assertTrue(all(score >= 0 for score in scores))
        
        # Verificar orden por score
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_identify_opportunities_technical(self):
        """Prueba la identificación de oportunidades técnicas."""
        opportunities = self.analysis._identify_opportunities(self.detailed_analysis)
        opportunity_types = [opp['motivo'] for opp in opportunities]
        self.assertTrue(
            set(['RSI Bajo', 'Bollinger', 'Señal Técnica']).intersection(set(opportunity_types))
        )
    
    def test_error_handling(self):
        """Prueba el manejo de errores."""
        # Prueba con datos inválidos
        invalid_analysis = {"BTC": None}
        alerts = self.analysis._generate_alerts(invalid_analysis, None)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['tipo'], 'Error')
        
        opportunities = self.analysis._identify_opportunities(invalid_analysis)
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0]['motivo'], 'Error')

    def test_identify_opportunities_edge_cases(self):
        """Prueba casos límite en la identificación de oportunidades."""
        # Caso 1: RSI extremadamente bajo
        edge_analysis = {
            "EXTREME_RSI": {
                "score_tendencia": 0,
                "metricas": {
                    "precio_actual": 100,
                    "precio_max": 120,
                    "precio_min": 90
                },
                "rsi": 15,  # RSI extremadamente bajo
                "bandas_bollinger": {"posicion": 0.5},
                "macd": {"cruce": "Neutral"},
                "oportunidad_compra": {"señales": []}
            }
        }
        opportunities = self.analysis._identify_opportunities(edge_analysis)
        self.assertTrue(any(opp['activo'] == 'EXTREME_RSI' and 'RSI' in opp['motivo'] for opp in opportunities))
        self.assertTrue(any(opp['score'] > 2 for opp in opportunities))  # Score alto por RSI muy bajo

    def test_identify_opportunities_no_signals(self):
        """Prueba el caso donde no hay señales de oportunidad."""
        no_signals_analysis = {
            "NEUTRAL": {
                "score_tendencia": 0,
                "metricas": {
                    "precio_actual": 100,
                    "precio_max": 120,
                    "precio_min": 90
                },
                "rsi": 50,  # RSI neutral
                "bandas_bollinger": {"posicion": 0.5},  # BB neutral
                "macd": {"cruce": "Neutral"},
                "oportunidad_compra": {"señales": []}
            }
        }
        opportunities = self.analysis._identify_opportunities(no_signals_analysis)
        self.assertEqual(len([opp for opp in opportunities if opp['activo'] == 'NEUTRAL']), 0)

    def test_identify_opportunities_multiple_signals(self):
        """Prueba el caso donde hay múltiples señales para un mismo activo."""
        multiple_signals_analysis = {
            "MULTI_SIGNAL": {
                "score_tendencia": 2.5,
                "metricas": {
                    "precio_actual": 90,
                    "precio_max": 120,
                    "precio_min": 85
                },
                "rsi": 25,  # RSI bajo
                "bandas_bollinger": {"posicion": 0.05},  # Cerca de banda inferior
                "macd": {"cruce": "Alcista"},
                "oportunidad_compra": {
                    "señales": [
                        {"tipo": "RSI", "descripcion": "Sobreventa", "contribucion": 1.0},
                        {"tipo": "BB", "descripcion": "Soporte", "contribucion": 0.8},
                        {"tipo": "MACD", "descripcion": "Cruce alcista", "contribucion": 0.7},
                        {"tipo": "Tendencia", "descripcion": "Momentum", "contribucion": 0.9}
                    ]
                }
            }
        }
        opportunities = self.analysis._identify_opportunities(multiple_signals_analysis)
        multi_signals = [opp for opp in opportunities if opp['activo'] == 'MULTI_SIGNAL']
        self.assertTrue(len(multi_signals) >= 3)  # Al menos 3 señales diferentes
        self.assertTrue(any(opp['score'] > 2.5 for opp in multi_signals))  # Al menos una señal con score alto

    def test_generate_alerts_edge_cases(self):
        """Prueba casos límite en la generación de alertas."""
        edge_moves = {
            "significant_moves": [
                {"symbol": "EXTREME_UP", "price_change": 15.0, "volume_change": 50.0},    # Cambios extremos positivos
                {"symbol": "EXTREME_DOWN", "price_change": -12.0, "volume_change": -30.0}, # Cambios extremos negativos
                {"symbol": "NO_CHANGE", "price_change": 0.0, "volume_change": 0.0}        # Sin cambios
            ]
        }
        edge_analysis = {
            "EXTREME_UP": {
                "rsi": 85,  # RSI extremadamente alto
                "bandas_bollinger": {"posicion": 0.98},  # Muy cerca de banda superior
                "macd": {"cruce": "Alcista"}
            },
            "EXTREME_DOWN": {
                "rsi": 15,  # RSI extremadamente bajo
                "bandas_bollinger": {"posicion": 0.02},  # Muy cerca de banda inferior
                "macd": {"cruce": "Bajista"}
            },
            "NO_CHANGE": {
                "rsi": 50,
                "bandas_bollinger": {"posicion": 0.5},
                "macd": {"cruce": "Neutral"}
            }
        }
        
        alerts = self.analysis._generate_alerts(edge_analysis, edge_moves)
        
        # Verificar alertas de precio extremas
        price_alerts = [alert for alert in alerts if alert['tipo'] == 'Precio']
        self.assertTrue(any(alert['severidad'] == 'Alta' for alert in price_alerts))
        
        # Verificar alertas técnicas extremas
        self.assertTrue(any(alert['tipo'] == 'RSI' and alert['severidad'] == 'Alta' for alert in alerts))
        self.assertTrue(any(alert['tipo'] == 'Bollinger' and alert['severidad'] == 'Alta' for alert in alerts))
        
        # Verificar que no hay alertas para el activo sin cambios
        self.assertFalse(any(alert['activo'] == 'NO_CHANGE' for alert in alerts))

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        """Configuración inicial para las pruebas de API."""
        self.analysis = MarketAnalysis()
        
        # Configurar API keys de prueba
        os.environ["ETHERSCAN_API_KEY"] = "test_key"
        os.environ["BSCSCAN_API_KEY"] = "test_key"
        os.environ["SOLSCAN_API_KEY"] = "test_key"
    
    @patch("requests.get")
    def test_fetch_from_coingecko_success(self, mock_get):
        """Prueba una respuesta exitosa de CoinGecko."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"prices": [[1678886400000, 50000]]}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_coingecko("coins/bitcoin/market_chart")
        self.assertEqual(data, {"prices": [[1678886400000, 50000]]})

    @patch("requests.get")
    def test_fetch_from_coingecko_empty(self, mock_get):
        """Prueba una respuesta vacía de CoinGecko."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"prices": []}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_coingecko("coins/bitcoin/market_chart")
        self.assertEqual(data, {"prices": []})

    @patch("requests.get")
    def test_fetch_from_coingecko_error(self, mock_get):
        """Prueba un error en la respuesta de CoinGecko."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not Found")
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.analysis._fetch_from_coingecko("coins/bitcoin/market_chart")

    @patch("requests.get")
    def test_fetch_from_defillama_success(self, mock_get):
        """Prueba una respuesta exitosa de DefiLlama."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tvl": [{"date": 1678886400, "totalLiquidityUSD": 1000000}]}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_defillama("protocols/ethereum")
        self.assertEqual(data, {"tvl": [{"date": 1678886400, "totalLiquidityUSD": 1000000}]})

    @patch("requests.get")
    def test_fetch_from_defillama_empty(self, mock_get):
        """Prueba una respuesta vacía de DefiLlama."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tvl": []}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_defillama("protocols/ethereum")
        self.assertEqual(data, {"tvl": []})

    @patch("requests.get")
    def test_fetch_from_defillama_error(self, mock_get):
        """Prueba un error en la respuesta de DefiLlama."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.analysis._fetch_from_defillama("protocols/ethereum")

    @patch("requests.get")
    def test_fetch_from_etherscan_success(self, mock_get):
        """Prueba una respuesta exitosa de Etherscan."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "1", "result": "100"}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_etherscan("block", {"module": "block", "action": "getblocknobytime"})
        self.assertEqual(data, "100")

    @patch("requests.get")
    def test_fetch_from_etherscan_empty(self, mock_get):
        """Prueba una respuesta vacía de Etherscan."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "0", "result": "", "message": "No data found"}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_etherscan("block", {"module": "block", "action": "getblocknobytime"})
        self.assertEqual(data, {})

    @patch("requests.get")
    def test_fetch_from_etherscan_error(self, mock_get):
        """Prueba un error en la respuesta de Etherscan."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Internal Server Error")
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_etherscan("block", {"module": "block", "action": "getblocknobytime"})
        self.assertEqual(data, {})

    @patch("requests.get")
    def test_fetch_from_bscscan_success(self, mock_get):
        """Prueba una respuesta exitosa de BSCScan."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "1", "result": "200"}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_bscscan("block", {"module": "block", "action": "getblocknobytime"})
        self.assertEqual(data, "200")

    @patch("requests.get")
    def test_fetch_from_bscscan_empty(self, mock_get):
        """Prueba una respuesta vacía de BSCScan."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "0", "result": "", "message": "No data found"}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_bscscan("block", {"module": "block", "action": "getblocknobytime"})
        self.assertEqual(data, {})

    @patch("requests.get")
    def test_fetch_from_bscscan_error(self, mock_get):
        """Prueba un error en la respuesta de BSCScan."""
        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.raise_for_status.side_effect = Exception("Bad Gateway")
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_bscscan("block", {"module": "block", "action": "getblocknobytime"})
        self.assertEqual(data, {})

    @patch("requests.get")
    def test_fetch_from_solscan_success(self, mock_get):
        """Prueba una respuesta exitosa de Solscan."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"blockTime": 1678886400, "txNum": 100}]}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_solscan("blocks/last", {"limit": 1})
        self.assertEqual(data, {"data": [{"blockTime": 1678886400, "txNum": 100}]})

    @patch("requests.get")
    def test_fetch_from_solscan_empty(self, mock_get):
        """Prueba una respuesta vacía de Solscan."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_solscan("blocks/last", {"limit": 1})
        self.assertEqual(data, {"data": []})

    @patch("requests.get")
    def test_fetch_from_solscan_error(self, mock_get):
        """Prueba un error en la respuesta de Solscan."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = Exception("Forbidden")
        mock_get.return_value = mock_response

        data = self.analysis._fetch_from_solscan("blocks/last", {"limit": 1})
        self.assertEqual(data, {})

if __name__ == "__main__":
    unittest.main() 