from django.apps import AppConfig


class ParametrosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "parametros"

    def ready(self):
        from . import signals  # noqa
