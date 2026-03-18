from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("operaciones", "0006_alter_estatusoperacionalviaje_options_and_more"),
        ("bitacora", "0004_alter_bitacora_destino_alter_bitacora_guias_raw_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="bitacora",
            name="estatus_origen",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bitacoras_generadas",
                to="operaciones.estatusoperacionalviaje",
            ),
        ),
    ]

