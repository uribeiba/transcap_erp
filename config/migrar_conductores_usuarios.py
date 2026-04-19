#!/usr/bin/env python
"""
Script para migrar conductores existentes que no tienen usuario asociado.
Ejecutar: python manage.py shell < migrar_conductores_usuarios.py
O mejor: python manage.py runscript migrar_conductores_usuarios (si tienes django-extensions)
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tu_proyecto.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from taller.models import Conductor
from roles.models import Rol, UsuarioRol

def migrar_conductores():
    print("=" * 60)
    print("MIGRACIÓN DE CONDUCTORES A USUARIOS")
    print("=" * 60)
    
    # Obtener o crear rol Chofer
    rol_chofer, created = Rol.objects.get_or_create(
        nombre='Chofer',
        defaults={'descripcion': 'Rol para conductores que usan la app móvil'}
    )
    
    if created:
        print("✅ Rol 'Chofer' creado")
    else:
        print(f"✅ Rol 'Chofer' encontrado (ID: {rol_chofer.id})")
    
    # Obtener conductores sin usuario asociado
    conductores_sin_usuario = Conductor.objects.filter(usuario__isnull=True)
    total = conductores_sin_usuario.count()
    
    print(f"\n📊 Conductores sin usuario: {total}")
    
    creados = 0
    errores = 0
    
    for conductor in conductores_sin_usuario:
        try:
            # Limpiar RUT
            rut_limpio = conductor.rut.replace('.', '').replace('-', '')
            username = rut_limpio
            password = rut_limpio
            
            # Crear usuario
            user, created_user = User.objects.get_or_create(username=username)
            
            if created_user:
                user.set_password(password)
                user.first_name = conductor.nombres
                user.last_name = conductor.apellidos
                user.email = conductor.email or ''
                user.save()
                print(f"  ✅ Usuario CREADO: {username} - {conductor.nombres} {conductor.apellidos}")
            else:
                print(f"  🔗 Usuario EXISTENTE: {username} - vinculando...")
            
            # Asignar rol Chofer
            usuario_rol, created_ur = UsuarioRol.objects.get_or_create(
                usuario=user,
                defaults={'rol': rol_chofer}
            )
            
            if not created_ur and usuario_rol.rol != rol_chofer:
                usuario_rol.rol = rol_chofer
                usuario_rol.save()
                print(f"     - Rol actualizado a Chofer")
            
            # Sincronizar permisos
            user.user_permissions.set(rol_chofer.permisos.all())
            
            # Vincular conductor
            conductor.usuario = user
            conductor.save()
            
            creados += 1
            
        except Exception as e:
            print(f"  ❌ ERROR con {conductor.rut}: {str(e)}")
            errores += 1
    
    print("\n" + "=" * 60)
    print(f"RESUMEN:")
    print(f"  ✅ Conductores migrados: {creados}")
    print(f"  ❌ Errores: {errores}")
    print("=" * 60)
    
    # Verificar resultados
    print("\n📋 CONDUCTORES CON USUARIO AHORA:")
    conductores_con_usuario = Conductor.objects.filter(usuario__isnull=False)
    for c in conductores_con_usuario:
        print(f"  - {c.rut} | {c.nombres} {c.apellidos} | usuario: {c.usuario.username}")

if __name__ == "__main__":
    migrar_conductores()