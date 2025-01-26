import logging
from typing import Dict, Optional
from dataclasses import dataclass
import numpy as np
from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.params = config.risk_params
        self.position_limits: Dict[str, float] = {}
        self.asset_correlations: Dict[str, Dict[str, float]] = {}
        
    def calculate_position_size(self, symbol: str, price: float, volatility: float, 
                              portfolio_value: float) -> float:
        """Calcula el tamaño óptimo de la posición basado en la volatilidad y el valor del portfolio"""
        try:
            # Ajustar tamaño según volatilidad
            vol_adjustment = max(0, 1 - (volatility / self.params.volatility_threshold))
            base_size = portfolio_value * self.params.max_position_size
            adjusted_size = base_size * vol_adjustment
            
            # Aplicar límites
            max_allowed = portfolio_value * self.params.max_position_size
            position_size = min(adjusted_size, max_allowed)
            
            return position_size
        except Exception as e:
            logger.error(f"Error calculando tamaño de posición para {symbol}: {str(e)}")
            return 0.0
    
    def check_portfolio_risk(self, positions: Dict[str, float], 
                           current_prices: Dict[str, float],
                           historical_prices: Dict[str, np.ndarray]) -> Dict[str, bool]:
        """Evalúa los riesgos del portfolio actual"""
        risk_flags = {}
        try:
            portfolio_value = sum(pos * current_prices.get(sym, 0) 
                                for sym, pos in positions.items())
            
            for symbol, position in positions.items():
                # Verificar tamaño de posición
                position_value = position * current_prices.get(symbol, 0)
                position_weight = position_value / portfolio_value if portfolio_value > 0 else 0
                
                risk_flags[symbol] = {
                    'size_exceeded': position_weight > self.params.max_position_size,
                    'high_volatility': self._check_volatility(historical_prices.get(symbol, [])),
                    'correlation_risk': self._check_correlation(symbol, historical_prices),
                    'liquidity_risk': self._check_liquidity(symbol, current_prices.get(symbol, 0))
                }
                
            return risk_flags
        except Exception as e:
            logger.error(f"Error evaluando riesgos del portfolio: {str(e)}")
            return {}
    
    def _check_volatility(self, prices: np.ndarray) -> bool:
        """Verifica si la volatilidad excede el umbral"""
        try:
            if len(prices) < 2:
                return False
            returns = np.diff(np.log(prices))
            volatility = np.std(returns) * np.sqrt(252)  # Anualizada
            return volatility > self.params.volatility_threshold
        except Exception as e:
            logger.error(f"Error calculando volatilidad: {str(e)}")
            return False
    
    def _check_correlation(self, symbol: str, historical_prices: Dict[str, np.ndarray]) -> bool:
        """Verifica correlaciones peligrosas con otros activos"""
        try:
            if symbol not in historical_prices:
                return False
            
            symbol_prices = historical_prices[symbol]
            if len(symbol_prices) < 30:  # Necesitamos al menos 30 días de datos
                return False
                
            symbol_returns = np.diff(np.log(symbol_prices))
            
            for other_symbol, other_prices in historical_prices.items():
                if other_symbol == symbol:
                    continue
                    
                if len(other_prices) < 30:  # Saltamos si no hay suficientes datos
                    continue
                    
                other_returns = np.diff(np.log(other_prices))
                
                # Asegurarnos de que tenemos el mismo número de puntos de datos
                min_len = min(len(symbol_returns), len(other_returns))
                if min_len < 30:  # No calcular correlación si no hay suficientes datos
                    continue
                    
                symbol_returns_aligned = symbol_returns[-min_len:]
                other_returns_aligned = other_returns[-min_len:]
                
                # Calcular correlación solo si tenemos datos válidos
                if not np.any(np.isnan(symbol_returns_aligned)) and not np.any(np.isnan(other_returns_aligned)):
                    correlation = np.corrcoef(symbol_returns_aligned, other_returns_aligned)[0, 1]
                    if not np.isnan(correlation) and abs(correlation) > self.params.correlation_threshold:
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error calculando correlaciones para {symbol}: {str(e)}")
            return False
    
    import requests
    from dataclasses import dataclass
    
    # Definimos una dataclass para configurar la API
    @dataclass
    class APIClientConfig:
        base_url: str
        api_key: str = None
        secret_key: str = None
    
    # Configuración de la API de Binance
    binance_api_config = APIClientConfig(base_url='https://api.binance.com')
    
    def get_24hr_ticker_price_change(symbol: str, config: APIClientConfig):
        """Obtiene el cambio de precio en las últimas 24 horas"""
        url = f"{config.base_url}/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Error al obtener datos de la API de Binance")
    
    class RiskManager:
        # ... Otros métodos ...
    
        def _check_liquidity(self, symbol: str, current_price: float) -> bool:
            """Verifica si el activo cumple con los requisitos mínimos de liquidez"""
            try:
                # Obtener datos de Binance
                ticker = get_24hr_ticker_price_change(symbol, binance_api_config)
                daily_volume = float(ticker.get('quoteVolume', 0))
                return daily_volume < self.params.min_liquidity
            except Exception as e:
                logger.error(f"Error verificando liquidez para {symbol}: {str(e)}")
                return True  # Por seguridad, asumimos riesgo de liquidez si hay error
            
    async def evaluate_risk(self, market_analysis: Dict) -> Dict:
        """Evalúa el riesgo basado en el análisis de mercado"""
        try:
            # Extraer datos relevantes del análisis de mercado
            positions = market_analysis.get('positions', {})
            symbol_data = market_analysis.get('symbol_data', {})
            market_conditions = market_analysis.get('market_conditions', 'neutral')
            market_metrics = market_analysis.get('market_metrics', {})
            
            # Evaluar riesgo general del mercado
            market_risk = self._evaluate_market_risk(market_conditions, market_metrics)
            
            # Evaluar riesgo por símbolo
            symbol_risks = {}
            portfolio_risk_score = 0
            symbols_evaluated = 0
            
            for symbol, data in symbol_data.items():
                if 'market_condition' not in data:
                    continue
                    
                mc = data['market_condition']
                ind = data.get('indicators', {})
                
                # Calcular puntuación de riesgo (0-100)
                risk_score = self._calculate_risk_score(
                    trend=mc.trend,
                    volatility=mc.volatility,
                    rsi=ind.get('rsi', 50),
                    volume_trend=mc.volume_trend,
                    risk_level=mc.risk_level,
                    market_cap=data.get('market_cap', 0),
                    change_24h=data.get('change_24h', 0)
                )
                
                symbol_risks[symbol] = {
                    'risk_score': risk_score,
                    'risk_level': mc.risk_level,
                    'volatility': mc.volatility,
                    'trend': mc.trend,
                    'volume_trend': mc.volume_trend,
                    'technical_signals': self._evaluate_technical_signals(ind)
                }
                
                portfolio_risk_score += risk_score
                symbols_evaluated += 1
            
            # Calcular riesgo promedio del portfolio
            avg_portfolio_risk = portfolio_risk_score / symbols_evaluated if symbols_evaluated > 0 else 50
            
            # Determinar si se debe operar
            should_trade = self._should_execute_trades(
                market_risk=market_risk,
                portfolio_risk=avg_portfolio_risk,
                market_conditions=market_conditions
            )
            
            return {
                'should_trade': should_trade,
                'market_risk': market_risk,
                'portfolio_risk': avg_portfolio_risk,
                'symbol_risks': symbol_risks,
                'market_conditions': market_conditions,
                'risk_summary': self._generate_risk_summary(
                    market_risk, avg_portfolio_risk, market_conditions, symbol_risks
                )
            }
            
        except Exception as e:
            logger.error(f"Error en la evaluación de riesgos: {str(e)}")
            return {
                'should_trade': False,
                'market_risk': 'high',
                'portfolio_risk': 100,
                'symbol_risks': {},
                'risk_summary': 'Error en la evaluación de riesgos',
                'error': str(e)
            }
            
    def _evaluate_market_risk(self, market_conditions: str, market_metrics: Dict) -> str:
        """Evalúa el nivel de riesgo general del mercado"""
        avg_volatility = market_metrics.get('average_volatility', 0)
        avg_strength = market_metrics.get('average_strength', 0)
        
        if avg_volatility > 0.4 or avg_strength < 0.2:
            return 'high'
        elif avg_volatility > 0.2 or avg_strength < 0.4:
            return 'medium'
        return 'low'
        
    def _calculate_risk_score(self, trend: str, volatility: float, rsi: float,
                            volume_trend: str, risk_level: str, market_cap: float,
                            change_24h: float) -> float:
        """Calcula una puntuación de riesgo (0-100) basada en múltiples factores"""
        score = 50  # Punto de partida neutral
        
        # Ajustar por tendencia
        if trend == 'bullish':
            score -= 10
        elif trend == 'bearish':
            score += 10
            
        # Ajustar por volatilidad (0-1)
        score += volatility * 20
        
        # Ajustar por RSI (0-100)
        if rsi > 70:
            score += 15  # Sobrecomprado
        elif rsi < 30:
            score += 10  # Sobrevendido
            
        # Ajustar por tendencia de volumen
        if volume_trend == 'increasing':
            score -= 5
        elif volume_trend == 'decreasing':
            score += 5
            
        # Ajustar por nivel de riesgo
        if risk_level == 'high':
            score += 15
        elif risk_level == 'low':
            score -= 15
            
        # Ajustar por capitalización de mercado
        if market_cap > 10e9:  # > 10B
            score -= 10
        elif market_cap < 1e9:  # < 1B
            score += 10
            
        # Ajustar por cambio en 24h
        if abs(change_24h) > 20:
            score += 10
            
        return max(0, min(100, score))  # Asegurar que esté entre 0 y 100
        
    def _evaluate_technical_signals(self, indicators: Dict) -> Dict:
        """Evalúa las señales técnicas"""
        signals = {
            'rsi': 'neutral',
            'macd': 'neutral',
            'bollinger': 'neutral'
        }
        
        # Evaluar RSI
        rsi = indicators.get('rsi', 50)
        if rsi > 70:
            signals['rsi'] = 'overbought'
        elif rsi < 30:
            signals['rsi'] = 'oversold'
            
        # Evaluar MACD
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        if macd > macd_signal:
            signals['macd'] = 'bullish'
        elif macd < macd_signal:
            signals['macd'] = 'bearish'
            
        # Evaluar Bandas de Bollinger
        if 'bollinger' in indicators:
            price = indicators.get('price', 0)
            upper, middle, lower = indicators['bollinger']
            if price > upper:
                signals['bollinger'] = 'overbought'
            elif price < lower:
                signals['bollinger'] = 'oversold'
                
        return signals
        
    def _should_execute_trades(self, market_risk: str, portfolio_risk: float,
                             market_conditions: str) -> bool:
        """Determina si se deben ejecutar operaciones"""
        # No operar en condiciones de alto riesgo
        if market_risk == 'high' and portfolio_risk > 70:
            return False
            
        # No operar en mercados muy bajistas
        if market_conditions == 'bearish' and portfolio_risk > 60:
            return False
            
        # Operar en mercados alcistas con riesgo controlado
        if market_conditions == 'bullish' and portfolio_risk < 80:
            return True
            
        # En condiciones neutrales, operar solo con riesgo moderado
        return portfolio_risk < 65
        
    def _generate_risk_summary(self, market_risk: str, portfolio_risk: float,
                             market_conditions: str, symbol_risks: Dict) -> str:
        """Genera un resumen del análisis de riesgo"""
        summary = []
        summary.append(f"Riesgo de mercado: {market_risk}")
        summary.append(f"Riesgo del portfolio: {portfolio_risk:.1f}/100")
        summary.append(f"Condición del mercado: {market_conditions}")
        
        high_risk_symbols = [
            symbol for symbol, risk in symbol_risks.items()
            if risk['risk_level'] == 'high'
        ]
        
        if high_risk_symbols:
            summary.append("\nActivos de alto riesgo:")
            for symbol in high_risk_symbols:
                risk = symbol_risks[symbol]
                summary.append(f"- {symbol}: {risk['risk_score']:.1f}/100")
                
        return "\n".join(summary)
