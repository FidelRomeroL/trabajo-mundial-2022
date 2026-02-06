
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import contextily as ctx
import os

# Configuración de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

# Rutas
DATA_PATH = r"C:\Users\Fidel\.gemini\antigravity\scratch\reemplazo_stata\data\wb_data_raw.csv"
OUTPUT_DIR = r"C:\Users\Fidel\.gemini\antigravity\scratch\reemplazo_stata\output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    print("Cargando datos...")
    df = pd.read_csv(DATA_PATH)
    
    print("Cargando mapa mundial...")
    # Descargar o cargar shapefile de Natural Earth
    # URL estable para ne_110m_admin_0_countries
    world_url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    
    local_shp_path = os.path.join(OUTPUT_DIR, "ne_110m_admin_0_countries.zip")
    
    if not os.path.exists(local_shp_path):
        import requests
        print(f"Descargando mapa base desde {world_url}...")
        r = requests.get(world_url)
        with open(local_shp_path, 'wb') as f:
            f.write(r.content)
            
    world = gpd.read_file(local_shp_path)
    
    # Renombrar columnas para compatibilidad con código anterior (ne_110m usa ADM0_A3 o ADM0_A3_IS)
    # Natural Earth 110m columns: ADM0_A3 (iso3)
    if 'ADM0_A3' in world.columns:
        world['iso_a3'] = world['ADM0_A3']
    if 'NAME' in world.columns:
        world['name'] = world['NAME']
    
    # Excluir Antártida para mejor visualización
    world = world[world.name != "Antarctica"]
    
    print("Uniendo datos...")
    # Unir por código ISO
    # world.iso_a3 tiene problemas con Francia y Noruega a veces (-99), corrección rápida para Francia
    world.loc[world['name'] == 'France', 'iso_a3'] = 'FRA'
    world.loc[world['name'] == 'Norway', 'iso_a3'] = 'NOR'
    
    gdf = world.merge(df, left_on='iso_a3', right_on='iso3_code', how='left')
    
    # Filtrar datos faltantes para el análisis estadístico
    gdf_clean = gdf.dropna(subset=['gdp_pcap_ppp', 'life_expectancy'])
    n_paises = len(gdf_clean)
    print(f"Número de países incluidos en el análisis: {n_paises}")
    
    # --- ANÁLISIS ESTADÍSTICO ---
    slope, intercept, r_value, p_value, std_err = stats.linregress(gdf_clean['gdp_pcap_ppp'], gdf_clean['life_expectancy'])
    r_squared = r_value**2
    
    # --- GRAFICO 1: MAPA PIB PER CÁPITA ---
    print("Generando Mapa de PIB...")
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    gdf.plot(column='gdp_pcap_ppp', ax=ax, legend=True,
             legend_kwds={'label': "PIB per cápita (PPA, $ int. 2017)", 'orientation': "horizontal", 'shrink': 0.6},
             cmap='viridis', missing_kwds={'color': 'lightgrey', 'label': 'Sin datos'})
    
    ax.set_title(f'Distribución Global del PIB per Cápita (2022)\nN={n_paises} países', fontsize=16, fontweight='bold')
    ax.set_axis_off()
    plt.annotate('Fuente: Elaboración propia con datos del Banco Mundial (WDI).', 
                 xy=(0.1, 0.05), xycoords='figure fraction', fontsize=10, color='#555555')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '01_mapa_pib.png'), bbox_inches='tight')
    plt.close()
    
    # --- GRAFICO 2: MAPA ESPERANZA DE VIDA ---
    print("Generando Mapa de Esperanza de Vida...")
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    gdf.plot(column='life_expectancy', ax=ax, legend=True,
             legend_kwds={'label': "Esperanza de Vida al Nacer (años)", 'orientation': "horizontal", 'shrink': 0.6},
             cmap='plasma', missing_kwds={'color': 'lightgrey', 'label': 'Sin datos'})
    
    ax.set_title(f'Distribución Global de la Esperanza de Vida (2022)\nN={n_paises} países', fontsize=16, fontweight='bold')
    ax.set_axis_off()
    plt.annotate('Fuente: Elaboración propia con datos del Banco Mundial (WDI).', 
                 xy=(0.1, 0.05), xycoords='figure fraction', fontsize=10, color='#555555')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '02_mapa_esperanza_vida.png'), bbox_inches='tight')
    plt.close()
    
    # --- GRAFICO 3: SCATTER PLOT ---
    print("Generando Gráfico de Dispersión...")
    plt.figure(figsize=(10, 7))
    sns.regplot(x='gdp_pcap_ppp', y='life_expectancy', data=gdf_clean, 
                scatter_kws={'alpha': 0.6, 's': 50, 'edgecolor': 'w'}, 
                line_kws={'color': 'red', 'label': f'Regresión Lineal (R²={r_squared:.2f})'},
                truncate=False)
    
    plt.title('Relación entre PIB per Cápita y Esperanza de Vida (2022)', fontsize=14, fontweight='bold')
    plt.xlabel('PIB per Cápita (PPA, $ constantes 2017)', fontsize=12)
    plt.ylabel('Esperanza de Vida (años)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Añadir algunas etiquetas a países destacados (opcional)
    destacados = ['USA', 'CHN', 'IND', 'JPN', 'DEU', 'BRA', 'NGA', 'ZWE', 'QAT']
    for idx, row in gdf_clean.iterrows():
        if row['iso_a3'] in destacados:
            plt.text(row['gdp_pcap_ppp']+500, row['life_expectancy'], row['iso_a3'], fontsize=9)
            
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '03_dispersion_pib_ev.png'), bbox_inches='tight')
    plt.close()

    # --- REPORTE DE TEXTO ---
    reporte = f"""
    # Análisis de Asociación Lineal: PIB per Cápita y Esperanza de Vida (2022)

    ## Resumen de Datos
    - Número de países/regiones analizados: {n_paises}
    
    ## Estadística Descriptiva
    - Correlación (r): {r_value:.4f}
    - Coeficiente de Determinación (R²): {r_squared:.4f}
    - Pendiente (m): {slope:.4f} (Por cada $1,000 extra de PIB, la esperanza de vida aumenta aprox. {slope*1000:.2f} años en promedio lineal)

    ## Análisis de Distribución Geográfica
    Se observa una clara división Norte-Sur, aunque con matices. Las regiones con mayores ingresos (Norteamérica, Europa Occidental, Australia) presentan consistentemente esperanzas de vida superiores a los 80 años. Por el contrario, África Subsahariana muestra los niveles más bajos en ambas variables, ilustrando la fuerte correlación visual entre desarrollo económico y salud poblacional.
    
    ## Análisis de la Relación Lineal
    El gráfico de dispersión muestra una asociación positiva fuerte (R² = {r_squared:.2f}). Sin embargo, la relación no es perfectamente lineal; exhibe rendimientos decrecientes (concavidad), conocida como la "Curva de Preston": aumentos en el ingreso tienen gran impacto en la salud en países pobres, pero el efecto marginal disminuye en países ricos. A pesar de esto, una aproximación lineal sigue siendo estadísticamente significativa y explicativa para una gran parte de la varianza.
    """
    
    with open(os.path.join(OUTPUT_DIR, 'analisis_resultados.txt'), 'w', encoding='utf-8') as f:
        f.write(reporte)
        
    print("Análisis completado. Archivos generados en 'output'.")

if __name__ == "__main__":
    main()
