import os
import shutil
from datetime import datetime
import json

def create_backup():
    # Usar fecha fija: 06/01/2025
    current_date = datetime(2025, 1, 6)
    backup_dir = f"backup_dca_{current_date.strftime('%Y%m%d')}"
    
    # Crear la carpeta si no existe
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Lista de archivos a respaldar
    files_to_backup = [
        'dca_simulator_enhanced.py',
        'dca_optimizer.py',
        'dca_strategy.py',
        'portfolio_history.json',
        'allocation_heatmap.png',
        'portfolio_analysis.png',
        'gemini_training_data.csv',
        'gemini_tuning_data.jsonl',
        'requirements.txt'
    ]
    
    # Copiar cada archivo si existe
    backed_up_files = []
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))
            backed_up_files.append(file)
    
    # Crear un archivo de resumen
    summary = {
        'backup_date': current_date.strftime('%Y-%m-%d'),
        'backed_up_files': backed_up_files,
        'backup_directory': backup_dir,
        'simulation_date': '2025-01-06',
        'portfolio_summary': {
            'total_invested': 0,  # Se actualizará si existe portfolio_history.json
            'current_assets': []  # Se actualizará si existe portfolio_history.json
        }
    }
    
    # Si existe portfolio_history.json, agregar información al resumen
    portfolio_file = 'portfolio_history.json'
    if os.path.exists(portfolio_file):
        with open(portfolio_file, 'r') as f:
            portfolio_data = json.load(f)
            summary['portfolio_summary']['total_invested'] = portfolio_data.get('total_invested', 0)
            summary['portfolio_summary']['current_assets'] = list(portfolio_data.get('positions', {}).keys())
    
    # Guardar el resumen en la carpeta de backup
    with open(os.path.join(backup_dir, 'backup_summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)
    
    print(f"\nBackup creado en la carpeta: {backup_dir}")
    print(f"Fecha de simulación: {current_date.strftime('%d/%m/%Y')}")
    print(f"\nArchivos respaldados:")
    for file in backed_up_files:
        print(f"- {file}")
    
    if summary['portfolio_summary']['current_assets']:
        print(f"\nResumen del portafolio:")
        print(f"- Inversión total: {summary['portfolio_summary']['total_invested']:.2f}€")
        print(f"- Activos actuales: {', '.join(summary['portfolio_summary']['current_assets'])}")
    
    print("\nResumen guardado en backup_summary.json")

if __name__ == "__main__":
    create_backup() 