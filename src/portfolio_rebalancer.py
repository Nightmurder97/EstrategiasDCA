"""
Sistema de Rebalanceo Automático para Múltiples Portafolios
Monitorea desviaciones y ejecuta rebalanceo automático cuando es necesario
"""

import logging
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_manager import PortfolioManager, PortfolioDefinition, PortfolioSnapshot
from config_models import load_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RebalanceAction:
    """Acción de rebalanceo para un activo"""
    symbol: str
    current_weight: float
    target_weight: float
    deviation: float
    action: str  # "buy", "sell", "hold"
    amount_change: float
    priority: int  # 1-5, 1 es más prioritario

@dataclass
class RebalanceExecution:
    """Registro de ejecución de rebalanceo"""
    portfolio_id: str
    execution_date: str
    trigger_reason: str
    actions: List[RebalanceAction]
    total_deviation: float
    execution_status: str  # "planned", "executed", "failed"
    execution_notes: str

class PortfolioRebalancer:
    """Sistema de rebalanceo automático para múltiples portafolios"""
    
    def __init__(self):
        self.config = load_config()
        self.pm = PortfolioManager()
        self.rebalance_dir = Path("portfolios/performance/rebalancing_history")
        self.rebalance_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuraciones de rebalanceo
        self.min_rebalance_interval = timedelta(days=7)  # Mínimo 7 días entre rebalanceos
        self.max_rebalance_interval = timedelta(days=30)  # Máximo 30 días sin rebalancear
        self.min_trade_value = 10.0  # Mínimo valor de trade en USD
        
        logger.info("Sistema de rebalanceo automático inicializado")
    
    def check_rebalance_needed(self, portfolio_id: str) -> Tuple[bool, float, str]:
        """
        Verificar si un portafolio necesita rebalanceo
        
        Args:
            portfolio_id: ID del portafolio
            
        Returns:
            Tuple (needs_rebalance, total_deviation, reason)
        """
        if portfolio_id not in self.pm.portfolios:
            return False, 0.0, "Portfolio not found"
        
        portfolio = self.pm.portfolios[portfolio_id]
        
        # Obtener snapshot actual (simulado con precios mock)
        current_snapshot = self._get_current_snapshot(portfolio_id)
        
        if not current_snapshot:
            return False, 0.0, "No current snapshot available"
        
        # Calcular desviaciones
        total_deviation = 0.0
        max_deviation = 0.0
        deviations = {}
        
        for symbol, target_weight in portfolio.allocation.items():
            current_weight = 0.0
            if symbol in current_snapshot.positions:
                current_weight = current_snapshot.positions[symbol].get("weight", 0.0)
            
            deviation = abs(current_weight - target_weight)
            deviations[symbol] = deviation
            total_deviation += deviation
            max_deviation = max(max_deviation, deviation)
        
        # Determinar si necesita rebalanceo
        needs_rebalance = False
        reason = ""
        
        if max_deviation > portfolio.rebalance_threshold:
            needs_rebalance = True
            reason = f"Desviación máxima: {max_deviation:.3f} > {portfolio.rebalance_threshold:.3f}"
        elif total_deviation > portfolio.rebalance_threshold * 2:
            needs_rebalance = True
            reason = f"Desviación total: {total_deviation:.3f} > {portfolio.rebalance_threshold * 2:.3f}"
        elif self._time_since_last_rebalance(portfolio_id) > self.max_rebalance_interval:
            needs_rebalance = True
            reason = f"Tiempo desde último rebalanceo > {self.max_rebalance_interval.days} días"
        
        # Verificar intervalo mínimo
        if needs_rebalance:
            time_since_last = self._time_since_last_rebalance(portfolio_id)
            if time_since_last < self.min_rebalance_interval:
                needs_rebalance = False
                reason = f"Intervalo mínimo no cumplido: {time_since_last.days} < {self.min_rebalance_interval.days} días"
        
        return needs_rebalance, total_deviation, reason
    
    def _get_current_snapshot(self, portfolio_id: str) -> Optional[PortfolioSnapshot]:
        """Obtener snapshot actual del portafolio (simulado con precios mock)"""
        if portfolio_id not in self.pm.portfolios:
            return None
        
        portfolio = self.pm.portfolios[portfolio_id]
        
        # Precios mock para simulación
        mock_prices = {
            "BTC": 45000.0,
            "ETH": 3200.0,
            "BNB": 350.0,
            "ADA": 0.45,
            "DOT": 6.5,
            "LINK": 15.0,
            "UNI": 8.0,
            "MATIC": 0.85,
            "ATOM": 12.0,
            "AVAX": 35.0,
            "USDT": 1.0,
            "USDC": 1.0
        }
        
        # Simular balance inicial de $10,000 para cálculos
        simulated_balance = 10000.0
        positions = {}
        
        for symbol, target_weight in portfolio.allocation.items():
            price = mock_prices.get(symbol, 1.0)
            target_value = simulated_balance * target_weight
            amount = target_value / price
            
            # Simular variación de precios ±5%
            price_variation = np.random.uniform(-0.05, 0.05)
            current_price = price * (1 + price_variation)
            current_value = amount * current_price
            current_weight = current_value / simulated_balance
            
            positions[symbol] = {
                "amount": amount,
                "value": current_value,
                "weight": current_weight
            }
        
        return PortfolioSnapshot(
            portfolio_id=portfolio_id,
            timestamp=datetime.now().isoformat(),
            total_value=simulated_balance,
            positions=positions,
            cash_balance=0.0,
            daily_pnl=0.0,
            total_pnl=0.0,
            metrics={}
        )
    
    def _time_since_last_rebalance(self, portfolio_id: str) -> timedelta:
        """Obtener tiempo desde el último rebalanceo"""
        if portfolio_id not in self.pm.portfolios:
            return timedelta(days=999)
        
        portfolio = self.pm.portfolios[portfolio_id]
        
        if not portfolio.last_rebalance:
            # Si nunca se ha rebalanceado, usar fecha de creación
            created_date = datetime.fromisoformat(portfolio.created_date)
            return datetime.now() - created_date
        
        last_rebalance = datetime.fromisoformat(portfolio.last_rebalance)
        return datetime.now() - last_rebalance
    
    def plan_rebalance(self, portfolio_id: str) -> Optional[RebalanceExecution]:
        """
        Planificar rebalanceo para un portafolio
        
        Args:
            portfolio_id: ID del portafolio
            
        Returns:
            Plan de rebalanceo o None si no es necesario
        """
        needs_rebalance, total_deviation, reason = self.check_rebalance_needed(portfolio_id)
        
        if not needs_rebalance:
            return None
        
        portfolio = self.pm.portfolios[portfolio_id]
        current_snapshot = self._get_current_snapshot(portfolio_id)
        
        if not current_snapshot:
            return None
        
        # Planificar acciones de rebalanceo
        actions = []
        
        for symbol, target_weight in portfolio.allocation.items():
            current_weight = 0.0
            if symbol in current_snapshot.positions:
                current_weight = current_snapshot.positions[symbol]["weight"]
            
            deviation = current_weight - target_weight
            
            if abs(deviation) > 0.01:  # Solo si desviación > 1%
                action_type = "sell" if deviation > 0 else "buy"
                amount_change = abs(deviation) * current_snapshot.total_value
                
                # Determinar prioridad
                priority = 1 if abs(deviation) > 0.05 else 2  # Alta prioridad si > 5%
                if amount_change < self.min_trade_value:
                    priority = 5  # Baja prioridad si monto es muy pequeño
                
                actions.append(RebalanceAction(
                    symbol=symbol,
                    current_weight=current_weight,
                    target_weight=target_weight,
                    deviation=deviation,
                    action=action_type,
                    amount_change=amount_change,
                    priority=priority
                ))
        
        # Ordenar por prioridad
        actions.sort(key=lambda x: x.priority)
        
        return RebalanceExecution(
            portfolio_id=portfolio_id,
            execution_date=datetime.now().isoformat(),
            trigger_reason=reason,
            actions=actions,
            total_deviation=total_deviation,
            execution_status="planned",
            execution_notes=""
        )
    
    def execute_rebalance(self, rebalance_plan: RebalanceExecution) -> bool:
        """
        Ejecutar plan de rebalanceo (simulado)
        
        Args:
            rebalance_plan: Plan de rebalanceo
            
        Returns:
            True si la ejecución fue exitosa
        """
        try:
            # Simular ejecución
            logger.info(f"Ejecutando rebalanceo para {rebalance_plan.portfolio_id}")
            
            executed_actions = []
            total_trades = 0
            
            for action in rebalance_plan.actions:
                if action.priority <= 3:  # Solo ejecutar acciones de alta/media prioridad
                    logger.info(f"  {action.action.upper()} {action.symbol}: "
                              f"{action.amount_change:.2f} USD "
                              f"({action.current_weight:.3f} -> {action.target_weight:.3f})")
                    executed_actions.append(action)
                    total_trades += 1
            
            # Actualizar estado del plan
            rebalance_plan.execution_status = "executed"
            rebalance_plan.execution_notes = f"Ejecutadas {total_trades} acciones de rebalanceo"
            
            # Guardar registro
            self._save_rebalance_record(rebalance_plan)
            
            # Actualizar fecha de último rebalanceo
            portfolio = self.pm.portfolios[rebalance_plan.portfolio_id]
            portfolio.last_rebalance = datetime.now().isoformat()
            self.pm.save_portfolio(rebalance_plan.portfolio_id)
            
            logger.info(f"Rebalanceo completado para {rebalance_plan.portfolio_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando rebalanceo: {e}")
            rebalance_plan.execution_status = "failed"
            rebalance_plan.execution_notes = f"Error: {str(e)}"
            self._save_rebalance_record(rebalance_plan)
            return False
    
    def _save_rebalance_record(self, rebalance_execution: RebalanceExecution):
        """Guardar registro de rebalanceo"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = self.rebalance_dir / f"{rebalance_execution.portfolio_id}_rebalance_{date_str}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(rebalance_execution), f, indent=4, ensure_ascii=False)
        
        logger.info(f"Registro de rebalanceo guardado: {file_path}")
    
    def run_automatic_rebalancing(self) -> Dict[str, str]:
        """
        Ejecutar rebalanceo automático para todos los portafolios activos
        
        Returns:
            Dict con resultados por portafolio
        """
        results = {}
        active_portfolios = self.pm.get_active_portfolios()
        
        logger.info(f"Iniciando rebalanceo automático para {len(active_portfolios)} portafolios")
        
        for portfolio in active_portfolios:
            try:
                # Verificar si necesita rebalanceo
                needs_rebalance, deviation, reason = self.check_rebalance_needed(portfolio.id)
                
                if not needs_rebalance:
                    results[portfolio.id] = f"No necesita rebalanceo: {reason}"
                    continue
                
                # Planificar rebalanceo
                rebalance_plan = self.plan_rebalance(portfolio.id)
                
                if not rebalance_plan:
                    results[portfolio.id] = "No se pudo planificar el rebalanceo"
                    continue
                
                # Ejecutar rebalanceo
                success = self.execute_rebalance(rebalance_plan)
                
                if success:
                    results[portfolio.id] = f"Rebalanceo exitoso: {len(rebalance_plan.actions)} acciones"
                else:
                    results[portfolio.id] = "Rebalanceo fallido"
                
            except Exception as e:
                logger.error(f"Error en rebalanceo automático para {portfolio.id}: {e}")
                results[portfolio.id] = f"Error: {str(e)}"
        
        return results
    
    def get_rebalance_summary(self) -> Dict:
        """Obtener resumen del estado de rebalanceo"""
        active_portfolios = self.pm.get_active_portfolios()
        summary = {
            "summary_date": datetime.now().isoformat(),
            "total_portfolios": len(active_portfolios),
            "portfolios_status": {}
        }
        
        for portfolio in active_portfolios:
            needs_rebalance, deviation, reason = self.check_rebalance_needed(portfolio.id)
            time_since_last = self._time_since_last_rebalance(portfolio.id)
            
            summary["portfolios_status"][portfolio.id] = {
                "name": portfolio.name,
                "needs_rebalance": needs_rebalance,
                "total_deviation": round(deviation, 4),
                "reason": reason,
                "days_since_last_rebalance": time_since_last.days,
                "rebalance_threshold": portfolio.rebalance_threshold
            }
        
        return summary

def main():
    """Función principal para ejecutar rebalanceo automático"""
    print("🔄 Iniciando sistema de rebalanceo automático...")
    
    rebalancer = PortfolioRebalancer()
    
    # Obtener resumen inicial
    summary = rebalancer.get_rebalance_summary()
    
    print("\n📊 ESTADO INICIAL DE PORTAFOLIOS:")
    print("="*50)
    for portfolio_id, status in summary["portfolios_status"].items():
        print(f"📋 {status['name']} ({portfolio_id})")
        print(f"   Necesita rebalanceo: {'✅ SÍ' if status['needs_rebalance'] else '❌ NO'}")
        print(f"   Desviación total: {status['total_deviation']:.4f}")
        print(f"   Días desde último: {status['days_since_last_rebalance']}")
        print(f"   Razón: {status['reason']}")
        print()
    
    # Ejecutar rebalanceo automático
    print("🚀 Ejecutando rebalanceo automático...")
    results = rebalancer.run_automatic_rebalancing()
    
    print("\n📈 RESULTADOS DEL REBALANCEO:")
    print("="*50)
    for portfolio_id, result in results.items():
        portfolio_name = summary["portfolios_status"][portfolio_id]["name"]
        print(f"📋 {portfolio_name}: {result}")
    
    print("\n✅ Rebalanceo automático completado")
    return results

if __name__ == "__main__":
    main() 