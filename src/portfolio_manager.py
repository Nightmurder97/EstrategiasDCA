"""
Gestor Principal de Múltiples Portafolios
Sistema avanzado para gestionar hasta 10 portafolios simultáneamente
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_models import load_config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PortfolioDefinition:
    """Definición completa de un portafolio"""
    id: str
    name: str
    type: str  # conservative, balanced, aggressive, etc.
    description: str
    allocation: Dict[str, float]  # {symbol: weight}
    initial_balance: float = 0.0
    max_position_size: float = 0.25  # 25% máximo por activo
    rebalance_threshold: float = 0.05  # 5% de desviación para rebalancear
    risk_tolerance: str = "medium"  # low, medium, high
    created_date: str = ""
    last_rebalance: str = ""
    status: str = "active"  # active, paused, archived
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

@dataclass
class PortfolioSnapshot:
    """Snapshot de estado de un portafolio en un momento dado"""
    portfolio_id: str
    timestamp: str
    total_value: float
    positions: Dict[str, Dict[str, float]]  # {symbol: {amount, value, weight}}
    cash_balance: float
    daily_pnl: float
    total_pnl: float
    metrics: Dict[str, float]  # sharpe, drawdown, etc.

class PortfolioManager:
    """Gestor principal de múltiples portafolios"""
    
    def __init__(self):
        self.config = load_config()
        self.portfolios_dir = Path("portfolios")
        self.definitions_dir = self.portfolios_dir / "definitions"
        self.performance_dir = self.portfolios_dir / "performance"
        self.active_dir = self.portfolios_dir / "active"
        
        self._ensure_directories()
        self.portfolios: Dict[str, PortfolioDefinition] = {}
        self.load_all_portfolios()
    
    def _ensure_directories(self):
        """Crear directorios necesarios si no existen"""
        directories = [
            self.portfolios_dir,
            self.definitions_dir,
            self.performance_dir,
            self.performance_dir / "daily_snapshots",
            self.performance_dir / "rebalancing_history",
            self.performance_dir / "risk_metrics",
            self.active_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio verificado: {directory}")
    
    def create_portfolio(
        self,
        name: str,
        portfolio_type: str,
        allocation: Dict[str, float],
        description: str = "",
        initial_balance: float = 0.0,
        risk_tolerance: str = "medium"
    ) -> str:
        """
        Crear un nuevo portafolio
        
        Args:
            name: Nombre del portafolio
            portfolio_type: Tipo (conservative, balanced, aggressive, etc.)
            allocation: Diccionario {symbol: weight}
            description: Descripción del portafolio
            initial_balance: Balance inicial (default 0.0)
            risk_tolerance: Tolerancia al riesgo (low, medium, high)
        
        Returns:
            portfolio_id: ID único del portafolio creado
        """
        # Validar allocation
        total_weight = sum(allocation.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Las ponderaciones deben sumar 1.0, actual: {total_weight}")
        
        # Generar ID único
        portfolio_id = f"portfolio_{len(self.portfolios) + 1:03d}_{portfolio_type}"
        
        # Crear definición del portafolio
        portfolio = PortfolioDefinition(
            id=portfolio_id,
            name=name,
            type=portfolio_type,
            description=description,
            allocation=allocation,
            initial_balance=initial_balance,
            risk_tolerance=risk_tolerance
        )
        
        # Guardar en memoria y disco
        self.portfolios[portfolio_id] = portfolio
        self.save_portfolio(portfolio_id)
        
        # Crear snapshot inicial
        self.create_initial_snapshot(portfolio_id)
        
        logger.info(f"Portafolio creado: {portfolio_id} - {name}")
        return portfolio_id
    
    def save_portfolio(self, portfolio_id: str):
        """Guardar definición del portafolio en disco"""
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portafolio {portfolio_id} no encontrado")
        
        portfolio = self.portfolios[portfolio_id]
        file_path = self.definitions_dir / f"{portfolio_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(portfolio), f, indent=4, ensure_ascii=False)
        
        logger.info(f"Portafolio guardado: {file_path}")
    
    def load_portfolio(self, portfolio_id: str) -> Optional[PortfolioDefinition]:
        """Cargar definición del portafolio desde disco"""
        file_path = self.definitions_dir / f"{portfolio_id}.json"
        
        if not file_path.exists():
            logger.warning(f"Archivo de portafolio no encontrado: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                portfolio = PortfolioDefinition(**data)
                self.portfolios[portfolio_id] = portfolio
                return portfolio
        except Exception as e:
            logger.error(f"Error cargando portafolio {portfolio_id}: {e}")
            return None
    
    def load_all_portfolios(self):
        """Cargar todos los portafolios desde disco"""
        if not self.definitions_dir.exists():
            return
        
        for file_path in self.definitions_dir.glob("*.json"):
            portfolio_id = file_path.stem
            self.load_portfolio(portfolio_id)
        
        logger.info(f"Cargados {len(self.portfolios)} portafolios")
    
    def get_active_portfolios(self) -> List[PortfolioDefinition]:
        """Obtener lista de portafolios activos"""
        return [p for p in self.portfolios.values() if p.status == "active"]
    
    def create_initial_snapshot(self, portfolio_id: str):
        """Crear snapshot inicial del portafolio"""
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portafolio {portfolio_id} no encontrado")
        
        portfolio = self.portfolios[portfolio_id]
        
        # Crear snapshot inicial con balance cero
        initial_positions = {}
        for symbol in portfolio.allocation.keys():
            initial_positions[symbol] = {
                "amount": 0.0,
                "value": 0.0,
                "weight": 0.0
            }
        
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            timestamp=datetime.now().isoformat(),
            total_value=portfolio.initial_balance,
            positions=initial_positions,
            cash_balance=portfolio.initial_balance,
            daily_pnl=0.0,
            total_pnl=0.0,
            metrics={}
        )
        
        self.save_snapshot(snapshot)
        logger.info(f"Snapshot inicial creado para {portfolio_id}")
    
    def save_snapshot(self, snapshot: PortfolioSnapshot):
        """Guardar snapshot del portafolio"""
        date_str = datetime.fromisoformat(snapshot.timestamp).strftime("%Y-%m-%d")
        snapshot_dir = self.performance_dir / "daily_snapshots" / date_str
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = snapshot_dir / f"{snapshot.portfolio_id}_snapshot.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, indent=4, ensure_ascii=False)
    
    def get_portfolio_summary(self) -> Dict:
        """Obtener resumen de todos los portafolios"""
        summary = {
            "total_portfolios": len(self.portfolios),
            "active_portfolios": len(self.get_active_portfolios()),
            "portfolios_by_type": {},
            "created_date": datetime.now().isoformat()
        }
        
        # Agrupar por tipo
        for portfolio in self.portfolios.values():
            portfolio_type = portfolio.type
            if portfolio_type not in summary["portfolios_by_type"]:
                summary["portfolios_by_type"][portfolio_type] = []
            
            summary["portfolios_by_type"][portfolio_type].append({
                "id": portfolio.id,
                "name": portfolio.name,
                "status": portfolio.status,
                "risk_tolerance": portfolio.risk_tolerance
            })
        
        return summary
    
    def export_portfolio_definitions(self, file_path: str = None):
        """Exportar todas las definiciones de portafolios"""
        if file_path is None:
            file_path = self.portfolios_dir / "all_portfolios_export.json"
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "portfolios": [asdict(p) for p in self.portfolios.values()]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Portafolios exportados a: {file_path}")
        return file_path

def test_portfolio_manager():
    """Función de prueba para el PortfolioManager"""
    pm = PortfolioManager()
    
    # Crear portafolio de prueba
    test_allocation = {
        "BTC": 0.4,
        "ETH": 0.3,
        "ADA": 0.2,
        "DOT": 0.1
    }
    
    portfolio_id = pm.create_portfolio(
        name="Test Conservative Portfolio",
        portfolio_type="conservative",
        allocation=test_allocation,
        description="Portafolio de prueba conservador",
        initial_balance=1000.0,
        risk_tolerance="low"
    )
    
    print(f"Portafolio creado: {portfolio_id}")
    print(f"Resumen: {pm.get_portfolio_summary()}")
    
    return portfolio_id

if __name__ == "__main__":
    test_portfolio_manager() 