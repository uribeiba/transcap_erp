# remuneraciones/services/calculo_remuneraciones.py
from decimal import Decimal

from remuneraciones.services.parametros import (
    tope_imponible_salud,
    tope_imponible_afp,
    UTM
)

from remuneraciones.models import TramoImpuesto, AFP


class CalculadoraRemuneraciones:

    def __init__(self, contrato):
        self.contrato = contrato
        self.sueldo_base = Decimal(str(contrato.sueldo_base))

    # -------------------------
    # HABERES
    # -------------------------

    def calcular_horas_extra(self, horas_extra):
        horas_extra = Decimal(str(horas_extra))
        valor_hora = self.sueldo_base / Decimal('30') / Decimal('8')
        return valor_hora * Decimal('1.5') * horas_extra

    def calcular_gratificacion(self):
        return self.sueldo_base * Decimal('0.25')

    def calcular_imponible(self, bonos=0, horas_extra=0):
        bonos = Decimal(str(bonos))

        horas_extra_monto = self.calcular_horas_extra(horas_extra)
        gratificacion = self.calcular_gratificacion()

        imponible = (
            self.sueldo_base +
            bonos +
            horas_extra_monto +
            gratificacion
        )

        return imponible, horas_extra_monto, gratificacion

    # -------------------------
    # DESCUENTOS
    # -------------------------

    def calcular_afp(self, imponible):
        """
        AFP real con comisión + tope imponible
        """
        from decimal import Decimal
        
        afp = getattr(self.contrato, 'afp', None)

        if not afp:
            return Decimal('0')

        imponible_topeado = min(imponible, tope_imponible_afp())
        
        # Asegurar que tasa_total sea Decimal
        tasa_total = afp.tasa_total()
        if isinstance(tasa_total, float):
            tasa_total = Decimal(str(tasa_total))

        return imponible_topeado * tasa_total

    def calcular_salud(self, imponible):
        """
        Salud 7% con tope imponible
        """
        from decimal import Decimal
        
        salud = getattr(self.contrato, 'salud', None)
        
        if not salud:
            return Decimal('0')
        
        imponible_topeado = min(imponible, tope_imponible_salud())
        
        # Asegurar que tasa_cotizacion sea Decimal
        tasa_cotizacion = salud.tasa_cotizacion
        if isinstance(tasa_cotizacion, float):
            tasa_cotizacion = Decimal(str(tasa_cotizacion))

        return imponible_topeado * tasa_cotizacion

    def calcular_afc(self, imponible):
        """
        AFC con tope imponible
        """
        from decimal import Decimal
        
        imponible_topeado = min(imponible, tope_imponible_afp())
        
        return imponible_topeado * Decimal('0.006')

    def calcular_impuesto(self, base):
        """
        Impuesto único usando tabla SII (UTM)
        """
        from decimal import Decimal
        
        if base <= 0:
            return Decimal('0')

        utm_valor = UTM()
        
        if utm_valor == 0:
            return Decimal('0')

        base_utm = base / utm_valor

        tramo = TramoImpuesto.objects.filter(
            desde__lte=base_utm,
            hasta__gte=base_utm
        ).first()

        if not tramo:
            return Decimal('0')

        impuesto_utm = (base_utm * tramo.factor) - tramo.rebaja

        if impuesto_utm < 0:
            return Decimal('0')

        return impuesto_utm * utm_valor

    # -------------------------
    # CÁLCULO FINAL
    # -------------------------

    def calcular(self, bonos=0, horas_extra=0):
        from decimal import Decimal
        
        # Convertir a Decimal si vienen como string
        bonos = Decimal(str(bonos))
        horas_extra = Decimal(str(horas_extra))

        imponible, horas_extra_monto, gratificacion = self.calcular_imponible(
            bonos, horas_extra
        )

        afp = self.calcular_afp(imponible)
        salud = self.calcular_salud(imponible)
        afc = self.calcular_afc(imponible)

        base_tributable = imponible - afp - salud - afc

        impuesto = self.calcular_impuesto(base_tributable)

        total_descuentos = afp + salud + afc + impuesto
        liquido = imponible - total_descuentos

        return {
            "sueldo_base": self.sueldo_base,
            "horas_extra": horas_extra_monto,
            "gratificacion": gratificacion,
            "imponible": imponible,
            "afp": afp,
            "salud": salud,
            "afc": afc,
            "impuesto": impuesto,
            "liquido": liquido,
            "base_tributable": base_tributable,
        }