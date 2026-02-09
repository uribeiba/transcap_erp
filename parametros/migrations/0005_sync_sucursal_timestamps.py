from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("parametros", "0003_sync_empresa_actualizada_el"),
    ]

    operations = [
        migrations.AddField(
            model_name="sucursal",
            name="creada_el",
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sucursal",
            name="actualizada_el",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
