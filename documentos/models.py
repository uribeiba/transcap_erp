from django.db import models
from django.contrib.auth.models import User


class Documento(models.Model):

    TIPO_DOCUMENTO = [
    ("GUIA", "Guía"),
    ("PEAJE", "Peaje"),
    ("FOTO_CARGA", "Foto de carga"),
]

    ESTADO = [
        ("PENDIENTE", "Pendiente"),
        ("REVISADO", "Revisado"),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Conductor"
    )

    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOCUMENTO,
        verbose_name="Tipo documento"
    )

    numero_documento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número documento"
    )

    texto_extraido = models.TextField(
        blank=True,
        null=True
    )

    imagen = models.ImageField(
        upload_to="documentos/"
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADO,
        default="PENDIENTE"
    )

    observacion = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.tipo_documento} - {self.numero_documento}"