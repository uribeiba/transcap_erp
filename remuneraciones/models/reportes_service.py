# remuneraciones/services/reportes_service.py
"""
Servicio de Reportes para Remuneraciones
----------------------------------------
Genera archivos para:
- Previred (Declaración de Remuneraciones)
- Libro de Remuneraciones
- Cotizaciones Previsionales
- Anexos SII
"""

from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from remuneraciones.models import Liquidacion, LiquidacionDetalle, Empleado, Contrato


class ReportesService:
    """Servicio para generar reportes y archivos de remuneraciones"""
    
    @staticmethod
    def generar_archivo_previred(periodo, rut_empresa, razon_social):
        """
        Genera archivo para Previred (Formato requerido por la AFP)
        
        Formato:
        TipoRegistro|RUT Empresa|RUT Trabajador|Nombre|Sueldo Base|Horas Extra|
        Bonos|Gratificación|Total Imponible|AFP|Salud|AFC|Líquido
        """
        lineas = []
        
        # Obtener liquidaciones del período
        liquidaciones = Liquidacion.objects.filter(periodo=periodo).select_related('empleado', 'contrato')
        
        for liq in liquidaciones:
            # Obtener detalles
            sueldo_base = liq.detalles.filter(concepto__codigo='SUELDO_BASE').first()
            horas_extra = liq.detalles.filter(concepto__codigo='HORAS_EXTRA').first()
            gratificacion = liq.detalles.filter(concepto__codigo='GRATIFICACION').first()
            afp = liq.detalles.filter(concepto__codigo='AFP').first()
            salud = liq.detalles.filter(concepto__codigo='SALUD').first()
            afc = liq.detalles.filter(concepto__codigo='AFC').first()
            
            linea = (
                f"P|{rut_empresa}|{liq.empleado.rut}|{liq.empleado.nombre_completo}|"
                f"{int(sueldo_base.monto) if sueldo_base else 0}|"
                f"{int(horas_extra.monto) if horas_extra else 0}|0|"
                f"{int(gratificacion.monto) if gratificacion else 0}|"
                f"{int(liq.total_haberes)}|"
                f"{int(afp.monto) if afp else 0}|"
                f"{int(salud.monto) if salud else 0}|"
                f"{int(afc.monto) if afc else 0}|"
                f"{int(liq.liquido_pagar)}"
            )
            lineas.append(linea)
        
        # Crear archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"previred_{periodo}_{rut_empresa}_{timestamp}.txt"
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write("\n".join(lineas))
        
        return nombre_archivo
    
    @staticmethod
    def generar_libro_remuneraciones(periodo, rut_empresa, razon_social):
        """
        Genera Libro de Remuneraciones en formato Excel (CSV para compatibilidad)
        """
        import csv
        
        liquidaciones = Liquidacion.objects.filter(periodo=periodo).select_related('empleado', 'contrato')
        
        nombre_archivo = f"libro_remuneraciones_{periodo}_{rut_empresa}.csv"
        
        with open(nombre_archivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            
            # Encabezados
            writer.writerow([
                'RUT Trabajador', 'Nombre Completo', 'Cargo', 'Área',
                'Sueldo Base', 'Horas Extra', 'Bonos', 'Gratificación',
                'Total Haberes', 'AFP', 'Salud', 'AFC', 'Impuesto',
                'Préstamos', 'Otros Descuentos', 'Total Descuentos',
                'Líquido a Pagar', 'Fecha Pago'
            ])
            
            for liq in liquidaciones:
                # Obtener detalles
                sueldo_base = liq.detalles.filter(concepto__codigo='SUELDO_BASE').first()
                horas_extra = liq.detalles.filter(concepto__codigo='HORAS_EXTRA').first()
                gratificacion = liq.detalles.filter(concepto__codigo='GRATIFICACION').first()
                afp = liq.detalles.filter(concepto__codigo='AFP').first()
                salud = liq.detalles.filter(concepto__codigo='SALUD').first()
                afc = liq.detalles.filter(concepto__codigo='AFC').first()
                impuesto = liq.detalles.filter(concepto__codigo='IMPUESTO').first()
                
                # Otros descuentos (préstamos, cooperativas, etc.)
                otros_descuentos = liq.detalles.filter(
                    concepto__tipo='DESCUENTO_VOLUNTARIO'
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                writer.writerow([
                    liq.empleado.rut,
                    liq.empleado.nombre_completo,
                    liq.empleado.cargo or '',
                    liq.empleado.area or '',
                    int(sueldo_base.monto) if sueldo_base else 0,
                    int(horas_extra.monto) if horas_extra else 0,
                    0,  # Bonos (se puede agregar después)
                    int(gratificacion.monto) if gratificacion else 0,
                    int(liq.total_haberes),
                    int(afp.monto) if afp else 0,
                    int(salud.monto) if salud else 0,
                    int(afc.monto) if afc else 0,
                    int(impuesto.monto) if impuesto else 0,
                    0,  # Préstamos (se puede agregar después)
                    int(otros_descuentos),
                    int(liq.total_descuentos),
                    int(liq.liquido_pagar),
                    liq.fecha_pago or ''
                ])
        
        return nombre_archivo
    
    @staticmethod
    def generar_cotizaciones_previred(periodo, rut_empresa, razon_social):
        """
        Genera archivo de cotizaciones para Previred
        (AFP, Salud, AFC, Seguro Cesantía)
        """
        from remuneraciones.models import Liquidacion, Contrato
        
        liquidaciones = Liquidacion.objects.filter(periodo=periodo).select_related('empleado', 'contrato')
        
        lineas = []
        
        for liq in liquidaciones:
            afp = liq.detalles.filter(concepto__codigo='AFP').first()
            salud = liq.detalles.filter(concepto__codigo='SALUD').first()
            afc = liq.detalles.filter(concepto__codigo='AFC').first()
            
            # Información de AFP del contrato
            nombre_afp = liq.contrato.afp.nombre if liq.contrato.afp else 'SIN AFP'
            
            linea = (
                f"C|{rut_empresa}|{liq.empleado.rut}|{liq.empleado.nombre_completo}|"
                f"{nombre_afp}|{int(liq.total_haberes)}|"
                f"{int(afp.monto) if afp else 0}|"
                f"{int(salud.monto) if salud else 0}|"
                f"{int(afc.monto) if afc else 0}"
            )
            lineas.append(linea)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"cotizaciones_previred_{periodo}_{rut_empresa}_{timestamp}.txt"
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write("\n".join(lineas))
        
        return nombre_archivo
    
    @staticmethod
    def generar_anexo_sii(periodo, rut_empresa, razon_social):
        """
        Genera Anexo SII para declaración de remuneraciones
        """
        from remuneraciones.models import Liquidacion
        
        liquidaciones = Liquidacion.objects.filter(periodo=periodo).select_related('empleado')
        
        lineas = []
        
        for liq in liquidaciones:
            linea = (
                f"{rut_empresa}|{liq.periodo}|{liq.empleado.rut}|"
                f"{liq.empleado.nombres} {liq.empleado.apellidos}|"
                f"{int(liq.total_haberes)}|{int(liq.total_descuentos)}|"
                f"{int(liq.liquido_pagar)}"
            )
            lineas.append(linea)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"anexo_sii_{periodo}_{rut_empresa}_{timestamp}.txt"
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write("\n".join(lineas))
        
        return nombre_archivo
    
    @staticmethod
    def generar_resumen_ejecutivo(periodo, rut_empresa, razon_social):
        """
        Genera resumen ejecutivo en formato CSV con estadísticas
        """
        import csv
        from django.db.models import Count, Avg, Sum
        
        liquidaciones = Liquidacion.objects.filter(periodo=periodo)
        
        if not liquidaciones.exists():
            return None
        
        # Estadísticas
        stats = liquidaciones.aggregate(
            total_empleados=Count('id'),
            total_haberes=Sum('total_haberes'),
            total_descuentos=Sum('total_descuentos'),
            total_liquido=Sum('liquido_pagar'),
            promedio_liquido=Avg('liquido_pagar'),
            max_liquido=Sum('liquido_pagar'),
            min_liquido=Sum('liquido_pagar')
        )
        
        nombre_archivo = f"resumen_ejecutivo_{periodo}_{rut_empresa}.csv"
        
        with open(nombre_archivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            
            writer.writerow(['RESUMEN EJECUTIVO DE REMUNERACIONES'])
            writer.writerow([f'Período: {periodo}'])
            writer.writerow([f'Empresa: {razon_social}'])
            writer.writerow([f'RUT: {rut_empresa}'])
            writer.writerow([])
            writer.writerow(['INDICADOR', 'VALOR'])
            writer.writerow(['Total Empleados', stats['total_empleados']])
            writer.writerow(['Total Haberes', f"${stats['total_haberes']:,.0f}"])
            writer.writerow(['Total Descuentos', f"${stats['total_descuentos']:,.0f}"])
            writer.writerow(['Total Líquido a Pagar', f"${stats['total_liquido']:,.0f}"])
            writer.writerow(['Promedio Líquido por Empleado', f"${stats['promedio_liquido']:,.0f}"])
            
            # Agregar detalle por empleado
            writer.writerow([])
            writer.writerow(['DETALLE POR EMPLEADO'])
            writer.writerow(['RUT', 'Nombre', 'Total Haberes', 'Total Descuentos', 'Líquido'])
            
            for liq in liquidaciones.select_related('empleado'):
                writer.writerow([
                    liq.empleado.rut,
                    liq.empleado.nombre_completo,
                    f"${liq.total_haberes:,.0f}",
                    f"${liq.total_descuentos:,.0f}",
                    f"${liq.liquido_pagar:,.0f}"
                ])
        
        return nombre_archivo