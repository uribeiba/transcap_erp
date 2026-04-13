# remuneraciones/services/liquidacion_service.py
from decimal import Decimal
from django.db import transaction

from remuneraciones.models import (
    Liquidacion,
    LiquidacionDetalle,
    Concepto
)
from remuneraciones.services.calculo_remuneraciones import CalculadoraRemuneraciones


class LiquidacionService:

    @staticmethod
    @transaction.atomic
    def crear_liquidacion(empleado, contrato, periodo, bonos=0, horas_extra=0):
        """
        Crea una liquidación completa de un contrato:
        - Calcula haberes y descuentos
        - Guarda Liquidacion y LiquidacionDetalle
        """

        # -------------------------
        # CALCULO DE REMUNERACION
        # -------------------------
        calc = CalculadoraRemuneraciones(contrato)
        resultado = calc.calcular(bonos=bonos, horas_extra=horas_extra)

        total_descuentos = resultado['afp'] + resultado['salud'] + resultado['afc'] + resultado['impuesto']

        # -------------------------
        # CREAR LIQUIDACIÓN
        # -------------------------
        liquidacion = Liquidacion.objects.create(
            empleado=empleado,
            contrato=contrato,
            periodo=periodo,
            fecha_pago=None,
            total_haberes=resultado['imponible'],
            total_descuentos=total_descuentos,
            liquido_pagar=resultado['liquido']
        )

        # -------------------------
        # FUNCION AUXILIAR PARA DETALLES
        # -------------------------
        def add_detalle(codigo, nombre, tipo, monto, es_imponible=True, es_tributable=True):
            concepto, _ = Concepto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'tipo': tipo,
                    'es_imponible': es_imponible,
                    'es_tributable': es_tributable
                }
            )

            LiquidacionDetalle.objects.create(
                liquidacion=liquidacion,
                concepto=concepto,
                monto=monto
            )

        # -------------------------
        # HABERES IMPONIBLES
        # -------------------------
        add_detalle("SUELDO_BASE", "Sueldo Base", "HABER_IMPONIBLE", resultado['sueldo_base'])
        add_detalle("HORAS_EXTRA", "Horas Extra", "HABER_IMPONIBLE", resultado['horas_extra'])
        add_detalle("GRATIFICACION", "Gratificación", "HABER_IMPONIBLE", resultado['gratificacion'])

        # -------------------------
        # DESCUENTOS
        # -------------------------
        add_detalle("AFP", "AFP", "DESCUENTO", resultado['afp'], es_imponible=False, es_tributable=True)
        add_detalle("SALUD", "Salud", "DESCUENTO", resultado['salud'], es_imponible=False, es_tributable=True)
        add_detalle("AFC", "AFC", "DESCUENTO", resultado['afc'], es_imponible=False, es_tributable=True)
        add_detalle("IMPUESTO", "Impuesto Único", "DESCUENTO", resultado['impuesto'], es_imponible=False, es_tributable=True)

        return liquidacion