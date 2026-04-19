#!/usr/bin/env python
"""
Carga masiva de conductores desde archivo Excel.
Solo procesa registros donde Tipo Ficha es 'Empleado' o 'Honorario'

Ejecutar: python manage.py shell < cargar_conductores_excel.py
"""

import os
import django

# ✅ CORREGIDO - Usando el nombre real de tu proyecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
from django.contrib.auth.models import User
from taller.models import Conductor
from roles.models import Rol, UsuarioRol

# Ruta del archivo Excel (en la raíz del proyecto)
EXCEL_PATH = 'Fichas.xlsx'

# Tipos que se consideran conductores
TIPOS_CONDUCTOR = ['Empleado', 'Honorario']

def limpiar_rut(rut):
    """Limpia el RUT: elimina puntos y guión, convierte a string"""
    if pd.isna(rut):
        return None
    rut_str = str(rut).strip().upper()
    rut_limpio = rut_str.replace('.', '').replace('-', '')
    return rut_limpio

def extraer_nombres_apellidos(nombre_completo):
    """Extrae nombres y apellidos de un nombre completo"""
    if pd.isna(nombre_completo) or not nombre_completo:
        return "", ""
    
    nombre_str = str(nombre_completo).strip()
    partes = nombre_str.split(' ', 1)
    
    if len(partes) == 2:
        return partes[0], partes[1]
    else:
        return nombre_str, ""

def cargar_conductores():
    print("=" * 60)
    print("CARGA MASIVA DE CONDUCTORES DESDE EXCEL")
    print("=" * 60)
    
    # Verificar si el archivo existe
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ ERROR: No se encuentra el archivo {EXCEL_PATH}")
        print(f"   Ubicación actual: {os.getcwd()}")
        print(f"   Archivos en esta carpeta: {os.listdir('.')}")
        return
    
    # Leer Excel
    try:
        df = pd.read_excel(EXCEL_PATH)
        print(f"✅ Archivo cargado: {len(df)} registros")
        print(f"📋 Columnas encontradas: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return
    
    # Filtrar solo conductores (Empleado o Honorario)
    df_conductores = df[df['Tipo Ficha'].isin(TIPOS_CONDUCTOR)]
    print(f"📊 Conductores a procesar (Empleado/Honorario): {len(df_conductores)}")
    
    if len(df_conductores) == 0:
        print("⚠️ No se encontraron registros con Tipo Ficha = Empleado o Honorario")
        print(f"   Tipos disponibles: {df['Tipo Ficha'].unique()}")
        return
    
    # Obtener o crear rol Chofer
    rol_chofer, created = Rol.objects.get_or_create(
        nombre='Chofer',
        defaults={'descripcion': 'Rol para conductores que usan la app móvil'}
    )
    print(f"✅ Rol Chofer: ID {rol_chofer.id} ({'creado' if created else 'existente'})")
    
    creados = 0
    actualizados = 0
    errores = 0
    
    for idx, row in df_conductores.iterrows():
        try:
            rut = row.get('Rut')
            
            if pd.isna(rut) or not str(rut).strip():
                print(f"  ⚠️ Fila {idx}: RUT vacío, saltando")
                continue
            
            rut_str = str(rut).strip()
            nombre_completo = row.get('Nombre', '')
            telefono = row.get('Teléfono', '')
            email = row.get('E-mail', '')
            estado = row.get('Estado', 'Activa')
            
            # Limpiar RUT
            rut_limpio = limpiar_rut(rut_str)
            
            # Extraer nombres y apellidos
            nombres, apellidos = extraer_nombres_apellidos(nombre_completo)
            
            # Verificar si el conductor ya existe
            conductor, created = Conductor.objects.get_or_create(
                rut=rut_str,
                defaults={
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'telefono': str(telefono) if not pd.isna(telefono) else '',
                    'email': str(email) if not pd.isna(email) else '',
                    'activo': estado.lower() == 'activa',
                }
            )
            
            if not created:
                # Actualizar datos si es necesario
                if nombres and not conductor.nombres:
                    conductor.nombres = nombres
                if apellidos and not conductor.apellidos:
                    conductor.apellidos = apellidos
                if not pd.isna(telefono) and telefono:
                    conductor.telefono = str(telefono)
                if not pd.isna(email) and email:
                    conductor.email = str(email)
                conductor.activo = estado.lower() == 'activa'
                conductor.save()
                print(f"  🔄 ACTUALIZADO: {rut_str} - {nombre_completo}")
                actualizados += 1
            else:
                print(f"  ✅ CREADO: {rut_str} - {nombre_completo}")
                creados += 1
            
            # Crear o vincular usuario si no tiene
            if not conductor.usuario:
                username = rut_limpio
                password = rut_limpio
                
                user, user_created = User.objects.get_or_create(username=username)
                if user_created:
                    user.set_password(password)
                    user.first_name = conductor.nombres
                    user.last_name = conductor.apellidos
                    user.email = conductor.email or ''
                    user.save()
                    print(f"     - Usuario creado: {username} / contraseña: {password}")
                else:
                    print(f"     - Usuario existente vinculado: {username}")
                
                # Asignar rol Chofer
                usuario_rol, ur_created = UsuarioRol.objects.get_or_create(
                    usuario=user,
                    defaults={'rol': rol_chofer}
                )
                
                if not ur_created and usuario_rol.rol != rol_chofer:
                    usuario_rol.rol = rol_chofer
                    usuario_rol.save()
                    print(f"     - Rol Chofer asignado")
                
                # Sincronizar permisos
                user.user_permissions.set(rol_chofer.permisos.all())
                
                conductor.usuario = user
                conductor.save()
            else:
                print(f"     - Ya tenía usuario: {conductor.usuario.username}")
            
        except Exception as e:
            print(f"  ❌ ERROR fila {idx} ({row.get('Rut', '?')}): {str(e)}")
            errores += 1
    
    print("\n" + "=" * 60)
    print(f"RESUMEN FINAL:")
    print(f"  ✅ Conductores creados: {creados}")
    print(f"  🔄 Conductores actualizados: {actualizados}")
    print(f"  ❌ Errores: {errores}")
    print("=" * 60)
    
    # Mostrar resultados
    print("\n📋 CONDUCTORES EN BASE DE DATOS:")
    conductores_total = Conductor.objects.all()
    for c in conductores_total[:20]:
        tiene_user = "✅" if c.usuario else "❌"
        print(f"  {tiene_user} {c.rut} - {c.nombres} {c.apellidos}")

if __name__ == "__main__":
    cargar_conductores()