import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from typing import Dict, Tuple

def load_portfolio_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Carga datos del portafolio y TradingView"""
    # Cargar portafolio actual
    portfolio_df = pd.read_csv('data/portfolio_consolidado.csv', 
                             comment='#', 
                             skipinitialspace=True)
    
    # Cargar datos de TradingView
    tecnicos_df = pd.read_csv('TradingViewData/Analizador de criptomonedas_2025-02-03-Datostecnicos.csv')
    direcciones_df = pd.read_csv('TradingViewData/Analizador de criptomonedas_2025-02-03-Direcciones.csv')
    pnl_df = pd.read_csv('TradingViewData/Analizador de criptomonedas_2025-02-03-PerdidasyGanancias.csv')
    
    # Combinar datos de TradingView
    metrics_df = pd.merge(tecnicos_df, direcciones_df[['Moneda', 'Capitalización de mercado']], 
                         on='Moneda', how='left')
    metrics_df = pd.merge(metrics_df, pnl_df[['Moneda', 'Direcciones de beneficios %']], 
                         on='Moneda', how='left')
    
    return portfolio_df, metrics_df

def clean_numeric_string(value):
    """Limpia y convierte strings numéricos"""
    if pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return value
    try:
        # Eliminar caracteres no numéricos excepto punto y coma
        clean_str = ''.join(c for c in str(value) if c.isdigit() or c in '.,')
        # Reemplazar coma por punto si hay coma
        clean_str = clean_str.replace(',', '')
        return float(clean_str)
    except:
        return 0

def analyze_portfolio(portfolio_df: pd.DataFrame, metrics_df: pd.DataFrame) -> Dict:
    """Analiza el portafolio y genera métricas"""
    try:
        # Preparar datos
        portfolio = portfolio_df.copy()
        portfolio['Moneda'] = portfolio['Moneda'].str.upper()
        
        # Limpiar y calcular market cap
        metrics_df['market_cap_clean'] = metrics_df['Capitalización de mercado'].apply(clean_numeric_string)
        
        # Merge con métricas
        analysis = pd.merge(portfolio, metrics_df, 
                          left_on='Moneda', 
                          right_on='Moneda', 
                          how='left')
        
        # Limpiar datos numéricos
        analysis['rsi'] = pd.to_numeric(analysis['Índice de fuerza relativa (14) 1 día'], errors='coerce')
        analysis['profit_ratio'] = pd.to_numeric(analysis['Direcciones de beneficios %'], errors='coerce')
        
        # Calcular valor en USD (simulado para ejemplo)
        analysis['valor_usd'] = analysis['Cantidad'] * 1  # Aquí deberías multiplicar por el precio real
        
        # Calcular métricas
        metrics = {
            'total_assets': int(len(portfolio)),
            'assets_with_data': int(analysis['Rating técnico 1 día'].notna().sum()),
            'buy_signals': int(analysis['Rating técnico 1 día'].str.contains('Compra', na=False).sum()),
            'sell_signals': int(analysis['Rating técnico 1 día'].str.contains('Venta', na=False).sum()),
            'avg_rsi': float(analysis['rsi'].mean()),
            'high_rsi': [str(x) for x in analysis[analysis['rsi'] > 70]['Moneda'].tolist()],
            'low_rsi': [str(x) for x in analysis[analysis['rsi'] < 30]['Moneda'].tolist()]
        }
        
        return analysis, metrics
        
    except Exception as e:
        print(f"Error en analyze_portfolio: {str(e)}")
        raise

def plot_portfolio_comparison(portfolio_df: pd.DataFrame, metrics_df: pd.DataFrame, analysis_df: pd.DataFrame):
    """Genera visualizaciones comparando portafolio personal con datos de TradingView"""
    try:
        os.makedirs('analisis/graficos', exist_ok=True)
        
        # Configuración de estilo
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams.update({
            'font.size': 12,
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12
        })
        
        # 1. Tu Portafolio Personal
        fig, axes = plt.subplots(2, 2, figsize=(20, 15))
        fig.suptitle('Análisis de Tu Portafolio Personal', fontsize=20, y=1.02)
        
        # Top 10 Holdings por cantidad
        top_holdings = portfolio_df.nlargest(10, 'Cantidad')
        axes[0,0].pie(top_holdings['Cantidad'], 
                     labels=top_holdings['Moneda'], 
                     autopct='%1.1f%%')
        axes[0,0].set_title('Top 10 Holdings por Cantidad')
        
        # Comparar con métricas de TradingView
        your_assets = set(portfolio_df['Moneda'].str.upper())
        tradingview_data = metrics_df[metrics_df['Moneda'].isin(your_assets)].copy()
        
        # RSI de tus activos
        rsi_data = pd.to_numeric(tradingview_data['Índice de fuerza relativa (14) 1 día'], errors='coerce')
        axes[0,1].hist(rsi_data, bins=20, color='skyblue')
        axes[0,1].axvline(x=30, color='green', linestyle='--', label='Sobreventa')
        axes[0,1].axvline(x=70, color='red', linestyle='--', label='Sobrecompra')
        axes[0,1].set_title('RSI de Tus Activos')
        axes[0,1].legend()
        
        # Señales técnicas de tus activos
        signals = tradingview_data['Rating técnico 1 día'].value_counts()
        axes[1,0].pie(signals.values, labels=signals.index, autopct='%1.1f%%',
                     colors=['green', 'red', 'gray', 'lightgreen', 'lightcoral'])
        axes[1,0].set_title('Señales Técnicas de Tus Activos')
        
        # Ratio de beneficios de tus activos
        profit_data = pd.to_numeric(tradingview_data['Direcciones de beneficios %'], errors='coerce')
        axes[1,1].hist(profit_data, bins=20, color='lightgreen')
        axes[1,1].axvline(x=50, color='red', linestyle='--', label='Mínimo Requerido')
        axes[1,1].set_title('Ratio de Beneficios de Tus Activos')
        axes[1,1].legend()
        
        plt.tight_layout()
        plt.savefig('analisis/graficos/tu_portfolio_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Comparación con Mercado General
        fig, axes = plt.subplots(2, 2, figsize=(20, 15))
        fig.suptitle('Comparación con Mercado General', fontsize=20, y=1.02)
        
        # RSI: Tus activos vs Mercado
        axes[0,0].hist(rsi_data, bins=20, alpha=0.5, label='Tu Portafolio', color='blue')
        market_rsi = pd.to_numeric(metrics_df['Índice de fuerza relativa (14) 1 día'], errors='coerce')
        axes[0,0].hist(market_rsi, bins=20, alpha=0.5, label='Mercado General', color='gray')
        axes[0,0].set_title('RSI: Tu Portafolio vs Mercado')
        axes[0,0].legend()
        
        # Ratio de Beneficios: Comparación
        axes[0,1].hist(profit_data, bins=20, alpha=0.5, label='Tu Portafolio', color='green')
        market_profit = pd.to_numeric(metrics_df['Direcciones de beneficios %'], errors='coerce')
        axes[0,1].hist(market_profit, bins=20, alpha=0.5, label='Mercado General', color='gray')
        axes[0,1].set_title('Ratio de Beneficios: Comparación')
        axes[0,1].legend()
        
        # Top 10 por Cantidad en tu portafolio
        top_10 = portfolio_df.nlargest(10, 'Cantidad')
        axes[1,0].barh(top_10['Moneda'], top_10['Cantidad'])
        axes[1,0].set_title('Top 10 por Cantidad en Tu Portafolio')
        
        # Distribución de Señales
        your_signals = tradingview_data['Rating técnico 1 día'].value_counts()
        market_signals = metrics_df['Rating técnico 1 día'].value_counts()
        
        width = 0.35
        axes[1,1].bar(np.arange(len(your_signals)) - width/2, your_signals.values, 
                     width, label='Tu Portafolio')
        axes[1,1].bar(np.arange(len(market_signals)) + width/2, market_signals.values, 
                     width, label='Mercado General')
        axes[1,1].set_xticks(np.arange(len(market_signals)))
        axes[1,1].set_xticklabels(market_signals.index, rotation=45)
        axes[1,1].set_title('Distribución de Señales: Comparación')
        axes[1,1].legend()
        
        plt.tight_layout()
        plt.savefig('analisis/graficos/mercado_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        print(f"Error en plot_portfolio_comparison: {str(e)}")
        raise

def main():
    try:
        # Cargar datos
        portfolio_df, metrics_df = load_portfolio_data()
        
        # Analizar portafolio
        analysis_df, metrics = analyze_portfolio(portfolio_df, metrics_df)
        
        # Generar visualizaciones comparativas
        plot_portfolio_comparison(portfolio_df, metrics_df, analysis_df)
        
        print("Análisis completado. Revisa los archivos generados:")
        print("1. analisis/graficos/tu_portfolio_analysis.png - Tu portafolio personal")
        print("2. analisis/graficos/mercado_comparison.png - Comparación con el mercado")
        
    except Exception as e:
        print(f"Error durante el análisis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 