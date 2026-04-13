# remuneraciones/urls.py
from django.urls import path
from . import views

app_name = 'remuneraciones'

urlpatterns = [
    # Vistas HTML
    path('dashboard/', views.dashboard, name='dashboard'),
    path('empleados/', views.empleados, name='empleados'),
    path('contratos/', views.contratos, name='contratos'),
    path('liquidaciones/', views.liquidaciones, name='liquidaciones'),
    path('honorarios/', views.honorarios, name='honorarios'),
    path('liquidaciones/detalle/<int:liquidacion_id>/', views.detalle_liquidacion, name='detalle_liquidacion'),
    path('parametros/', views.parametros, name='parametros'),
    
    # API - Administración de Liquidaciones (solo staff)
    path('admin/liquidaciones/', views.liquidaciones_administrar, name='admin_liquidaciones'),
    path('api/liquidaciones/<int:liquidacion_id>/editar/', views.editar_liquidacion, name='editar_liquidacion'),
    path('api/liquidaciones/<int:liquidacion_id>/eliminar/', views.eliminar_liquidacion, name='eliminar_liquidacion'),
    path('api/liquidaciones/<int:liquidacion_id>/', views.api_liquidacion_detail, name='api_liquidacion_detail'),  # ← NUEVO
    
    # API - Dashboard
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/dashboard/evolucion/', views.dashboard_evolucion, name='dashboard_evolucion'),
    path('api/dashboard/conceptos/', views.dashboard_conceptos, name='dashboard_conceptos'),
    path('api/dashboard/ultimas-liquidaciones/', views.dashboard_ultimas_liquidaciones, name='dashboard_ultimas_liquidaciones'),
    
    # API - Empleados CRUD
    path('api/empleados/', views.api_empleados_list, name='api_empleados_list'),
    path('api/empleados/<int:empleado_id>/', views.api_empleado_detail, name='api_empleado_detail'),
    
    # API - AFP y Salud
    path('api/afp/', views.api_afp_list, name='api_afp_list'),
    path('api/afp/<int:afp_id>/', views.api_afp_detail, name='api_afp_detail'),
    path('api/salud/', views.api_salud_list, name='api_salud_list'),
    path('api/salud/<int:salud_id>/', views.api_salud_detail, name='api_salud_detail'),
    
    # API - Contratos CRUD
    path('api/contratos/', views.api_contratos_list, name='api_contratos_list'),
    path('api/contratos/<int:contrato_id>/', views.api_contrato_detail, name='api_contrato_detail'),
    
    # API - Honorarios CRUD
    path('api/honorarios/', views.api_honorarios_list, name='api_honorarios_list'),
    path('api/honorarios/<int:honorario_id>/', views.api_honorario_detail, name='api_honorario_detail'),
    
    # API - Liquidaciones
    path('liquidaciones/calcular/<int:contrato_id>/', views.calcular_liquidacion, name='calcular_liquidacion'),
    path('liquidaciones/guardar/<int:contrato_id>/', views.guardar_liquidacion, name='guardar_liquidacion'),
    path('liquidaciones/generar_periodo/', views.generar_liquidaciones_periodo, name='generar_liquidaciones_periodo'),
    path('liquidaciones/resumen/', views.resumen_mensual, name='resumen_mensual'),
    path('api/liquidaciones/', views.api_liquidaciones_list, name='api_liquidaciones_list'),
    
    # API - Conceptos
    path('api/conceptos/', views.api_conceptos_list, name='api_conceptos_list'),
    path('api/conceptos/<int:concepto_id>/', views.api_concepto_detail, name='api_concepto_detail'),
    
    
    # En remuneraciones/urls.py, agrega estas líneas dentro de urlpatterns:

# Reportes
path('reportes/', views.reportes, name='reportes'),
path('reportes/previred/', views.generar_reporte_previred, name='reporte_previred'),
path('reportes/cotizaciones/', views.generar_cotizaciones_previred, name='reporte_cotizaciones'),
path('reportes/libro/', views.generar_libro_remuneraciones, name='reporte_libro'),
path('reportes/anexo/', views.generar_anexo_sii, name='reporte_anexo'),
path('reportes/resumen/', views.generar_resumen_ejecutivo, name='reporte_resumen'),
]