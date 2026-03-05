from django.db import migrations
from django.db.utils import OperationalError


def forwards(apps, schema_editor):
    """
    Esta migración originalmente era 100% PostgreSQL.
    Aquí la hacemos compatible:
      - PostgreSQL: mantiene SQL original (public., timestamptz, defaults, not null)
      - SQLite: agrega columna (si no existe) y setea valores para filas antiguas
    """
    vendor = schema_editor.connection.vendor  # 'postgresql' | 'sqlite' | etc.

    if vendor == "postgresql":
        sql = """
            ALTER TABLE public.parametros_empresa
            ADD COLUMN IF NOT EXISTS actualizada_el timestamptz;

            UPDATE public.parametros_empresa
            SET actualizada_el = NOW()
            WHERE actualizada_el IS NULL;

            ALTER TABLE public.parametros_empresa
            ALTER COLUMN actualizada_el SET DEFAULT NOW();

            ALTER TABLE public.parametros_empresa
            ALTER COLUMN actualizada_el SET NOT NULL;
        """
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql)
        return

    # ✅ SQLite / otros motores (local)
    # SQLite no soporta:
    # - public.schema
    # - timestamptz
    # - ADD COLUMN IF NOT EXISTS (según versión)
    # - ALTER COLUMN SET DEFAULT / SET NOT NULL
    # Solución: agregar columna y rellenar NULLs. Defaults/NOT NULL no son críticos en local.
    table = "parametros_empresa"

    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN actualizada_el datetime;")
        except OperationalError as e:
            # Si ya existe la columna, SQLite lanza "duplicate column name"
            if "duplicate column name" not in str(e).lower():
                raise

        # Rellenar valores nulos (timestamp actual)
        cursor.execute(
            f"UPDATE {table} SET actualizada_el = CURRENT_TIMESTAMP WHERE actualizada_el IS NULL;"
        )


def backwards(apps, schema_editor):
    vendor = schema_editor.connection.vendor

    if vendor == "postgresql":
        sql = """
            ALTER TABLE public.parametros_empresa
            DROP COLUMN IF EXISTS actualizada_el;
        """
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql)
        return

    # SQLite no soporta DROP COLUMN de forma universal (depende de versión),
    # y no vale la pena reconstruir tablas en local para un rollback.
    # Dejamos NOOP.
    return


class Migration(migrations.Migration):

    dependencies = [
        ("parametros", "0002_alter_empresa_options_alter_perfil_options_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]