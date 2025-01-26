import logging
import yaml
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import requests
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass
from tqdm import tqdm
from src.config import config

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LiveTradingParameters:
    """Parámetros para el trading en vivo"""
    weekly_investment: float = 100.0
    lookback_period: int = 90  # Período para calcular métricas
    min_volume_percentile: float = 25  # Percentil mínimo de volumen
    max_position_size: float = 0.30  # Tamaño máximo de posición (30%)
    rebalance_threshold: float = 0.05  # Umbral de rebalanceo (5%)


def validate_portfolio_weights(weights: Dict[str, float]) -> bool:
    """Valida que los pesos del portafolio sumen 1 y sean positivos"""
    total_weight = sum(weights.values())
    if not 0.999 <= total_weight <= 1.001:
        logger.error(f"Los pesos del portafolio no suman 1 (suma actual: {total_weight})")
        return False
    if not all(weight >= 0 for weight in weights.values()):
        logger.error("Los pesos del portafolio deben ser positivos")
        return False
    return True


class LiveDCATrader:
    def __init__(self, params: Dict):
        self.params = LiveTradingParameters(
            weekly_investment=params.get('weekly_investment', 100.0),
            lookback_period=params.get('lookback_period', 90),
            min_volume_percentile=params.get('min_volume_percentile', 25),
            max_position_size=params.get('max_position_size', 0.30),
            rebalance_threshold=params.get('rebalance_threshold', 0.05)
        )
        self.portfolio_weights = params.get('portfolio_weights', {})
        self.next_execution_date = self._calculate_next_tuesday()
        self.current_prices = {}

        # Verificar que los pesos sumen 1
        if not validate_portfolio_weights(self.portfolio_weights):
            raise ValueError("Los pesos del portafolio no son válidos")

        logger.info(f"Próxima ejecución programada para: {self.next_execution_date}")

    async def execute_trades(self, market_analysis: Dict) -> Dict:
        """Execute trades based on market analysis and risk parameters"""
        try:
            # Update current prices
            self._update_current_prices()

            # Get current portfolio
            portfolio = await self._get_current_portfolio()

            # Calculate target allocations considering risk parameters
            target_allocations = self._calculate_target_allocations(
                portfolio,
                market_analysis
            )

            logger.debug(f"Current prices: {self.current_prices}")

            # Generate trade orders with proper position sizing
            orders = self._generate_trade_orders(
                portfolio,
                target_allocations,
                market_analysis
            )

            # Execute orders with error handling
            execution_results = await self._execute_orders(orders)

            # Log trade execution
            await self._log_trade_execution(orders, execution_results)

            return {
                'status': 'success',
                'orders_executed': len(orders),
                'details': execution_results
            }

        except Exception as e:
            logger.error(f"Trade execution error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'orders_executed': 0
            }

    async def _get_current_portfolio(self) -> Dict:
        """Get simulated portfolio holdings"""
        try:
            # Simular un portfolio vacío para nuevas inversiones
            portfolio = {
                symbol: {
                    'free': 0.0,
                    'locked': 0.0
                }
                for symbol in self.portfolio_weights.keys()
            }

            logger.debug(f"Current portfolio (simulation): {portfolio}")
            return portfolio

        except Exception as e:
            logger.error(f"Error getting simulated portfolio: {str(e)}")
            return {}

    def _calculate_target_allocations(self, portfolio: Dict, market_analysis: Dict) -> Dict:
        """Calculate target allocations considering risk parameters"""
        try:
            # Calculate total portfolio value
            total_value = sum(
                (asset['free'] + asset['locked']) * self.current_prices.get(symbol, 0)
                for symbol, asset in portfolio.items()
            )

            # Si el portfolio está vacío, usar los pesos objetivo directamente
            if total_value == 0:
                logger.debug("Portfolio vacío - usando pesos objetivo iniciales")
                return self.portfolio_weights

            # Calculate current allocations
            current_allocations = {
                symbol: (asset['free'] + asset['locked']) * self.current_prices.get(symbol, 0) / total_value
                for symbol, asset in portfolio.items()
            }

            # Calculate desired allocations based on strategy weights
            desired_allocations = {
                symbol: self.portfolio_weights.get(symbol, 0)
                for symbol in portfolio.keys()
            }

            # Apply risk parameters
            target_allocations = {}
            for symbol in portfolio.keys():
                # Calculate target allocation considering max position size
                target = min(
                    desired_allocations[symbol],
                    self.params.max_position_size
                )

                # Check if rebalancing is needed
                current = current_allocations.get(symbol, 0)
                if abs(current - target) > self.params.rebalance_threshold:
                    target_allocations[symbol] = target
                else:
                    target_allocations[symbol] = current

            # Normalize allocations to sum to 1
            total = sum(target_allocations.values())
            if total > 0:
                target_allocations = {
                    k: v / total
                    for k, v in target_allocations.items()
                }

            logger.debug(f"Target allocations calculated: {target_allocations}")
            return target_allocations

        except Exception as e:
            logger.error(f"Error calculating target allocations: {str(e)}")
            return {}

    def _generate_trade_orders(self, portfolio: Dict, target_allocations: Dict, market_analysis: Dict) -> List[Dict]:
        """Generate trade orders with proper position sizing"""
        try:
            orders = []
            # Si el portfolio está vacío, usar la inversión semanal como base
            total_value = sum(
                (asset['free'] + asset['locked']) * self.current_prices.get(symbol, 0)
                for symbol, asset in portfolio.items()
            )

            if total_value == 0:
                total_value = self.params.weekly_investment
                logger.debug(f"Portfolio vacío - usando inversión semanal: ${total_value}")

            for symbol, target_weight in target_allocations.items():
                current_asset = portfolio.get(symbol, {'free': 0, 'locked': 0})
                current_value = (current_asset['free'] + current_asset['locked']) * self.current_prices.get(symbol, 0)
                target_value = total_value * target_weight

                # Calculate value difference
                value_diff = target_value - current_value

                # Only create order if difference is significant
                if abs(value_diff) > 1.0:  # Minimum trade size of $1
                    order_type = 'BUY' if value_diff > 0 else 'SELL'
                    quantity = abs(value_diff) / self.current_prices[symbol]

                    # Apply position sizing rules
                    max_order_value = self.params.weekly_investment * self.params.max_position_size
                    order_value = min(abs(value_diff), max_order_value)

                    # Round quantity to appropriate decimal places
                    quantity = round(quantity, self._get_quantity_precision(symbol))

                    orders.append({
                        'symbol': symbol,
                        'type': order_type,
                        'quantity': quantity,
                        'price': self.current_prices[symbol],
                        'value': order_value,
                        'timestamp': datetime.now().isoformat()
                    })

            logger.debug(f"Generated {len(orders)} trade orders")
            return orders

        except Exception as e:
            logger.error(f"Error generating trade orders: {str(e)}")
            return []

    def _get_quantity_precision(self, symbol: str) -> int:
        """Get quantity precision for a symbol based on exchange rules"""
        # Binance typically uses 8 decimal places for most cryptocurrencies
        # This could be enhanced by querying exchange info endpoint
        return 8

    async def _execute_orders(self, orders: List[Dict]) -> List[Dict]:
        """Simulate order execution"""
        results = []

        for order in orders:
            # Simular una ejecución exitosa
            results.append({
                'status': 'success',
                'order_id': f"sim_{datetime.now().timestamp()}",
                'symbol': order['symbol'],
                'executed_quantity': order['quantity'],
                'cumulative_quote_qty': order['quantity'] * order['price'],
                'status': 'FILLED',
                'fills': [{
                    'price': order['price'],
                    'quantity': order['quantity'],
                    'commission': 0.001 * order['quantity'] * order['price']  # 0.1% comisión simulada
                }]
            })

        logger.debug(f"Simulated execution of {len(results)} orders successfully")
        return results

    async def _log_trade_execution(self, orders: List[Dict], results: List[Dict]):
        """Log trade execution details to database and file"""
        try:
            # Create execution log entry
            execution_log = {
                'timestamp': datetime.now().isoformat(),
                'orders': orders,
                'results': results,
                'status': 'completed' if all(r['status'] == 'success' for r in results) else 'partial',
                'total_value': sum(
                    r['cumulative_quote_qty']
                    for r in results
                    if r['status'] == 'success'
                ),
                'success_count': len([r for r in results if r['status'] == 'success']),
                'error_count': len([r for r in results if r['status'] == 'error'])
            }

            # Append to JSON log file
            try:
                with open("trade_execution_log.json", "r") as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = []

            history.append(execution_log)

            with open("trade_execution_log.json", "w") as f:
                json.dump(history, f, indent=2)

            logger.debug(f"Logged trade execution with {execution_log['success_count']} successful orders")

            # TODO: Add database logging implementation
            # This would connect to a database and store the execution details
            # for long-term analysis and reporting

        except Exception as e:
            logger.error(f"Error logging trade execution: {str(e)}")

    def _update_current_prices(self):
        """Actualiza los precios actuales de los activos usando solicitudes en paralelo"""
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(self._get_current_price, symbol) for symbol in self.portfolio_weights.keys()]
                for future in tqdm(futures, desc="Actualizando precios", unit="símbolo"):
                    symbol, price = future.result()
                    if price:
                        self.current_prices[symbol] = price
                    else:
                        logger.warning(f"No se pudo obtener el precio para {symbol}")
        except Exception as e:
            error_msg = f"Error al obtener precios actuales: {str(e)}"
            logger.error(error_msg)
            raise

    def _get_current_price(self, symbol: str) -> Tuple[str, Optional[float]]:
        """Obtiene el precio actual de un activo desde el análisis de mercado"""
        try:
            # Simular un precio basado en el último precio conocido o un valor por defecto
            # En una implementación real, estos precios vendrían del análisis de mercado
            simulated_prices = {
                'BTCUSDT': 42000.0,
                'ETHUSDT': 2200.0,
                'XRPUSDT': 0.55,
                'SOLUSDT': 98.0,
                'BNBUSDT': 305.0,
                'DOGEUSDT': 0.08,
                'ADAUSDT': 0.45,
                'TRXUSDT': 0.11,
                'AVAXUSDT': 34.0,
                'LINKUSDT': 15.0
            }
            price = simulated_prices.get(symbol)
            if price is None:
                logger.warning(f"No se encontró precio simulado para {symbol}")
                return symbol, None
            return symbol, price
        except Exception as e:
            logger.warning(f"Error al obtener precio simulado para {symbol}: {str(e)}")
            return symbol, None

    def _calculate_next_tuesday(self) -> datetime:
        """Calcula la próxima fecha de ejecución (martes)"""
        today = datetime.now()
        days_until_tuesday = (1 - today.weekday()) % 7  # 1 = martes
        if days_until_tuesday == 0 and today.hour >= 16:  # Si es martes después de las 16:00
            days_until_tuesday = 7
        next_tuesday = today + timedelta(days=days_until_tuesday)
        return next_tuesday.replace(hour=16, minute=0, second=0, microsecond=0)

    def _validate_balance(self, balance: float) -> bool:
        """Valida el saldo disponible"""
        if not isinstance(balance, (int, float)):
            error_msg = "El saldo debe ser un número"
            logger.error(error_msg)
            return False
        if balance <= 0:
            error_msg = "El saldo debe ser positivo"
            logger.error(error_msg)
            return False
        if balance > 1000:  # Límite máximo de seguridad
            error_msg = "El saldo excede el límite máximo permitido"
            logger.error(error_msg)
            return False
        return True

    def _calculate_investment_amounts(self, available_balance: float) -> Dict[str, float]:
        """Calcula los montos de inversión considerando los precios actuales"""
        investments = {}
        for symbol, weight in self.portfolio_weights.items():
            investment_amount = Decimal(str(available_balance * weight))
            # Redondear a 2 decimales hacia abajo
            investments[symbol] = float(investment_amount.quantize(Decimal('0.01'), rounding=ROUND_DOWN))
        return investments

    def execute_dca_strategy(self, available_balance: float):
        """Ejecuta la estrategia DCA con el saldo disponible"""
        if not self._validate_balance(available_balance):
            return

        self._update_current_prices()
        investments = self._calculate_investment_amounts(available_balance)
        self._log_recommendations(investments)

        return investments

    def _log_recommendations(self, investments: Dict[str, float]):
        """Registra las recomendaciones de inversión"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        recommendations = {
            "timestamp": timestamp,
            "investments": investments,
            "prices": self.current_prices,
            "next_execution": self.next_execution_date.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            with open("recommendations.json", "r") as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []

        history.append(recommendations)

        with open("recommendations.json", "w") as f:
            json.dump(history, f, indent=2)

        logger.debug("Recomendaciones registradas en recommendations.json")
