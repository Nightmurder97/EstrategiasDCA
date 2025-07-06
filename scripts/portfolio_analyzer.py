import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from typing import Dict, Tuple
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def analyze_specific_coins(portfolio_df: pd.DataFrame, metrics_df: pd.DataFrame):
    """Analiza específicamente criptomonedas de interés"""
    coins_of_interest = ['XRP', 'XLM', 'ONDO', 'SUI', 'ADA']
    
    # Obtener datos de estas monedas
    specific_analysis = metrics_df[metrics_df['Moneda'].isin(coins_of_interest)].copy()
    
    # Limpiar y preparar datos
    specific_analysis['rsi'] = pd.to_numeric(specific_analysis['Índice de fuerza relativa (14) 1 día'], errors='coerce')
    specific_analysis['profit_ratio'] = pd.to_numeric(specific_analysis['Direcciones de beneficios %'], errors='coerce')
    specific_analysis['market_cap_clean'] = specific_analysis['Capitalización de mercado'].apply(clean_numeric_string)
    
    # Crear visualización específica
    plt.figure(figsize=(15, 10))
    
    # 1. RSI y Señales Técnicas
    plt.subplot(2, 1, 1)
    bars = plt.bar(specific_analysis['Moneda'], specific_analysis['rsi'])
    
    # Colorear barras según señal técnica
    colors = {
        'Compra fuerte': 'darkgreen',
        'Comprar': 'lightgreen',
        'Neutral': 'gray',
        'Vender': 'salmon',
        'Venta fuerte': 'red'
    }
    
    for bar, signal in zip(bars, specific_analysis['Rating técnico 1 día']):
        bar.set_color(colors.get(signal, 'blue'))
    
    plt.axhline(y=70, color='r', linestyle='--', label='Sobrecompra')
    plt.axhline(y=30, color='g', linestyle='--', label='Sobreventa')
    plt.title('RSI y Señales Técnicas de Proyectos Seleccionados')
    plt.legend()
    
    # 2. Ratio de Beneficios y Market Cap
    plt.subplot(2, 1, 2)
    x = np.arange(len(specific_analysis))
    width = 0.35
    
    plt.bar(x - width/2, specific_analysis['profit_ratio'], 
           width, label='Ratio de Beneficios (%)', color='green', alpha=0.6)
    plt.bar(x + width/2, specific_analysis['market_cap_clean'] / 1e9, 
           width, label='Market Cap (B)', color='blue', alpha=0.6)
    
    plt.xticks(x, specific_analysis['Moneda'])
    plt.title('Métricas Fundamentales')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('analisis/graficos/analisis_proyectos_especificos.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # Generar reporte detallado
    report = {
        'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'proyectos_analizados': {}
    }
    
    for _, row in specific_analysis.iterrows():
        report['proyectos_analizados'][row['Moneda']] = {
            'rsi': float(row['rsi']),
            'señal_tecnica': row['Rating técnico 1 día'],
            'ratio_beneficios': float(row['profit_ratio']),
            'market_cap_usd': float(row['market_cap_clean']),
            'recomendacion': 'Comprar' if (
                30 <= float(row['rsi']) <= 70 and 
                row['profit_ratio'] > 50 and 
                'Compra' in str(row['Rating técnico 1 día'])
            ) else 'Monitorear'
        }
    
    # Guardar reporte
    with open('analisis/graficos/analisis_proyectos_especificos.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    return report

def analyze_popular_coins(metrics_df: pd.DataFrame):
    """Analiza las criptomonedas más populares y compara con recomendaciones actuales"""
    # Lista de criptomonedas populares
    popular_coins = [
        'BTC', 'ETH', 'BNB', 'XRP', 'SOL',  # Top por Market Cap
        'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC',  # DeFi/Smart Contracts
        'DOGE', 'SHIB', 'PEPE',  # Memecoins
        'UNI', 'AAVE', 'CRV',  # DeFi Blue Chips
        'OP', 'ARB', 'MATIC',  # L2s
        'SUI', 'APT', 'SEI'  # Nuevos L1s
    ]
    
    # Obtener datos
    popular_analysis = metrics_df[metrics_df['Moneda'].isin(popular_coins)].copy()
    
    # Limpiar datos
    popular_analysis['rsi'] = pd.to_numeric(popular_analysis['Índice de fuerza relativa (14) 1 día'], errors='coerce')
    popular_analysis['profit_ratio'] = pd.to_numeric(popular_analysis['Direcciones de beneficios %'], errors='coerce')
    popular_analysis['market_cap_clean'] = popular_analysis['Capitalización de mercado'].apply(clean_numeric_string)
    
    # Crear visualización
    plt.figure(figsize=(20, 15))
    
    # 1. RSI y Señales Técnicas
    plt.subplot(2, 1, 1)
    bars = plt.bar(popular_analysis['Moneda'], popular_analysis['rsi'])
    
    colors = {
        'Compra fuerte': 'darkgreen',
        'Comprar': 'lightgreen',
        'Neutral': 'gray',
        'Vender': 'salmon',
        'Venta fuerte': 'red'
    }
    
    for bar, signal in zip(bars, popular_analysis['Rating técnico 1 día']):
        bar.set_color(colors.get(signal, 'blue'))
        
    plt.axhline(y=70, color='r', linestyle='--', label='Sobrecompra')
    plt.axhline(y=30, color='g', linestyle='--', label='Sobreventa')
    plt.title('RSI y Señales Técnicas de Criptomonedas Populares')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    
    # 2. Ratio de Beneficios vs Market Cap
    plt.subplot(2, 1, 2)
    
    # Crear scatter plot
    plt.scatter(popular_analysis['market_cap_clean'] / 1e9, 
               popular_analysis['profit_ratio'],
               alpha=0.6, 
               s=100)
    
    # Añadir etiquetas para cada punto
    for idx, row in popular_analysis.iterrows():
        plt.annotate(row['Moneda'], 
                    (row['market_cap_clean'] / 1e9, row['profit_ratio']),
                    xytext=(5, 5), textcoords='offset points')
    
    plt.xlabel('Market Cap (Billones USD)')
    plt.ylabel('Ratio de Beneficios (%)')
    plt.title('Market Cap vs Ratio de Beneficios')
    
    plt.tight_layout()
    plt.savefig('analisis/graficos/analisis_populares.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Generar reporte detallado
    report = {
        'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'criptos_populares': {},
        'resumen': {
            'mejor_rsi': '',
            'mejor_beneficio': '',
            'mejor_tecnico': '',
            'recomendaciones': []
        }
    }
    
    # Analizar cada cripto
    for _, row in popular_analysis.iterrows():
        coin_data = {
            'rsi': float(row['rsi']),
            'señal_tecnica': row['Rating técnico 1 día'],
            'ratio_beneficios': float(row['profit_ratio']),
            'market_cap_usd': float(row['market_cap_clean']),
            'momentum': row['Momentum (10) 1 día'],
            'recomendacion': 'Comprar' if (
                30 <= float(row['rsi']) <= 70 and 
                row['profit_ratio'] > 50 and 
                'Compra' in str(row['Rating técnico 1 día'])
            ) else 'Monitorear'
        }
        
        report['criptos_populares'][row['Moneda']] = coin_data
        
        # Añadir a recomendaciones si cumple criterios
        if coin_data['recomendacion'] == 'Comprar':
            report['resumen']['recomendaciones'].append(row['Moneda'])
    
    # Encontrar mejores métricas
    best_rsi = min(popular_analysis.iterrows(), key=lambda x: abs(x[1]['rsi'] - 50))
    best_profit = max(popular_analysis.iterrows(), key=lambda x: x[1]['profit_ratio'])
    best_tech = popular_analysis[popular_analysis['Rating técnico 1 día'].str.contains('Compra fuerte', na=False)]
    
    report['resumen']['mejor_rsi'] = best_rsi[1]['Moneda']
    report['resumen']['mejor_beneficio'] = best_profit[1]['Moneda']
    report['resumen']['mejores_tecnicos'] = best_tech['Moneda'].tolist()
    
    # Guardar reporte
    with open('analisis/graficos/analisis_populares.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    return report

def normalize_trading_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza los pares de trading para consistencia"""
    try:
        # Crear una copia del DataFrame
        df_normalized = df.copy()
        
        # Normalizar la columna 'Pair' reemplazando tanto '-' como '/' por '/'
        df_normalized['Pair'] = df_normalized['Pair'].str.replace('-', '/')
        
        # Asegurarse de que todos los pares terminen en USDT o USDC
        def normalize_quote(pair):
            if pair.endswith(('USDT', 'USDC', 'EUR')):
                return pair
            else:
                return pair + 'USDT'
        
        df_normalized['Pair'] = df_normalized['Pair'].apply(normalize_quote)
        
        logger.info("Pares normalizados correctamente")
        return df_normalized
        
    except Exception as e:
        logger.error(f"Error normalizando pares: {str(e)}")
        return df

def analyze_trading_pair(transactions_df: pd.DataFrame, pair: str) -> Dict:
    """Analiza un par de trading específico"""
    try:
        # Filtrar transacciones del par
        pair_df = transactions_df[transactions_df['Pair'] == pair].copy()
        
        # Convertir columnas a números, reemplazando comas por puntos
        pair_df['Amount'] = pair_df['Amount'].astype(str).str.replace(',', '.').astype(float)
        pair_df['Price'] = pair_df['Price'].astype(str).str.replace(',', '.').astype(float)
        pair_df['Fee'] = pair_df['Fee'].astype(str).str.replace(',', '.').astype(float)
        
        # Separar compras y ventas
        buys = pair_df[pair_df['Type'] == 'BUY']
        sells = pair_df[pair_df['Type'] == 'SELL']
        
        # Calcular métricas
        metrics = {
            'par': pair,
            'compras': {
                'cantidad_total': float(buys['Amount'].sum()),
                'importe_total': float((buys['Amount'] * buys['Price']).sum()),
                'precio_promedio': float((buys['Amount'] * buys['Price']).sum() / buys['Amount'].sum()) if not buys.empty else 0
            },
            'ventas': {
                'cantidad_total': float(sells['Amount'].sum()),
                'importe_total': float((sells['Amount'] * sells['Price']).sum()),
                'precio_promedio': float((sells['Amount'] * sells['Price']).sum() / sells['Amount'].sum()) if not sells.empty else 0
            },
            'posicion': {
                'cantidad': float(buys['Amount'].sum() - sells['Amount'].sum()),
                'coste_total': float((buys['Amount'] * buys['Price']).sum() - (sells['Amount'] * sells['Price']).sum())
            },
            'comisiones': {
                'total': float(pair_df['Fee'].sum()),
                'moneda_fee': str(pair_df['Fee'].iloc[-1]) if not pair_df.empty else None
            }
        }
        
        # Calcular precio medio por posición
        if metrics['posicion']['cantidad'] > 0:
            metrics['posicion']['coste_medio'] = float(metrics['posicion']['coste_total'] / metrics['posicion']['cantidad'])
        else:
            metrics['posicion']['coste_medio'] = 0
            
        # Calcular PnL realizado
        if not sells.empty:
            precio_venta_promedio = metrics['ventas']['precio_promedio']
            cantidad_vendida = metrics['ventas']['cantidad_total']
            coste_promedio_compra = metrics['compras']['precio_promedio']
            
            pnl_realizado = float((precio_venta_promedio - coste_promedio_compra) * cantidad_vendida)
            metrics['pnl_realizado'] = pnl_realizado
        else:
            metrics['pnl_realizado'] = 0
            
        # Calcular último precio y PnL no realizado
        ultima_transaccion = pair_df.iloc[-1]
        ultimo_precio = float(ultima_transaccion['Price'])
        
        if metrics['posicion']['cantidad'] > 0:
            pnl_no_realizado = float((ultimo_precio - metrics['posicion']['coste_medio']) * metrics['posicion']['cantidad'])
            metrics['pnl_no_realizado'] = pnl_no_realizado
        else:
            metrics['pnl_no_realizado'] = 0
            
        return metrics
        
    except Exception as e:
        logger.error(f"Error analizando par {pair}: {str(e)}")
        return None

def analyze_portfolio_transactions(transactions_file: str) -> Dict:
    """Analiza todas las transacciones del portafolio"""
    try:
        # Leer archivo de transacciones
        df = pd.read_csv(transactions_file, delimiter=';', decimal=',')
        
        # Convertir fecha a datetime
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y %H:%M')
        
        # Normalizar pares de trading
        df = normalize_trading_pairs(df)
        
        # Obtener pares únicos
        pares = df['Pair'].unique()
        
        # Analizar cada par
        portfolio_analysis = {}
        total_portfolio_value = 0
        total_pnl_realized = 0
        total_pnl_unrealized = 0
        
        for par in pares:
            metrics = analyze_trading_pair(df, par)
            if metrics:
                portfolio_analysis[par] = metrics
                if metrics['posicion']['cantidad'] > 0:
                    total_portfolio_value += metrics['posicion']['coste_total']
                total_pnl_realized += metrics['pnl_realizado']
                total_pnl_unrealized += metrics['pnl_no_realizado']
        
        # Crear resumen
        analysis_output = {
            'fecha_analisis': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'portfolio_analysis': portfolio_analysis,
            'resumen': {
                'valor_total': float(total_portfolio_value),
                'pnl_realizado_total': float(total_pnl_realized),
                'pnl_no_realizado_total': float(total_pnl_unrealized),
                'pnl_total': float(total_pnl_realized + total_pnl_unrealized)
            }
        }
        
        return analysis_output
        
    except Exception as e:
        logger.error(f"Error analizando transacciones: {str(e)}")
        return None

def export_to_excel(portfolio_analysis: Dict) -> None:
    """Exporta el análisis del portafolio a Excel"""
    try:
        # Crear DataFrame para el análisis detallado
        detailed_data = []
        
        for par, metricas in portfolio_analysis['portfolio_analysis'].items():
            # Asegurar que todos los valores numéricos sean float
            data = {
                'Par': par,
                # Compras
                'Cantidad Total Comprada': float(metricas['compras']['cantidad_total']),
                'Importe Total Compras': float(metricas['compras']['importe_total']),
                'Precio Promedio Compra': float(metricas['compras']['precio_promedio']),
                # Ventas
                'Cantidad Total Vendida': float(metricas['ventas']['cantidad_total']),
                'Importe Total Ventas': float(metricas['ventas']['importe_total']),
                'Precio Promedio Venta': float(metricas['ventas']['precio_promedio']),
                # Posición
                'Cantidad Actual': float(metricas['posicion']['cantidad']),
                'Coste Total': float(metricas['posicion']['coste_total']),
                'Coste Medio': float(metricas['posicion']['coste_medio']),
                # PnL
                'PnL Realizado': float(metricas['pnl_realizado']),
                'PnL No Realizado': float(metricas['pnl_no_realizado']),
                'PnL Total': float(metricas['pnl_realizado'] + metricas['pnl_no_realizado']),
                # Comisiones
                'Comisiones Total': float(metricas['comisiones']['total']),
                'Moneda Comisión': metricas['comisiones']['moneda_fee']
            }
            detailed_data.append(data)
        
        # Crear DataFrame y convertir columnas numéricas
        df_detailed = pd.DataFrame(detailed_data)
        numeric_columns = df_detailed.columns.drop(['Par', 'Moneda Comisión'])
        for col in numeric_columns:
            df_detailed[col] = pd.to_numeric(df_detailed[col], errors='coerce')
        
        # Crear Excel writer
        excel_path = 'analisis/graficos/portfolio_analysis.xlsx'
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # Hoja 1: Análisis Detallado
            df_detailed.to_excel(writer, sheet_name='Análisis Detallado', index=False)
            
            # Hoja 2: Resumen
            resumen_data = {
                'Métrica': [
                    'Valor Total Portfolio',
                    'PnL Realizado Total',
                    'PnL No Realizado Total',
                    'PnL Total'
                ],
                'Valor': [
                    float(portfolio_analysis['resumen']['valor_total']),
                    float(portfolio_analysis['resumen']['pnl_realizado_total']),
                    float(portfolio_analysis['resumen']['pnl_no_realizado_total']),
                    float(portfolio_analysis['resumen']['pnl_total'])
                ]
            }
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Dar formato al Excel
            workbook = writer.book
            
            # Formato para números
            num_format = workbook.add_format({
                'num_format': '#,##0.00000000',
                'align': 'right'
            })
            money_format = workbook.add_format({
                'num_format': '#,##0.00 USDT',
                'align': 'right'
            })
            
            # Aplicar formatos a la hoja de análisis detallado
            worksheet = writer.sheets['Análisis Detallado']
            worksheet.set_column('A:A', 15)  # Par
            worksheet.set_column('B:C', 20, num_format)  # Cantidades
            worksheet.set_column('D:E', 20, money_format)  # Importes
            worksheet.set_column('F:G', 20, num_format)  # Precios promedio
            worksheet.set_column('H:J', 20, money_format)  # Costes
            worksheet.set_column('K:M', 20, money_format)  # PnL
            worksheet.set_column('N:N', 20, num_format)  # Comisiones
            worksheet.set_column('O:O', 15)  # Moneda Comisión
            
            # Aplicar formatos a la hoja de resumen
            worksheet_resumen = writer.sheets['Resumen']
            worksheet_resumen.set_column('A:A', 25)
            worksheet_resumen.set_column('B:B', 20, money_format)
        
        print(f"\nAnálisis exportado a Excel: {excel_path}")
        
    except Exception as e:
        logger.error(f"Error exportando a Excel: {str(e)}")
        raise

def main():
    try:
        # 1. Analizar transacciones del portafolio
        transactions_file = 'Portafolio _personal/data_actualizada_binance_kucoin'
        portfolio_analysis = analyze_portfolio_transactions(transactions_file)
        
        print("\nAnálisis de Portafolio por Par:")
        print("=" * 50)
        
        total_portfolio_value = 0
        total_pnl_realized = 0
        total_pnl_unrealized = 0
        
        for par, metricas in portfolio_analysis['portfolio_analysis'].items():
            print(f"\n{par}:")
            print("-" * 30)
            
            print("Compras:")
            print(f"  Cantidad total: {metricas['compras']['cantidad_total']:.8f}")
            print(f"  Importe total: {metricas['compras']['importe_total']:.2f} USDT")
            print(f"  Precio promedio: {metricas['compras']['precio_promedio']:.8f} USDT")
            
            print("\nVentas:")
            print(f"  Cantidad total: {metricas['ventas']['cantidad_total']:.8f}")
            print(f"  Importe total: {metricas['ventas']['importe_total']:.2f} USDT")
            print(f"  Precio promedio: {metricas['ventas']['precio_promedio']:.8f} USDT")
            
            print("\nPosición Actual:")
            print(f"  Cantidad: {metricas['posicion']['cantidad']:.8f}")
            print(f"  Coste total: {metricas['posicion']['coste_total']:.2f} USDT")
            print(f"  Coste medio: {metricas['posicion']['coste_medio']:.8f} USDT")
            
            print("\nPnL:")
            print(f"  Realizado: {metricas['pnl_realizado']:.2f} USDT")
            print(f"  No realizado: {metricas['pnl_no_realizado']:.2f} USDT")
            
            print("\nComisiones:")
            print(f"  Total: {metricas['comisiones']['total']:.8f}")
            print(f"  Moneda: {metricas['comisiones']['moneda_fee']}")
            
            # Actualizar totales
            if metricas['posicion']['cantidad'] > 0:
                total_portfolio_value += metricas['posicion']['coste_total']
            total_pnl_realized += metricas['pnl_realizado']
            total_pnl_unrealized += metricas['pnl_no_realizado']
        
        print("\nResumen Total del Portafolio:")
        print("=" * 50)
        print(f"Valor Total: {total_portfolio_value:.2f} USDT")
        print(f"PnL Realizado Total: {total_pnl_realized:.2f} USDT")
        print(f"PnL No Realizado Total: {total_pnl_unrealized:.2f} USDT")
        print(f"PnL Total: {(total_pnl_realized + total_pnl_unrealized):.2f} USDT")
        
        # Guardar análisis en JSON
        analysis_output = {
            'fecha_analisis': portfolio_analysis['fecha_analisis'],
            'portfolio_analysis': portfolio_analysis['portfolio_analysis'],
            'resumen': {
                'valor_total': float(total_portfolio_value),
                'pnl_realizado_total': float(total_pnl_realized),
                'pnl_no_realizado_total': float(total_pnl_unrealized),
                'pnl_total': float(total_pnl_realized + total_pnl_unrealized)
            }
        }
        
        # Exportar a JSON
        with open('analisis/graficos/portfolio_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_output, f, indent=4, ensure_ascii=False)
        
        # Exportar a Excel
        export_to_excel(analysis_output)
            
        print("\nAnálisis guardado en:")
        print("- 'analisis/graficos/portfolio_analysis.json'")
        print("- 'analisis/graficos/portfolio_analysis.xlsx'")
        
    except Exception as e:
        print(f"Error durante el análisis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 