#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Meteogram for WRF 5-days-simulation
"""

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import pandas as pd
from datetime import datetime

def validate_input(date_str, hour_str):
    """Valida a data e hora inseridas pelo usuário."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        if not (0 <= int(hour_str) <= 23):
            raise ValueError("Hora deve estar entre 0 e 23.")
        return True
    except ValueError as e:
        print(f"Erro na entrada: {e}")
        return False

def main():
    # Entrada do usuário
    print("Bem-vindo ao sistema de previsões meteorológicas!")
    while True:
        date = input("Digite a data para previsão (formato: YYYY-MM-DD): ").strip()
        hour = input("Digite a hora para previsão (0-23): ").strip()
        if validate_input(date, hour):
            break
        print("Entrada inválida. Por favor, tente novamente.")
    
    # Diretórios
    output_dir = '/var/www/html/met/temp/'
    os.makedirs(output_dir, exist_ok=True)

    input_dir = f'/home/mpiuser/transfer/{date}{hour}/'
    file_list = glob.glob(os.path.join(input_dir, '*d02*4km'))

    if not file_list:
        print(f"Erro: Nenhum arquivo encontrado no diretório {input_dir}.")
        return

    try:
        # Carregar o primeiro arquivo NetCDF
        ds = xr.open_dataset(file_list[0])
    except Exception as e:
        print(f"Erro ao abrir o arquivo NetCDF: {e}")
        return

    # Extração de dados
    try:
        temperature = ds['T2']
        lat = ds['XLAT'][0, :, :]
        lon = ds['XLONG'][0, :, :]
        time = ds['Times']
    except KeyError as e:
        print(f"Erro: Variável ausente no NetCDF ({e}).")
        return

    # Configuração de fuso horário
    timezone = 'America/Cuiaba'
    utc = pd.date_range(start=f'{date} {hour}', periods=len(time), freq='H', tz='Etc/UCT')
    local_time = utc.tz_convert(timezone)
    formatted_time = local_time.strftime("%d/%m %Hh")
    weekdays = local_time.strftime("%a")

    # Geração dos gráficos
    for t in range(len(formatted_time)):
        fig = plt.figure(figsize=(10, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        levels = np.arange(5, 40, 1)

        # Contorno da temperatura
        plt.contourf(
            lon, lat, temperature[t, :, :] - 273.15,
            levels=levels, cmap='turbo', transform=ccrs.PlateCarree(), extend='both'
        )
        ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black')

        # Adicionar limites estaduais
        states_provinces = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none'
        )
        ax.add_feature(states_provinces, edgecolor='black', linewidth=0.5)

        plt.colorbar(label='Temperatura (°C)', shrink=0.8, orientation='vertical')
        plt.title('Temperatura a 2 m')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

        # Texto com dia e horário
        text = f'Dia {formatted_time[t]} ({weekdays[t]})'
        fig.text(0.45, 0.05, text, ha='center')

        # Cidades
        cities = [
            {'name': 'Campo Grande', 'lon': -54.6156, 'lat': -20.4428},
            {'name': 'Dourados', 'lon': -54.5494, 'lat': -22.2231},
            {'name': 'Três Lagoas', 'lon': -51.7044, 'lat': -20.7511},
        ]

        for city in cities:
            plt.scatter(
                city['lon'], city['lat'], marker='o', color='black', s=50,
                transform=ccrs.PlateCarree(), alpha=0.4
            )
            plt.text(
                city['lon'] + 0.2, city['lat'], city['name'], fontsize=8,
                color='black', transform=ccrs.PlateCarree(), alpha=0.6
            )

        # Salvar a figura
        plt.savefig(f'{output_dir}/{str(t).zfill(3)}.png', dpi=200)
        plt.close()

    print(f"Previsões geradas com sucesso em: {output_dir}")

if __name__ == "__main__":
    main()
