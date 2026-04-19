#!/usr/bin/env python
"""
Carga masiva de vehículos desde Excel Detalle Equipos VE.10-04.xlsx
Ejecutar: python manage.py shell < cargar_vehiculos_excel.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
from taller.models import Vehiculo

# Ruta del archivo
EXCEL_PATH = 'Detalle Equipos VE.10-04.xlsx'

def limpiar_patente(patente):
    if pd.isna(patente):
        return None
    return str(patente).strip().upper().replace(' ', '')

def mapear_tipo(tipo_texto):
    tipo_texto = str(tipo_texto).strip().upper() if not pd.isna(tipo_texto) else ''
    if 'TRACT' in tipo_texto:
        return 'TRACTO'
    elif 'REMOLQUE' in tipo_texto or 'SEMIRREMOLQUE' in tipo_texto:
        return 'SEMIRREMOLQUE'
    elif 'CAMION' in tipo_texto:
        return 'CAMION'
    else:
        return 'OTRO'

def cargar_vehiculos():
    print("=" * 60)
    print("CARGA MASIVA DE VEHÍCULOS")
    print("=" * 60)
    
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ No se encuentra {EXCEL_PATH}")
        print(f"Archivos en carpeta: {os.listdir('.')[:10]}")
        return
    
    df = pd.read_excel(EXCEL_PATH, header=1)
    print(f"✅ Excel cargado: {len(df)} registros")
    
    # Renombrar columnas
    df.columns = ['N°', 'Patente', 'Marca', 'Modelo', 'Año', 'Color', 'Tipo', 
                  'Leasing', 'Valor Comercial', 'Chasis']
    
    creados = 0
    errores = 0
    
    for idx, row in df.iterrows():
        try:
            patente = limpiar_patente(row.get('Patente'))
            if not patente or patente == 'NAN':
                continue
            
            marca = str(row.get('Marca', '')).strip() if not pd.isna(row.get('Marca')) else ''
            modelo = str(row.get('Modelo', '')).strip() if not pd.isna(row.get('Modelo')) else ''
            anio = row.get('Año')
            anio = int(anio) if not pd.isna(anio) and anio else None
            color = str(row.get('Color', '')).strip() if not pd.isna(row.get('Color')) else ''
            tipo = mapear_tipo(row.get('Tipo', ''))
            leasing = str(row.get('Leasing', '')).strip() if not pd.isna(row.get('Leasing')) else ''
            chasis = str(row.get('Chasis', '')).strip() if not pd.isna(row.get('Chasis')) else ''
            
            vehiculo, created = Vehiculo.objects.update_or_create(
                patente=patente,
                defaults={
                    'marca': marca,
                    'modelo': modelo,
                    'anio': anio,
                    'tipo': tipo,
                    'nro_chasis': chasis,
                    'aseguradora': leasing,
                    'descripcion_equipo': f"Color: {color}" if color else '',
                    'activo': True,
                }
            )
            
            if created:
                creados += 1
                print(f"  ✅ CREADO: {patente} - {marca} {modelo}")
            else:
                print(f"  🔄 ACTUALIZADO: {patente}")
                
        except Exception as e:
            errores += 1
            print(f"  ❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"  ✅ Creados: {creados}")
    print(f"  ❌ Errores: {errores}")
    print(f"  📊 Total vehículos: {Vehiculo.objects.count()}")
    print("=" * 60)

if __name__ == "__main__":
    cargar_vehiculos()