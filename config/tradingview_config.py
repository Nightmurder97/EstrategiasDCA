TRADINGVIEW_CONFIG = {
    'data_dir': 'TradingViewData',
    'required_files': [
        'Datostecnicos_{date}_{time}.csv',
        'Direcciones_{date}_{time}.csv',
        'Perdidas&ganancias_{date}_{time}.csv'
    ],
    'metrics': {
        'technical': ['RSI', 'Momentum', 'Rating técnico'],
        'fundamental': ['Capitalización de mercado', 'Volumen 24h'],
        'holders': ['Direcciones de beneficios %', 'Direcciones de pérdidas %']
    }
} 