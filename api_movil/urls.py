from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api_movil'  # ← Agrega esta línea

router = DefaultRouter()
router.register(r'reportes', views.ReporteChoferViewSet, basename='reportes')
router.register(r'viajes', views.ViajeViewSet, basename='viajes')

urlpatterns = [
    path('auth/login/', views.AuthViewSet.as_view({'post': 'login'}), name='chofer_login'),
    path('panel/', views.panel_seguimiento, name='panel_seguimiento'),
    path('api/ubicaciones/', views.api_ubicaciones, name='api_ubicaciones'),
    path('', include(router.urls)),
    path('api/reportes/<int:conductor_id>/', views.obtener_reportes_chofer, name='reportes_chofer'),
    path('api/reportes/<int:conductor_id>/exportar/excel/', views.exportar_reportes_excel, name='exportar_reportes_excel'),
    path('api/reportes/<int:conductor_id>/exportar/pdf/', views.exportar_reportes_pdf, name='exportar_reportes_pdf'),
]