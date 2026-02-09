# fix_diagnose.py
import os
import sys

print("=" * 60)
print("DIAGNÓSTICO DEL PROYECTO: transcap_erp 2")
print("=" * 60)

# 1. Información del sistema
print(f"\n1. Directorio actual: {os.getcwd()}")
print(f"2. Python path:")
for i, path in enumerate(sys.path[:10]):  # Solo primeros 10
    print(f"   {i:2d}. {path}")

# 2. Buscar TODAS las apps 'parametros' en el sistema
print(f"\n3. Buscando apps 'parametros' en todo el sistema...")

parametros_paths = []
start_path = "/Users/uribe/Desktop/proyectos"

for root, dirs, files in os.walk(start_path):
    if 'parametros' in dirs:
        full_path = os.path.join(root, 'parametros')
        # Verificar que sea una app Django (tenga apps.py)
        if os.path.exists(os.path.join(full_path, 'apps.py')):
            parametros_paths.append(full_path)
            print(f"   ✅ ENCONTRADA: {full_path}")

print(f"\n4. Total encontradas: {len(parametros_paths)}")
for i, path in enumerate(parametros_paths, 1):
    print(f"   {i}. {path}")

# 3. Verificar INSTALLED_APPS en settings.py
print(f"\n5. Verificando settings.py actual...")
settings_file = "config/settings.py"
if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'parametros' in line.lower():
                print(f"   Línea {i+1}: {line.strip()}")
else:
    print("   ❌ No se encuentra settings.py")

print("\n" + "=" * 60)
print("RECOMENDACIÓN:")
if len(parametros_paths) > 1:
    print("⚠️  HAY MÚLTIPLES APPS 'parametros'. Debes eliminar las extras.")
    print("   Mantén solo: /Users/uribe/Desktop/proyectos/python/transcap_erp 2/config/parametros")
else:
    print("✅ Solo hay una app 'parametros'.")
print("=" * 60)