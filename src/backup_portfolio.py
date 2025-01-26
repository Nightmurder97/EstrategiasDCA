#!/usr/bin/env python3
import os
import shutil
from datetime import datetime
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioBackup:
    def __init__(self):
        self.base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.backup_dir = self.base_dir / 'backups'
        self.daily_dir = self.backup_dir / 'daily'
        self.weekly_dir = self.backup_dir / 'weekly'
        self._create_directories()

    def _create_directories(self):
        """Crear estructura de directorios si no existe"""
        for directory in [self.backup_dir, self.daily_dir, self.weekly_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _get_date_str(self):
        """Obtener string de fecha actual"""
        return datetime.now().strftime('%Y-%m-%d')

    def backup_daily_analysis(self):
        """Realizar backup diario de todos los archivos de análisis"""
        date_str = self._get_date_str()
        
        # Lista de archivos a respaldar
        files_to_backup = [
            'market_analysis_report.md',
            'unified_report.md',
            'portfolio_summary.csv',
            'recommendations.json',
            'recommendations.csv'
        ]

        # Crear directorio para el día actual
        daily_backup_dir = self.daily_dir / date_str
        daily_backup_dir.mkdir(exist_ok=True)

        # Crear directorio para imágenes
        images_backup_dir = daily_backup_dir / 'images'
        images_backup_dir.mkdir(exist_ok=True)

        try:
            # Backup de archivos principales
            for file in files_to_backup:
                if (self.base_dir / file).exists():
                    shutil.copy2(
                        self.base_dir / file,
                        daily_backup_dir / f"{file.split('.')[0]}_{date_str}.{file.split('.')[1]}"
                    )
                    logger.info(f"Backup realizado: {file}")

            # Backup de imágenes y gráficos
            images_dir = self.base_dir / 'images'
            if images_dir.exists():
                for image in images_dir.glob('*'):
                    if image.is_file():
                        shutil.copy2(
                            image,
                            images_backup_dir / f"{image.stem}_{date_str}{image.suffix}"
                        )
                        logger.info(f"Backup realizado: {image.name}")

            # Backup de métricas individuales
            for metric_file in self.base_dir.glob('*_metrics.csv'):
                shutil.copy2(
                    metric_file,
                    daily_backup_dir / f"{metric_file.stem}_{date_str}.csv"
                )
                logger.info(f"Backup realizado: {metric_file.name}")

            # Backup de gráficos HTML
            for html_file in self.base_dir.glob('*_radar.html'):
                shutil.copy2(
                    html_file,
                    daily_backup_dir / f"{html_file.stem}_{date_str}.html"
                )
                logger.info(f"Backup realizado: {html_file.name}")

            logger.info(f"Backup diario completado para {date_str}")
            return True

        except Exception as e:
            logger.error(f"Error durante el backup: {str(e)}")
            return False

    def cleanup_old_backups(self, days_to_keep=30):
        """Limpiar backups antiguos manteniendo solo los últimos N días"""
        try:
            all_backups = sorted(self.daily_dir.glob('*'))
            old_backups = all_backups[:-days_to_keep] if len(all_backups) > days_to_keep else []
            
            for backup in old_backups:
                if backup.is_dir():
                    shutil.rmtree(backup)
                    logger.info(f"Eliminado backup antiguo: {backup}")
            
            return True
        except Exception as e:
            logger.error(f"Error durante la limpieza de backups: {str(e)}")
            return False

def main():
    backup_system = PortfolioBackup()
    backup_system.backup_daily_analysis()
    backup_system.cleanup_old_backups()

if __name__ == "__main__":
    main() 