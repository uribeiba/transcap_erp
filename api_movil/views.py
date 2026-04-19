from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import ReporteChofer, FotoReporte, UbicacionChofer
from .serializers import ReporteChoferSerializer, FotoReporteSerializer, ViajeChoferSerializer
from operaciones.models import EstatusOperacionalViaje
from taller.models import Conductor
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

    
import csv
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from django.http import HttpResponse
from django.db.models import Q


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        rut = request.data.get('rut')
        password = request.data.get('password')
        
        # Limpiar RUT para comparación
        rut_limpio = rut.replace('.', '').replace('-', '') if rut else None
        
        try:
            # Buscar conductor por RUT (con o sin puntos)
            conductor = Conductor.objects.filter(
                Q(rut=rut) | Q(rut__icontains=rut_limpio) if rut_limpio else Q(rut=rut),
                activo=True
            ).first()
            
            if not conductor:
                # Intentar buscar por username del usuario
                try:
                    user = User.objects.get(username=rut_limpio)
                    conductor = Conductor.objects.get(usuario=user, activo=True)
                except:
                    pass
            
            if conductor and conductor.usuario:
                if conductor.usuario.check_password(password):
                    from rest_framework.authtoken.models import Token
                    token, _ = Token.objects.get_or_create(user=conductor.usuario)
                    return Response({
                        'success': True,
                        'token': token.key,
                        'conductor_id': conductor.id,
                        'nombre': f"{conductor.nombres} {conductor.apellidos}",
                        'rut': conductor.rut,
                    })
                else:
                    return Response({'success': False, 'error': 'Contraseña incorrecta'}, status=401)
            else:
                return Response({'success': False, 'error': 'Conductor no tiene usuario asociado'}, status=401)
                
        except Conductor.DoesNotExist:
            pass
        
        return Response({'success': False, 'error': 'Credenciales inválidas'}, status=401)


class ViajeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ViajeChoferSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Obtener el conductor a través del usuario autenticado
        try:
            conductor = Conductor.objects.get(usuario=self.request.user)
            return EstatusOperacionalViaje.objects.filter(
                conductor=conductor,
                fecha__gte=timezone.now().date() - timedelta(days=7)
            ).order_by('-fecha', '-turno')
        except Conductor.DoesNotExist:
            return EstatusOperacionalViaje.objects.none()


class ReporteChoferViewSet(viewsets.ModelViewSet):
    serializer_class = ReporteChoferSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            conductor = Conductor.objects.get(usuario=self.request.user)
            return ReporteChofer.objects.filter(conductor=conductor).order_by('-fecha')
        except Conductor.DoesNotExist:
            return ReporteChofer.objects.none()
    
    def perform_create(self, serializer):
        conductor = Conductor.objects.get(usuario=self.request.user)
        serializer.save(conductor=conductor)
    
    @action(detail=True, methods=['post'])
    def subir_foto(self, request, pk=None):
        reporte = self.get_object()
        imagen = request.FILES.get('imagen')
        descripcion = request.data.get('descripcion', '')
        
        if imagen:
            foto = FotoReporte.objects.create(
                reporte=reporte,
                imagen=imagen,
                descripcion=descripcion
            )
            return Response({'success': True, 'foto_id': foto.id})
        
        return Response({'success': False, 'error': 'No se recibió imagen'}, status=400)
    
    
    
@action(detail=False, methods=['post'])
def actualizar_ubicacion(self, request):
    """Actualiza la ubicación en tiempo real del chofer"""
    try:
        conductor = Conductor.objects.get(usuario=request.user)
        latitud = request.data.get('latitud')
        longitud = request.data.get('longitud')
        velocidad = request.data.get('velocidad')
        direccion = request.data.get('direccion', '')
        
        if latitud and longitud:
            UbicacionChofer.objects.create(
                conductor=conductor,
                latitud=latitud,
                longitud=longitud,
                velocidad=velocidad,
                direccion=direccion
            )
            return Response({'success': True})
        return Response({'success': False, 'error': 'Faltan coordenadas'}, status=400)
    except Conductor.DoesNotExist:
        return Response({'success': False, 'error': 'Conductor no encontrado'}, status=404)
    
    




@login_required
def panel_seguimiento(request):
    """Panel de seguimiento de choferes en tiempo real"""
    conductores = Conductor.objects.filter(activo=True)
    
    # Obtener última ubicación de cada conductor
    ubicaciones = []
    for conductor in conductores:
        ultima_ubicacion = conductor.ubicaciones.first()
        if ultima_ubicacion:
            ubicaciones.append({
                'conductor_id': conductor.id,
                'nombre': conductor.nombre_completo,
                'rut': conductor.rut,
                'latitud': float(ultima_ubicacion.latitud),
                'longitud': float(ultima_ubicacion.longitud),
                'velocidad': float(ultima_ubicacion.velocidad) if ultima_ubicacion.velocidad else 0,
                'timestamp': ultima_ubicacion.timestamp,
            })
    
    return render(request, 'api_movil/panel_seguimiento.html', {
        'ubicaciones': ubicaciones,
        'conductores': conductores,
    })
    
    




@login_required
def api_ubicaciones(request):
    """API para obtener ubicaciones de choferes (para el mapa)"""
    conductores = Conductor.objects.filter(activo=True)
    data = []
    for conductor in conductores:
        ultima = conductor.ubicaciones.first()
        if ultima:
            data.append({
                'conductor_id': conductor.id,
                'nombre': conductor.nombre_completo,
                'rut': conductor.rut,
                'latitud': float(ultima.latitud),
                'longitud': float(ultima.longitud),
                'velocidad': float(ultima.velocidad) if ultima.velocidad else 0,
                'timestamp': ultima.timestamp.strftime('%H:%M:%S'),
            })
    return JsonResponse(data, safe=False)




