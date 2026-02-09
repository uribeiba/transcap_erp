from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("parametros", "0002_alter_empresa_options_alter_perfil_options_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE public.parametros_empresa
                ADD COLUMN IF NOT EXISTS actualizada_el timestamptz;

                UPDATE public.parametros_empresa
                SET actualizada_el = NOW()
                WHERE actualizada_el IS NULL;

                ALTER TABLE public.parametros_empresa
                ALTER COLUMN actualizada_el SET DEFAULT NOW();

                ALTER TABLE public.parametros_empresa
                ALTER COLUMN actualizada_el SET NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE public.parametros_empresa
                DROP COLUMN IF EXISTS actualizada_el;
            """,
        ),
    ]
