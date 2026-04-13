# remuneraciones/services/sii_integration.py
from decimal import Decimal
from django.utils import timezone
from remuneraciones.models import Liquidacion, Honorario

class SIIExporter:
    """Genera archivos planos para declaraciones juradas SII (DJ 1847 y 1879)"""
    
    @staticmethod
    def generar_dj1847(periodo, rut_empresa, razon_social):
        """
        Genera archivo TXT para DJ 1847 (Honorarios)
        Formato: Secuencia | RUT Beneficiario | Nombre | Monto Bruto | Monto Exento | Tasa Retención (12.25%) | Monto Retenido
        """
        lineas = []
        honorarios = Honorario.objects.filter(periodo=periodo, estado='PAGADO')
        secuencia = 1
        for h in honorarios:
            monto_retencion = h.monto_bruto * Decimal('0.1225')
            linea = f"{secuencia:06d}|{h.rut_beneficiario}|{h.nombre_beneficiario}|{int(h.monto_bruto)}|0|12.25|{int(monto_retencion)}"
            lineas.append(linea)
            secuencia += 1
        
        header = f"{rut_empresa}|{razon_social}|{periodo}|HONORARIOS|DJ1847|{timezone.now().strftime('%Y%m%d%H%M%S')}"
        contenido = "\n".join([header] + lineas)
        
        with open(f"dj1847_{periodo}_{rut_empresa}.txt", "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"dj1847_{periodo}_{rut_empresa}.txt"
    
    @staticmethod
    def generar_dj1879(periodo, rut_empresa, razon_social):
        """
        Genera archivo TXT para DJ 1879 (Liquidaciones de Sueldo - Detalle de trabajadores)
        Formato: RUT Trabajador | Nombres | Sueldo Imponible | Total Haberes | Total Descuentos | Líquido a Pagar
        """
        lineas = []
        liquidaciones = Liquidacion.objects.filter(periodo=periodo).select_related('empleado', 'contrato')
        for liq in liquidaciones:
            linea = f"{liq.empleado.rut}|{liq.empleado.nombre_completo}|{int(liq.contrato.sueldo_base)}|{int(liq.total_haberes)}|{int(liq.total_descuentos)}|{int(liq.liquido_pagar)}"
            lineas.append(linea)
        
        header = f"{rut_empresa}|{razon_social}|{periodo}|LIQUIDACIONES_SUELDOS|DJ1879|{timezone.now().strftime('%Y%m%d%H%M%S')}"
        contenido = "\n".join([header] + lineas)
        
        with open(f"dj1879_{periodo}_{rut_empresa}.txt", "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"dj1879_{periodo}_{rut_empresa}.txt"