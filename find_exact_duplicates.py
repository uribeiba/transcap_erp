import sys
import os

print("=" * 80)
print("BUSCANDO DUPLICADOS EXACTOS DE 'parametros'")
print("=" * 80)

# Configurar Django MANUALMENTE para evitar el error
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Importar solo lo necesario para diagnóstico
from django.conf import settings

print("\n1. INSTALLED_APPS en settings.py:")
for i, app in enumerate(settings.INSTALLED_APPS):
    if 'parametros' in str(app):
        print(f"   {i}: ⚠️  {app}")
    else:
        print(f"   {i}: {app}")

print("\n2. Buscando archivos 'apps.py' con 'ParametrosConfig'...")
apps_found = []

# Buscar en todo el sistema de archivos
search_paths = [
    "/Users/uribe/Desktop/proyectos",
    os.getcwd(),
    os.path.dirname(os.getcwd())
]

for search_path in search_paths:
    if os.path.exists(search_path):
        for root, dirs, files in os.walk(search_path):
            if 'apps.py' in files:
                apps_file = os.path.join(root, 'apps.py')
                try:
                    with open(apps_file, 'r') as f:
                        content = f.read()
                        if 'ParametrosConfig' in content:
                            # Extraer nombre de la app
                            app_name = os.path.basename(os.path.dirname(apps_file))
                            apps_found.append({
                                'path': os.path.dirname(apps_file),
                                'apps_file': apps_file,
                                'name': app_name
                            })
                except:
                    pass

print(f"\n3. Apps 'ParametrosConfig' encontradas: {len(apps_found)}")
for i, app in enumerate(apps_found, 1):
    print(f"\n   {i}. Nombre: {app['name']}")
    print(f"      Ruta: {app['path']}")
    print(f"      apps.py: {app['apps_file']}")
    
    # Leer apps.py
    try:
        with open(app['apps_file'], 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'name =' in line or 'class ' in line:
                    print(f"      → {line.strip()}")
    except:
        print("      ❌ No se pudo leer")

print("\n" + "=" * 80)
if len(apps_found) > 1:
    print("⚠️  PROBLEMA: Hay múltiples apps 'ParametrosConfig'!")
    print("\nSOLUCIÓN: Eliminar todas excepto UNA.")
    print("La correcta debe ser:")
    correct_path = "/Users/uribe/Desktop/proyectos/python/transcap_erp 2/config/parametros"
    print(f"   {correct_path}")
    
    print("\nPara eliminar las otras:")
    for app in apps_found:
        if app['path'] != correct_path:
            print(f"   rm -rf \"{app['path']}\"")
else:
    print("✅ Solo hay una app 'parametros'")
print("=" * 80)
