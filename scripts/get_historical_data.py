from binance.client import Client
import pandas as pd
import os

# Initialize Binance client
api_key = 'Tro2UZTWPSwkV7v5RJvnOg3qJ9FSrrrW9BH8G4Qn0IumJGdM9LV73T1wF69h4PeA'
api_secret = 'J5wpTFzo86NmljBUeOvBwYwLiAPlzFTwIRgfrErbhCIpu2C1yvCDpY83kmNPD243'
client = Client(api_key, api_secret)

# List of top 100 cryptocurrencies by market cap
symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "SOLUSDT", "USDTUSDT", "USDCUSDT", "DOTUSDT",
    "LTCUSDT", "LINKUSDT", "XLMUSDT", "BCHUSDT", "ETCUSDT", "XMRUSDT", "EOSUSDT", "TRXUSDT", "XEMUSDT", "XTZUSDT",
    "VETUSDT", "NEOUSDT", "ATOMUSDT", "ONTUSDT", "ICXUSDT", "QTUMUSDT", "ZECUSDT", "DASHUSDT", "ZILUSDT", "THETAUSDT",
    "IOTAUSDT", "BATUSDT", "NANOUSDT", "OMGUSDT", "ZRXUSDT", "COMPUSDT", "BALUSDT", "YFIUSDT", "UNIUSDT", "AAVEUSDT",
    "FILUSDT", "SUSHIUSDT", "KNCUSDT", "CRVUSDT", "SNXUSDT", "LRCUSDT", "MATICUSDT", "RUNEUSDT", "AVAXUSDT", "FTMUSDT",
    "BANDUSDT", "GRTUSDT", "1INCHUSDT", "RENUSDT", "KSMUSDT", "CELRUSDT", "HNTUSDT", "OGNUSDT", "ANKRUSDT", "DENTUSDT",
    "ANKRUSDT", "STORJUSDT", "SXPUSDT", "NUUSDT", "OCEANUSDT", "CHZUSDT", "SANDUSDT", "MANAUSDT", "LPTUSDT", "ENJUSDT",
    "SKLUSDT", "REQUSDT", "BNTUSDT", "RLCUSDT", "GNOUSDT", "ANTUSDT", "STXUSDT", "POWRUSDT", "INJUSDT", "FORUSDT",
    "KEEPUSDT", "UOSUSDT", "RNDRUSDT", "GLMUSDT", "VIDTUSDT", "DENTUSDT", "BONDUSDT", "RLCUSDT", "LRCUSDT", "QNTUSDT",
    "GNOUSDT", "ANTUSDT", "STXUSDT", "SKLUSDT", "SUSHIUSDT", "CELUSDT", "RVNUSDT", "OXTUSDT", "BELUSDT", "CTSIUSDT",
    "RLYUSDT", "POWRUSDT", "INJUSDT", "FORUSDT", "KEEPUSDT", "UOSUSDT", "RNDRUSDT", "SXPUSDT", "GLMUSDT", "VIDTUSDT",
    "DENTUSDT", "BONDUSDT"
]

# Directory to save historical data
data_dir = 'data/historical'
os.makedirs(data_dir, exist_ok=True)

# Fetch historical data for each symbol
for symbol in symbols:
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "1 year ago UTC")
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df.to_csv(os.path.join(data_dir, f'{symbol}_historical_data.csv'))

print("Historical data fetched and saved successfully.")
