from rest_framework import serializers
from .models import ReporteChofer, FotoReporte
from operaciones.models import EstatusOperacionalViaje
from taller.models import Conductor

class FotoReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoReporte
        fields = ['id', 'imagen', 'descripcion', 'creado_el']

class ReporteChoferSerializer(serializers.ModelSerializer):
    fotos = FotoReporteSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReporteChofer
        fields = '__all__'
        read_only_fields = ['conductor', 'creado_el']

class ViajeChoferSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.razon_social', read_only=True)
    
    class Meta:
        model = EstatusOperacionalViaje
        fields = ['id', 'fecha', 'turno', 'cliente_nombre', 'estado_carga', 'lugar_carga', 'lugar_descarga', 'nro_guia']