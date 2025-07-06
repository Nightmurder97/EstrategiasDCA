import pandas as pd

def normalize_data_file():
    # Leer el archivo original
    df = pd.read_csv('Portafolio _personal/data_actualizada_binance_kucoin', delimiter=';')
    
    # Normalizar la columna Pair reemplazando '-' por '/'
    df['Pair'] = df['Pair'].str.replace('-', '/')
    
    # Guardar el archivo normalizado
    df.to_csv('Portafolio _personal/data_actualizada_binance_kucoin', sep=';', index=False)
    
    print("Archivo normalizado correctamente")

if __name__ == "__main__":
    normalize_data_file() 