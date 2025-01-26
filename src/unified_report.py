import os

def combine_reports():
    """Combina todos los reportes markdown en un solo archivo."""
    reports_dir = 'reports'
    combined_report = "# Reporte Unificado\n\n"
    
    # Asegurarse de que el directorio reports existe
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    report_files = [
        f for f in os.listdir(reports_dir) if f.endswith('.md')
    ]
    
    for filename in sorted(report_files):
        file_path = os.path.join(reports_dir, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            combined_report += f"---\n\n## {filename[:-3]}\n\n"  # Elimina la extensión .md del título
            combined_report += content + "\n\n"
    
    with open(os.path.join(reports_dir, 'unified_report.md'), 'w') as outfile:
        outfile.write(combined_report)

if __name__ == "__main__":
    combine_reports() 