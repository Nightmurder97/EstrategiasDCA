"""
Optimizador Automático de Portafolios
Genera múltiples portafolios optimizados con diferentes estrategias y perfiles de riesgo
"""

import logging
import math
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_manager import PortfolioManager, PortfolioDefinition
from config_models import load_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AssetProfile:
    """Perfil de un activo para optimización"""
    symbol: str
    category: str  # large_cap, mid_cap, small_cap, stable
    volatility: float  # Volatilidad histórica
    correlation_btc: float  # Correlación con BTC
    liquidity_score: float  # Puntuación de liquidez
    market_cap_rank: int  # Ranking por capitalización
    risk_score: float  # Puntuación de riesgo (1-10)

class PortfolioOptimizer:
    """Optimizador automático de portafolios"""
    
    def __init__(self):
        self.config = load_config()
        self.pm = PortfolioManager()
        
        # Definir activos disponibles con sus perfiles
        self.assets = self._define_asset_profiles()
        
        # Estrategias predefinidas
        self.strategies = self._define_strategies()
        
        logger.info(f"Optimizador inicializado con {len(self.assets)} activos")
    
    def _define_asset_profiles(self) -> Dict[str, AssetProfile]:
        """Definir perfiles de activos disponibles"""
        return {
            # Large Cap - Baja volatilidad, alta liquidez
            "BTC": AssetProfile("BTC", "large_cap", 0.85, 1.0, 10.0, 1, 5.0),
            "ETH": AssetProfile("ETH", "large_cap", 0.90, 0.85, 9.5, 2, 5.5),
            "BNB": AssetProfile("BNB", "large_cap", 0.95, 0.75, 9.0, 3, 6.0),
            
            # Mid Cap - Volatilidad media
            "ADA": AssetProfile("ADA", "mid_cap", 1.10, 0.70, 8.0, 8, 6.5),
            "DOT": AssetProfile("DOT", "mid_cap", 1.15, 0.65, 7.5, 12, 7.0),
            "LINK": AssetProfile("LINK", "mid_cap", 1.20, 0.60, 7.0, 15, 7.0),
            "UNI": AssetProfile("UNI", "mid_cap", 1.25, 0.55, 6.5, 20, 7.5),
            
            # Small Cap - Alta volatilidad, menor liquidez
            "MATIC": AssetProfile("MATIC", "small_cap", 1.30, 0.50, 6.0, 25, 8.0),
            "ATOM": AssetProfile("ATOM", "small_cap", 1.35, 0.45, 5.5, 30, 8.5),
            "AVAX": AssetProfile("AVAX", "small_cap", 1.40, 0.40, 5.0, 35, 8.5),
            
            # Stablecoins - Estabilidad
            "USDT": AssetProfile("USDT", "stable", 0.05, 0.10, 10.0, 3, 1.0),
            "USDC": AssetProfile("USDC", "stable", 0.05, 0.10, 9.5, 5, 1.0),
        }
    
    def _define_strategies(self) -> Dict[str, Dict]:
        """Definir estrategias de portafolio predefinidas"""
        return {
            "ultra_conservative": {
                "name": "Ultra Conservador",
                "description": "Máxima estabilidad, mínimo riesgo",
                "risk_tolerance": "low",
                "stable_allocation": 0.50,  # 50% stablecoins
                "large_cap_min": 0.40,      # 40% large caps mínimo
                "max_single_asset": 0.30,   # 30% máximo por activo
                "min_assets": 4,
                "max_assets": 6
            },
            "conservative": {
                "name": "Conservador",
                "description": "Enfoque en estabilidad con crecimiento moderado",
                "risk_tolerance": "low",
                "stable_allocation": 0.30,  # 30% stablecoins
                "large_cap_min": 0.50,      # 50% large caps mínimo
                "max_single_asset": 0.35,   # 35% máximo por activo
                "min_assets": 5,
                "max_assets": 7
            },
            "balanced": {
                "name": "Equilibrado",
                "description": "Balance entre estabilidad y crecimiento",
                "risk_tolerance": "medium",
                "stable_allocation": 0.20,  # 20% stablecoins
                "large_cap_min": 0.40,      # 40% large caps mínimo
                "max_single_asset": 0.40,   # 40% máximo por activo
                "min_assets": 6,
                "max_assets": 8
            },
            "growth": {
                "name": "Crecimiento",
                "description": "Enfoque en crecimiento con riesgo controlado",
                "risk_tolerance": "medium",
                "stable_allocation": 0.10,  # 10% stablecoins
                "large_cap_min": 0.30,      # 30% large caps mínimo
                "max_single_asset": 0.45,   # 45% máximo por activo
                "min_assets": 7,
                "max_assets": 9
            },
            "aggressive": {
                "name": "Agresivo",
                "description": "Máximo crecimiento, riesgo elevado",
                "risk_tolerance": "high",
                "stable_allocation": 0.05,  # 5% stablecoins
                "large_cap_min": 0.20,      # 20% large caps mínimo
                "max_single_asset": 0.50,   # 50% máximo por activo
                "min_assets": 8,
                "max_assets": 10
            },
            "btc_focused": {
                "name": "Bitcoin Dominante",
                "description": "Estrategia centrada en Bitcoin",
                "risk_tolerance": "medium",
                "stable_allocation": 0.15,  # 15% stablecoins
                "large_cap_min": 0.60,      # 60% large caps (principalmente BTC)
                "max_single_asset": 0.60,   # 60% máximo (permite BTC dominante)
                "min_assets": 4,
                "max_assets": 6
            },
            "defi_focused": {
                "name": "DeFi Especializado",
                "description": "Enfoque en tokens DeFi y ecosistemas",
                "risk_tolerance": "high",
                "stable_allocation": 0.10,  # 10% stablecoins
                "large_cap_min": 0.30,      # 30% large caps
                "max_single_asset": 0.40,   # 40% máximo por activo
                "min_assets": 7,
                "max_assets": 9
            },
            "diversified": {
                "name": "Máxima Diversificación",
                "description": "Diversificación extrema entre múltiples activos",
                "risk_tolerance": "medium",
                "stable_allocation": 0.15,  # 15% stablecoins
                "large_cap_min": 0.35,      # 35% large caps
                "max_single_asset": 0.25,   # 25% máximo por activo
                "min_assets": 9,
                "max_assets": 10
            }
        }
    
    def generate_optimized_allocation(self, strategy_name: str) -> Dict[str, float]:
        """
        Generar allocation optimizada para una estrategia específica
        
        Args:
            strategy_name: Nombre de la estrategia
            
        Returns:
            Dict con la allocation optimizada {symbol: weight}
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Estrategia '{strategy_name}' no encontrada")
        
        strategy = self.strategies[strategy_name]
        
        # Paso 1: Seleccionar activos según la estrategia
        selected_assets = self._select_assets_for_strategy(strategy)
        
        # Paso 2: Generar pesos optimizados
        allocation = self._optimize_weights(selected_assets, strategy)
        
        # Paso 3: Validar y ajustar
        allocation = self._validate_and_adjust_allocation(allocation, strategy)
        
        logger.info(f"Allocation generada para {strategy_name}: {allocation}")
        return allocation
    
    def _select_assets_for_strategy(self, strategy: Dict) -> List[str]:
        """Seleccionar activos apropiados para la estrategia"""
        selected = []
        
        # Categorizar activos
        large_caps = [s for s, p in self.assets.items() if p.category == "large_cap"]
        mid_caps = [s for s, p in self.assets.items() if p.category == "mid_cap"]
        small_caps = [s for s, p in self.assets.items() if p.category == "small_cap"]
        stables = [s for s, p in self.assets.items() if p.category == "stable"]
        
        # Seleccionar stablecoins si la estrategia los requiere
        if strategy["stable_allocation"] > 0:
            selected.extend(stables[:2])  # USDT y USDC
        
        # Seleccionar large caps
        large_cap_count = max(2, int(strategy["large_cap_min"] * 5))  # Al menos 2
        selected.extend(large_caps[:large_cap_count])
        
        # Seleccionar mid caps según tolerancia al riesgo
        if strategy["risk_tolerance"] in ["medium", "high"]:
            mid_cap_count = 2 if strategy["risk_tolerance"] == "medium" else 4
            selected.extend(mid_caps[:mid_cap_count])
        
        # Seleccionar small caps para estrategias agresivas
        if strategy["risk_tolerance"] == "high":
            small_cap_count = 2
            selected.extend(small_caps[:small_cap_count])
        
        # Ajustar según límites de activos
        target_count = random.randint(strategy["min_assets"], strategy["max_assets"])
        selected = list(set(selected))  # Eliminar duplicados
        
        if len(selected) > target_count:
            # Priorizar por calidad (liquidez y ranking)
            selected.sort(key=lambda x: (self.assets[x].liquidity_score, -self.assets[x].market_cap_rank), reverse=True)
            selected = selected[:target_count]
        
        logger.info(f"Activos seleccionados: {selected}")
        return selected
    
    def _optimize_weights(self, assets: List[str], strategy: Dict) -> Dict[str, float]:
        """Optimizar pesos de los activos seleccionados"""
        allocation = {}
        
        # Separar por categorías
        stables = [a for a in assets if self.assets[a].category == "stable"]
        large_caps = [a for a in assets if self.assets[a].category == "large_cap"]
        mid_caps = [a for a in assets if self.assets[a].category == "mid_cap"]
        small_caps = [a for a in assets if self.assets[a].category == "small_cap"]
        
        # Asignar pesos a stablecoins
        if stables:
            stable_weight = strategy["stable_allocation"]
            if len(stables) == 1:
                allocation[stables[0]] = stable_weight
            else:
                # Dividir entre USDT y USDC
                allocation[stables[0]] = stable_weight * 0.6  # USDT ligeramente más
                allocation[stables[1]] = stable_weight * 0.4
        
        # Peso restante para otros activos
        remaining_weight = 1.0 - strategy["stable_allocation"]
        
        # Asignar pesos a large caps (prioridad)
        if large_caps:
            large_cap_weight = max(strategy["large_cap_min"], remaining_weight * 0.5)
            large_cap_weight = min(large_cap_weight, remaining_weight * 0.8)
            
            if len(large_caps) == 1:
                allocation[large_caps[0]] = large_cap_weight
            else:
                # BTC dominante si está presente
                if "BTC" in large_caps:
                    allocation["BTC"] = large_cap_weight * 0.5
                    remaining_lc = large_cap_weight * 0.5
                    other_lc = [a for a in large_caps if a != "BTC"]
                    for asset in other_lc:
                        allocation[asset] = remaining_lc / len(other_lc)
                else:
                    # Distribución equitativa
                    for asset in large_caps:
                        allocation[asset] = large_cap_weight / len(large_caps)
            
            remaining_weight -= large_cap_weight
        
        # Asignar pesos a mid caps
        if mid_caps and remaining_weight > 0:
            mid_cap_weight = remaining_weight * 0.7
            for asset in mid_caps:
                allocation[asset] = mid_cap_weight / len(mid_caps)
            remaining_weight -= mid_cap_weight
        
        # Asignar pesos a small caps
        if small_caps and remaining_weight > 0:
            for asset in small_caps:
                allocation[asset] = remaining_weight / len(small_caps)
        
        return allocation
    
    def _validate_and_adjust_allocation(self, allocation: Dict[str, float], strategy: Dict) -> Dict[str, float]:
        """Validar y ajustar allocation según restricciones"""
        total_weight = sum(allocation.values())
        
        # Normalizar si no suma 1.0
        if abs(total_weight - 1.0) > 0.001:
            allocation = {k: v / total_weight for k, v in allocation.items()}
        
        # Verificar límite máximo por activo
        max_single = strategy["max_single_asset"]
        adjustments_needed = True
        
        while adjustments_needed:
            adjustments_needed = False
            for asset, weight in allocation.items():
                if weight > max_single:
                    # Reducir peso excesivo
                    excess = weight - max_single
                    allocation[asset] = max_single
                    
                    # Redistribuir exceso entre otros activos
                    other_assets = [a for a in allocation.keys() if a != asset]
                    if other_assets:
                        redistribution = excess / len(other_assets)
                        for other_asset in other_assets:
                            allocation[other_asset] += redistribution
                    
                    adjustments_needed = True
                    break
        
        # Redondear a 3 decimales
        allocation = {k: round(v, 3) for k, v in allocation.items()}
        
        # Ajuste final para que sume exactamente 1.0
        total = sum(allocation.values())
        if abs(total - 1.0) > 0.001:
            # Ajustar el activo con mayor peso
            largest_asset = max(allocation.keys(), key=lambda x: allocation[x])
            allocation[largest_asset] += 1.0 - total
            allocation[largest_asset] = round(allocation[largest_asset], 3)
        
        return allocation
    
    def create_all_optimized_portfolios(self) -> List[str]:
        """
        Crear todos los portafolios optimizados automáticamente
        
        Returns:
            Lista de IDs de portafolios creados
        """
        created_portfolios = []
        
        # Crear un portafolio por cada estrategia
        for strategy_name, strategy_config in self.strategies.items():
            try:
                allocation = self.generate_optimized_allocation(strategy_name)
                
                portfolio_id = self.pm.create_portfolio(
                    name=strategy_config["name"],
                    portfolio_type=strategy_name,
                    allocation=allocation,
                    description=strategy_config["description"],
                    initial_balance=0.0,
                    risk_tolerance=strategy_config["risk_tolerance"]
                )
                
                created_portfolios.append(portfolio_id)
                logger.info(f"✅ Portafolio creado: {portfolio_id}")
                
            except Exception as e:
                logger.error(f"❌ Error creando portafolio {strategy_name}: {e}")
        
        # Crear 2 portafolios adicionales con variaciones
        try:
            # Portafolio 9: Variación conservadora
            variation_1 = self.generate_optimized_allocation("balanced")
            portfolio_id_1 = self.pm.create_portfolio(
                name="Equilibrado Plus",
                portfolio_type="balanced_plus",
                allocation=variation_1,
                description="Variación equilibrada con ajustes dinámicos",
                initial_balance=0.0,
                risk_tolerance="medium"
            )
            created_portfolios.append(portfolio_id_1)
            
            # Portafolio 10: Variación agresiva
            variation_2 = self.generate_optimized_allocation("growth")
            portfolio_id_2 = self.pm.create_portfolio(
                name="Crecimiento Acelerado",
                portfolio_type="growth_accelerated",
                allocation=variation_2,
                description="Variación de crecimiento con mayor exposición",
                initial_balance=0.0,
                risk_tolerance="high"
            )
            created_portfolios.append(portfolio_id_2)
            
        except Exception as e:
            logger.error(f"❌ Error creando portafolios adicionales: {e}")
        
        logger.info(f"🎉 Creados {len(created_portfolios)} portafolios optimizados")
        return created_portfolios
    
    def get_optimization_summary(self) -> Dict:
        """Obtener resumen de la optimización"""
        summary = {
            "optimization_date": datetime.now().isoformat(),
            "total_strategies": len(self.strategies),
            "total_assets": len(self.assets),
            "strategies_detail": {}
        }
        
        for strategy_name, strategy_config in self.strategies.items():
            summary["strategies_detail"][strategy_name] = {
                "name": strategy_config["name"],
                "description": strategy_config["description"],
                "risk_tolerance": strategy_config["risk_tolerance"],
                "stable_allocation": strategy_config["stable_allocation"],
                "asset_range": f"{strategy_config['min_assets']}-{strategy_config['max_assets']}"
            }
        
        return summary

def main():
    """Función principal para ejecutar la optimización"""
    print("🚀 Iniciando optimización automática de portafolios...")
    
    optimizer = PortfolioOptimizer()
    
    # Crear todos los portafolios optimizados
    created_portfolios = optimizer.create_all_optimized_portfolios()
    
    # Mostrar resumen
    summary = optimizer.get_optimization_summary()
    pm_summary = optimizer.pm.get_portfolio_summary()
    
    print("\n" + "="*60)
    print("🎯 OPTIMIZACIÓN COMPLETADA")
    print("="*60)
    print(f"📊 Portafolios creados: {len(created_portfolios)}")
    print(f"📈 Estrategias implementadas: {summary['total_strategies']}")
    print(f"💎 Activos disponibles: {summary['total_assets']}")
    print(f"🎪 Portafolios activos: {pm_summary['active_portfolios']}")
    
    print("\n📋 PORTAFOLIOS CREADOS:")
    for i, portfolio_id in enumerate(created_portfolios, 1):
        print(f"   {i:2d}. {portfolio_id}")
    
    print("\n🔄 Próximos pasos:")
    print("   - Implementar sistema de rebalanceo automático")
    print("   - Configurar monitoreo de métricas")
    print("   - Establecer alertas de riesgo")
    print("   - Iniciar simulación con datos históricos")
    
    return created_portfolios

if __name__ == "__main__":
    main() 