@login_required
@login_required
def obtener_reportes_chofer(request, conductor_id):
    """API para obtener los reportes de un chofer específico con filtros de fecha"""
    try:
        conductor = Conductor.objects.get(id=conductor_id)
        reportes = ReporteChofer.objects.filter(conductor=conductor).order_by('-fecha')
        
        # Aplicar filtros de fecha si existen
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                reportes = reportes.filter(fecha__date__gte=fecha_desde_obj)
            except:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                # Sumar un día para incluir todo el día
                fecha_hasta_obj = fecha_hasta_obj + timedelta(days=1)
                reportes = reportes.filter(fecha__date__lte=fecha_hasta_obj)
            except:
                pass
        
        data = []
        for r in reportes:
            fotos = []
            for foto in r.fotos.all():
                fotos.append({
                    'id': foto.id,
                    'imagen': foto.imagen.url if foto.imagen else None,
                    'descripcion': foto.descripcion,
                })
            
            data.append({
                'id': r.id,
                'estado': r.estado,
                'observaciones': r.observaciones,
                'fecha': r.fecha.strftime('%d/%m/%Y %H:%M:%S'),
                'fecha_iso': r.fecha.isoformat(),
                'ubicacion': {
                    'latitud': float(r.latitud) if r.latitud else None,
                    'longitud': float(r.longitud) if r.longitud else None,
                },
                'fotos': fotos,
            })
        
        return JsonResponse({'success': True, 'reportes': data, 'conductor': conductor.nombre_completo})
    except Conductor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conductor no encontrado'}, status=404)
    
    

@login_required
def exportar_reportes_excel(request, conductor_id):
    """Exportar reportes a Excel (CSV por simplicidad)"""
    try:
        conductor = Conductor.objects.get(id=conductor_id)
        reportes = ReporteChofer.objects.filter(conductor=conductor).order_by('-fecha')
        
        # Aplicar filtros
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if fecha_desde:
            reportes = reportes.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            from datetime import datetime, timedelta
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date() + timedelta(days=1)
            reportes = reportes.filter(fecha__date__lte=fecha_hasta_obj)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reportes_{conductor.rut}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Estado', 'Observaciones', 'Latitud', 'Longitud'])
        
        for r in reportes:
            writer.writerow([
                r.fecha.strftime('%d/%m/%Y %H:%M:%S'),
                r.estado,
                r.observaciones or '',
                r.latitud or '',
                r.longitud or '',
            ])
        
        return response
    except Conductor.DoesNotExist:
        return HttpResponse('Conductor no encontrado', status=404)

@login_required
def exportar_reportes_pdf(request, conductor_id):
    """Exportar reportes a PDF"""
    try:
        conductor = Conductor.objects.get(id=conductor_id)
        reportes = ReporteChofer.objects.filter(conductor=conductor).order_by('-fecha')
        
        # Aplicar filtros
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if fecha_desde:
            reportes = reportes.filter(fecha__date__gte=fecha_desde)
        if fecha_hasta:
            from datetime import datetime, timedelta
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date() + timedelta(days=1)
            reportes = reportes.filter(fecha__date__lte=fecha_hasta_obj)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reportes_{conductor.rut}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        elements.append(Paragraph(f"Reportes de {conductor.nombres} {conductor.apellidos}", title_style))
        elements.append(Spacer(1, 0.5 * cm))
        
        data = [['Fecha', 'Estado', 'Observaciones']]
        for r in reportes:
            data.append([
                r.fecha.strftime('%d/%m/%Y %H:%M:%S'),
                r.get_estado_display(),
                r.observaciones or ''
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return response
    except Conductor.DoesNotExist:
        return HttpResponse('Conductor no encontrado', status=404)
    


@login_required
def historial_rutas(request, conductor_id):
    """API para obtener el historial de ubicaciones de un chofer en un día específico"""
    try:
        conductor = Conductor.objects.get(id=conductor_id)
        
        # Obtener fecha del query param (default: hoy)
        fecha_str = request.GET.get('fecha')
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except:
                fecha = timezone.now().date()
        else:
            fecha = timezone.now().date()
        
        # Ubicaciones del día
        ubicaciones = UbicacionChofer.objects.filter(
            conductor=conductor,
            timestamp__date=fecha
        ).order_by('timestamp')
        
        data = []
        for u in ubicaciones:
            data.append({
                'latitud': float(u.latitud),
                'longitud': float(u.longitud),
                'velocidad': float(u.velocidad) if u.velocidad else 0,
                'timestamp': u.timestamp.strftime('%H:%M:%S'),
                'timestamp_iso': u.timestamp.isoformat(),
            })
        
        # Calcular distancia total
        distancia_total = 0
        for i in range(1, len(data)):
            from math import radians, sin, cos, sqrt, atan2
            lat1 = radians(data[i-1]['latitud'])
            lon1 = radians(data[i-1]['longitud'])
            lat2 = radians(data[i]['latitud'])
            lon2 = radians(data[i]['longitud'])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distancia_total += 6371 * c  # Radio de la Tierra en km
        
        return JsonResponse({
            'success': True,
            'conductor': conductor.nombre_completo,
            'fecha': fecha.strftime('%d/%m/%Y'),
            'ubicaciones': data,
            'total_puntos': len(data),
            'distancia_total': round(distancia_total, 2),
        })
    except Conductor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Conductor no encontrado'}, status=404)