import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time
import psutil
import numpy as np
from dataclasses import dataclass
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    execution_time: float
    success_rate: float

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            'execution_times': [],
            'cpu_usage': [],
            'memory_usage': [],
            'success_rates': []
        }
        self.operation_times: Dict[str, float] = {}
        self.alerts: List[str] = []
        self.start_times: Dict[str, float] = {}
        
    def start_operation(self, operation_name: str):
        """Inicia el cronómetro para una operación"""
        self.start_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str):
        """Finaliza el cronómetro y registra el tiempo de ejecución"""
        if operation_name in self.start_times:
            duration = time.time() - self.start_times[operation_name]
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            self.operation_times[operation_name].append(duration)
            logger.info(f"Operación {operation_name} completada en {duration:.2f} segundos")
    
    def track_system_metrics(self) -> PerformanceMetrics:
        """Registra métricas del sistema"""
        try:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.metrics['cpu_usage'].append(cpu)
            self.metrics['memory_usage'].append(memory)
            
            # Calcular tasa de éxito (últimas 100 operaciones)
            success_rate = self._calculate_success_rate()
            
            # Calcular tiempo medio de ejecución
            execution_time = np.mean(self.metrics['execution_times'][-100:]) if self.metrics['execution_times'] else 0
            
            return PerformanceMetrics(
                cpu_usage=cpu,
                memory_usage=memory,
                disk_usage=disk,
                execution_time=execution_time,
                success_rate=success_rate
            )
        except Exception as e:
            logger.error(f"Error tracking system metrics: {str(e)}")
            return PerformanceMetrics(0, 0, 0, 0, 0)
    
    def _calculate_success_rate(self) -> float:
        """Calcula la tasa de éxito de las operaciones"""
        if not self.metrics['success_rates']:
            return 100.0
        recent_rates = self.metrics['success_rates'][-100:]
        return sum(recent_rates) / len(recent_rates) if recent_rates else 0
    
    def check_performance(self) -> List[str]:
        """Verifica el rendimiento y genera alertas si es necesario"""
        alerts = []
        try:
            metrics = self.track_system_metrics()
            
            # Verificar uso de CPU
            if metrics.cpu_usage > 80:
                alerts.append(f"Alto uso de CPU: {metrics.cpu_usage}%")
            
            # Verificar uso de memoria
            if metrics.memory_usage > 80:
                alerts.append(f"Alto uso de memoria: {metrics.memory_usage}%")
            
            # Verificar uso de disco
            if metrics.disk_usage > 80:
                alerts.append(f"Alto uso de disco: {metrics.disk_usage}%")
            
            # Verificar tiempos de ejecución
            for operation, times in self.operation_times.items():
                if len(times) > 1:
                    avg_time = np.mean(times)
                    last_time = times[-1]
                    if last_time > avg_time * 2:
                        alerts.append(
                            f"Tiempo de ejecución anormal en {operation}: "
                            f"{last_time:.2f}s vs promedio {avg_time:.2f}s"
                        )
            
            # Verificar tasa de éxito
            if metrics.success_rate < 95:
                alerts.append(f"Baja tasa de éxito: {metrics.success_rate:.2f}%")
            
            self.alerts = alerts
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking performance: {str(e)}")
            return ["Error al verificar rendimiento"]
    
    def generate_performance_report(self) -> str:
        """Genera un reporte de rendimiento en formato markdown"""
        try:
            metrics = self.track_system_metrics()
            
            report = "# Reporte de Rendimiento del Sistema\n\n"
            report += f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            report += "## Métricas del Sistema\n"
            report += f"* CPU: {metrics.cpu_usage:.1f}%\n"
            report += f"* Memoria: {metrics.memory_usage:.1f}%\n"
            report += f"* Disco: {metrics.disk_usage:.1f}%\n"
            report += f"* Tasa de Éxito: {metrics.success_rate:.1f}%\n\n"
            
            report += "## Tiempos de Ejecución\n"
            for operation, times in self.operation_times.items():
                if times:
                    avg_time = np.mean(times)
                    max_time = np.max(times)
                    min_time = np.min(times)
                    report += f"### {operation}\n"
                    report += f"* Promedio: {avg_time:.2f}s\n"
                    report += f"* Máximo: {max_time:.2f}s\n"
                    report += f"* Mínimo: {min_time:.2f}s\n\n"
            
            if self.alerts:
                report += "## Alertas Activas\n"
                for alert in self.alerts:
                    report += f"* {alert}\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return "Error al generar reporte de rendimiento"
    
    def save_metrics(self, filename: str = 'performance_metrics.json'):
        """Guarda las métricas en un archivo JSON"""
        try:
            metrics_dict = {
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics,
                'operation_times': self.operation_times,
                'alerts': self.alerts
            }
            
            with open(filename, 'w') as f:
                json.dump(metrics_dict, f, indent=2)
                
            logger.info(f"Métricas guardadas en {filename}")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
    
    def load_metrics(self, filename: str = 'performance_metrics.json'):
        """Carga métricas desde un archivo JSON"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self.metrics = data['metrics']
            self.operation_times = data['operation_times']
            self.alerts = data['alerts']
            
            logger.info(f"Métricas cargadas desde {filename}")
            
        except Exception as e:
            logger.error(f"Error loading metrics: {str(e)}") 