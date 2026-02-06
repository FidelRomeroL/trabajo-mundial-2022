
import wbgapi as wb
import pandas as pd
import os

# Configuración
OUTPUT_DIR = r"C:\Users\Fidel\.gemini\antigravity\scratch\reemplazo_stata\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Indicadores
# NY.GDP.PCAP.PP.KD: GDP per capita, PPP (constant 2017 international $)
# SP.DYN.LE00.IN: Life expectancy at birth, total (years)
indicators = {
    'NY.GDP.PCAP.PP.KD': 'gdp_pcap_ppp',
    'SP.DYN.LE00.IN': 'life_expectancy'
}

YEAR = 2022

print(f"Descargando datos del Banco Mundial para el año {YEAR}...")

try:
    # Descargar datos
    # economy=all para todos los países
    df = wb.data.DataFrame(indicators.keys(), time=YEAR, labels=True, economy='all')
    
    # Renombrar columnas
    df = df.rename(columns=indicators)
    
    # Reset index para tener el código del país como columna
    df = df.reset_index()
    df = df.rename(columns={'economy': 'iso3_code', 'Country': 'country_name'})
    
    # Guardar
    output_path = os.path.join(OUTPUT_DIR, "wb_data_raw.csv")
    df.to_csv(output_path, index=False)
    
    print(f"Datos guardados exitosamente en: {output_path}")
    print(df.head())
    print("\nResumen de datos faltantes:")
    print(df.isnull().sum())

except Exception as e:
    print(f"Error al descargar datos: {e}")
