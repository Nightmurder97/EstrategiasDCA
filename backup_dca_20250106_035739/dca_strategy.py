import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def get_historical_data(symbol, start_date, end_date):
    # Obtener datos históricos de Yahoo Finance
    crypto = yf.Ticker(symbol)
    data = crypto.history(start=start_date, end=end_date)
    if data.empty:
        print("No se pudieron obtener datos para esta criptomoneda.")
        return pd.DataFrame()
    data.reset_index(inplace=True)
    data['timestamp'] = data['Date'].apply(lambda x: x.timestamp())
    return data[['timestamp', 'Close']].rename(columns={'Close': 'price'})


def dca_strategy(symbols, start_date, end_date, investment_per_week):
    print(f"Fecha de inicio: {start_date}, Fecha de fin: {end_date}")
    for symbol in symbols:
        print(f"\nEstrategia DCA para {symbol}:")
        data = get_historical_data(symbol, start_date, end_date)
        if data.empty:
            print("No se pudieron obtener datos para esta criptomoneda.")
            continue
        data['date'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('date', inplace=True)

        total_investment = 0
        total_coins = 0

        current_date = start_date
        while current_date <= end_date:
            if current_date in data.index:
                price = data.loc[current_date, 'price']
                coins_bought = investment_per_week / price
                total_coins += coins_bought
                total_investment += investment_per_week
                print(f"Date: {current_date}, Price: {price}, Coins Bought: {coins_bought}")
            current_date += timedelta(weeks=1)

        final_value = total_coins * data.iloc[-1]['price']
        print(f"Total Investment: {total_investment}, Final Value: {final_value}")


# Ejemplo de uso
if __name__ == "__main__":
    symbols = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD']  # Símbolos de Yahoo Finance para criptomonedas
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    investment_per_week = 100  # Inversión en EUR por semana

    dca_strategy(symbols, start_date, end_date, investment_per_week) 