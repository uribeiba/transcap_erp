from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bitacora
from operaciones.models import EstatusOperacionalViaje

@receiver(post_save, sender=Bitacora)
def crear_viaje_desde_bitacora(sender, instance, created, **kwargs):
    """Cuando se crea una bitácora con conductor, crea un viaje automáticamente"""
    
    if not created:
        return  # Solo al crear
    
    if not instance.conductor:
        return  # Sin conductor, no crear viaje
    
    if instance.estatus_origen:
        return  # Ya tiene viaje asociado
    
    # Crear el viaje
    viaje = EstatusOperacionalViaje.objects.create(
        fecha=instance.fecha,
        turno='AM',
        conductor=instance.conductor,
        cliente=instance.cliente,
        tracto=instance.tracto,
        rampla=instance.rampla,
        lugar_carga=instance.origen,
        lugar_descarga=instance.destino,
        nro_guia=instance.guias_raw,
        estado_carga='PENDIENTE',
    )
    
    instance.estatus_origen = viaje
    instance.save(update_fields=['estatus_origen'])
    
    print(f"✅ Viaje #{viaje.id} creado automáticamente para bitácora #{instance.id}")