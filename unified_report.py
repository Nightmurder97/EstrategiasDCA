import os

def combine_html_txt_reports():
    reports_dir = 'reports'
    html_report = ""
    txt_report = ""
    
    html_files = [
        f for f in os.listdir(reports_dir) if f.endswith('.html')
    ]
    
    txt_files = [
        f for f in os.listdir(reports_dir) if f.endswith('.txt')
    ]
    
    for filename in sorted(html_files):
        file_path = os.path.join(reports_dir, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            html_report += f"---\n\n## {filename[:-5]}\n\n"  # Elimina la extensión .html del título
            html_report += content + "\n\n"
    
    for filename in sorted(txt_files):
        file_path = os.path.join(reports_dir, filename)
        with open(file_path, 'r') as file:
            content = file.read()
            txt_report += f"---\n\n## {filename[:-4]}\n\n"  # Elimina la extensión .txt del título
            txt_report += content + "\n\n"
    
    return html_report, txt_report

def combine_reports():
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
    
    html_report, txt_report = combine_html_txt_reports()
    combined_report += html_report + txt_report
    
    with open(os.path.join(reports_dir, 'unified_report.md'), 'w') as outfile:
        outfile.write(combined_report)

if __name__ == "__main__":
    combine_reports()
