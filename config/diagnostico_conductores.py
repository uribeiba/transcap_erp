#!/usr/bin/env python
"""
Diagnóstico: Verifica el estado de los conductores
Ejecutar: python manage.py shell < diagnostico_conductores.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tu_proyecto.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Conductor
from roles.models import UsuarioRol
from api_movil.models import UbicacionChofer

def diagnosticar():
    print("=" * 60)
    print("DIAGNÓSTICO DE CONDUCTORES")
    print("=" * 60)
    
    conductores = Conductor.objects.all()
    
    print(f"\n📊 TOTAL CONDUCTORES: {conductores.count()}")
    print("-" * 60)
    
    for c in conductores:
        tiene_usuario = c.usuario is not None
        tiene_rol = False
        puede_loguear = False
        tiene_ubicacion = UbicacionChofer.objects.filter(conductor=c).exists()
        
        if tiene_usuario:
            usuario_rol = UsuarioRol.objects.filter(usuario=c.usuario).first()
            tiene_rol = usuario_rol is not None
            puede_loguear = c.usuario.is_active
        
        estado = "✅" if (tiene_usuario and tiene_rol and puede_loguear) else "⚠️"
        
        print(f"\n{estado} {c.rut} - {c.nombres} {c.apellidos}")
        print(f"   ├── Usuario: {'SÍ' if tiene_usuario else '❌ NO'} ({c.usuario.username if c.usuario else '-'})")
        print(f"   ├── Rol Chofer: {'SÍ' if tiene_rol else '❌ NO'}")
        print(f"   ├── Activo: {'SÍ' if c.activo else 'NO'}")
        print(f"   ├── Usuario activo: {'SÍ' if puede_loguear else 'NO' if tiene_usuario else '-'}")
        print(f"   └── Ubicaciones: {UbicacionChofer.objects.filter(conductor=c).count()} registros")
    
    print("\n" + "=" * 60)
    print("RESUMEN:")
    print(f"  ✅ Conductores con usuario: {Conductor.objects.filter(usuario__isnull=False).count()}")
    print(f"  ⚠️ Conductores SIN usuario: {Conductor.objects.filter(usuario__isnull=True).count()}")
    print("=" * 60)

if __name__ == "__main__":
    diagnosticar()