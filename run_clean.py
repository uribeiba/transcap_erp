#!/usr/bin/env python
import os
import sys

# NUKELAR: Eliminar cualquier ruta de otros proyectos
clean_paths = []
for path in sys.path:
    # Mantener rutas del sistema
    if 'site-packages' in path or 'python' in path or not path:
        clean_paths.append(path)
    # Mantener SOLO si es ESTE proyecto exacto
    elif 'transcap_erp 2/config' in path:
        clean_paths.append(path)
    # ELIMINAR cualquier otra ruta de proyectos transcap
    elif 'transcap' in path.lower():
        print(f"✗ Eliminando ruta contaminada: {path}")
    else:
        clean_paths.append(path)

sys.path = clean_paths
print(f"Python Path limpio: {len(sys.path)} rutas")

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    
    from django.apps import apps
    app_labels = [app.label for app in apps.get_app_configs()]
    
    print(f"\n✅ Django configurado!")
    print(f"Apps registradas: {app_labels}")
    
    # Verificar duplicados
    from collections import Counter
    counts = Counter(app_labels)
    duplicates = [label for label, count in counts.items() if count > 1]
    
    if duplicates:
        print(f"\n❌ ERROR: Duplicados: {duplicates}")
        # Mostrar dónde están
        for dup in duplicates:
            print(f"\nApps con label '{dup}':")
            for app in apps.get_app_configs():
                if app.label == dup:
                    print(f"  - {app.name} ({app.path})")
    else:
        print("\n✅ PERFECTO: No hay duplicados!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
