# Configuración de APIs
import os
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno

API_KEYS = {
    'etherscan': '8AIIWK9Y3JAGK83D4RQBMG34DWAFYZS93B',
    'bscscan': 'ATSE5PJ3C3UFZPFJ3D5Q7SWPPHUAT8VKSY',
    'solscan': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzYzNjE1MTU2NDQsImVtYWlsIjoiZWxhcmFuZjIwMjVAcG0ubWUiLCJhY3Rpb24iOiJ0b2tlbi1hcGkiLCJhcGlWZXJzaW9uIjoidjIiLCJpYXQiOjE3MzYzNjE1MTV9.J7JkgHfD5iGBRsQMU47bDImR8tvLmqcQbCIhd352cRY',
    'coingecko': '',  # API pública
    'coinmarketcap': '7d306239-f647-4b67-8638-4b6f2e9fbae5',
    'deepseek': os.getenv('DEEPSEEK_API_KEY', '')  # Añadir DeepSeek API key
}

# URLs base de APIs
API_URLS = {
    'coingecko': 'https://api.coingecko.com/api/v3',
    'defillama': 'https://api.llama.fi',
    'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1',
    'deepseek': 'https://api.deepseek.com/v1'  # Añadir URL base de DeepSeek
}

# Endpoints de APIs
API_ENDPOINTS = {
    'etherscan': {
        'base_url': 'https://api.etherscan.io/api',
        'gas_oracle': '?module=gastracker&action=gasoracle',
        'latest_block': '?module=proxy&action=eth_blockNumber',
        'block_time': '?module=block&action=getblockreward',
        'validators': '?module=stats&action=validators',
        'block_by_number': '?module=proxy&action=eth_getBlockByNumber'
    },
    'bscscan': {
        'base_url': 'https://api.bscscan.com/api',
        'gas_oracle': '?module=gastracker&action=gasoracle',
        'latest_block': '?module=proxy&action=eth_blockNumber',
        'block_time': '?module=block&action=getblockreward',
        'validators': '?module=stats&action=validators',
        'block_by_number': '?module=proxy&action=eth_getBlockByNumber'
    },
    'solscan': {
        'base_url': 'https://public-api.solscan.io',
        'chain_info': '/chaininfo',
        'block': '/block',
        'latest_block': '/block/last',
        'blocks': '/blocks',
        'account': '/account',
        'token': '/token'
    },
    'defillama': {
        'base_url': 'https://api.llama.fi',
        'chains': '/chains',
        'protocol': '/protocol/{id}',
        'tvl': '/tvl/{chain}',
        'protocols': '/protocols',
        'protocol_tvl': '/protocol/{id}/tvl',
        'chain_tvl': '/chain/{chain}/tvl',
        'stablecoins': '/stablecoins',
        'bridges': '/bridges',
        'yields': '/yields'
    },
    'coinmarketcap': {
        'listings': '/cryptocurrency/listings/latest',
        'quotes': '/cryptocurrency/quotes/latest',
        'info': '/cryptocurrency/info',
        'global': '/global-metrics/quotes/latest',
        'categories': '/cryptocurrency/categories',
        'trending': '/cryptocurrency/trending/latest',
        'gainers_losers': '/cryptocurrency/trending/gainers-losers',
        'market_pairs': '/cryptocurrency/market-pairs/latest',
        'historical': '/cryptocurrency/quotes/historical',
        'ohlcv': '/cryptocurrency/ohlcv/historical'
    },
    'coingecko': {
        'coins_list': '/coins/list',
        'coins_markets': '/coins/markets',
        'coin_data': '/coins/{id}',
        'coin_tickers': '/coins/{id}/tickers',
        'coin_history': '/coins/{id}/history',
        'coin_market_chart': '/coins/{id}/market_chart',
        'coin_ohlc': '/coins/{id}/ohlc',
        'global': '/global',
        'global_defi': '/global/decentralized_finance_defi',
        'exchanges': '/exchanges',
        'exchange_rates': '/exchange_rates',
        'search': '/search',
        'trending': '/search/trending',
        'categories': '/coins/categories/list',
        'category': '/coins/markets?vs_currency={vs_currency}&category={category}',
        'derivatives': '/derivatives'
    }
}

# Configuración específica para cada API
COINGECKO_CONFIG = {
    'base_url': 'https://api.coingecko.com/api/v3',
    'api_key': '',  # Empty string for public API
    'endpoints': API_ENDPOINTS['coingecko'],
    'rate_limit': 50,  # calls per minute for public API
    'use_pro': False,  # Flag to indicate we're using public API
    'timeout': 30,     # Request timeout in seconds
    'retry_count': 3   # Number of retries for failed requests
}

DEFILLAMA_CONFIG = {
    'base_url': 'https://api.llama.fi',
    'endpoints': API_ENDPOINTS['defillama'],
    'rate_limit': 30,  # calls per minute
    'timeout': 30,
    'retry_count': 3
}

ETHERSCAN_CONFIG = {
    'base_url': 'https://api.etherscan.io/api',
    'modules': API_ENDPOINTS['etherscan'],
    'api_key': API_KEYS['etherscan'],
    'rate_limit': 5,  # calls per second
    'timeout': 30,
    'retry_count': 3
}

BSCSCAN_CONFIG = {
    'base_url': 'https://api.bscscan.com/api',
    'modules': API_ENDPOINTS['bscscan'],
    'api_key': API_KEYS['bscscan'],
    'rate_limit': 5,  # calls per second
    'timeout': 30,
    'retry_count': 3
}

SOLSCAN_CONFIG = {
    'base_url': 'https://public-api.solscan.io',
    'endpoints': API_ENDPOINTS['solscan'],
    'api_key': API_KEYS['solscan'],
    'rate_limit': 10,  # calls per second
    'timeout': 30,
    'retry_count': 3
}

# Configuración de análisis
MAIN_ASSETS = {
    'BTC': {'name': 'Bitcoin', 'category': 'Store of Value'},
    'ETH': {'name': 'Ethereum', 'category': 'Smart Contract Platform'},
    'BNB': {'name': 'BNB', 'category': 'Exchange Token'},
    'SOL': {'name': 'Solana', 'category': 'Smart Contract Platform'},
    'ADA': {'name': 'Cardano', 'category': 'Smart Contract Platform'}
}

ASSET_CATEGORIES = {
    'Store of Value': ['BTC'],
    'Smart Contract Platform': ['ETH', 'SOL', 'ADA'],
    'Exchange Token': ['BNB'],
    'DeFi': [],
    'Gaming': [],
    'Infrastructure': []
}

# Configuración de análisis técnico
TREND_ANALYSIS_PERIOD = 30  # días
CORRELATION_THRESHOLD = 0.7
VOLUME_RATIO_THRESHOLD = 2.0

# Configuración del reporte
REPORT_CONFIG = {
    'block_sample_size': {
        'ethereum': 100,
        'bsc': 100,
        'solana': 1440
    },
    'block_time_validation': {
        'ethereum': {'min_time': 10, 'max_time': 20},
        'bsc': {'min_time': 2, 'max_time': 5},
        'solana': {'min_time': 0.4, 'max_time': 1.0}
    }
}

# Configuración específica para DeepSeek
DEEPSEEK_CONFIG = {
    'base_url': API_URLS['deepseek'],
    'api_key': API_KEYS['deepseek'],
    'endpoints': {
        'symbols_top': '/symbols/top',
        'analysis': '/analysis',
        'market_overview': '/market/overview'
    },
    'rate_limit': 60,  # calls per minute
    'timeout': 30,
    'retry_count': 3
} 