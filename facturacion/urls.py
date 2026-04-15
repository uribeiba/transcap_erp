from django.urls import path
from . import views

app_name = 'facturacion'
urlpatterns = [
    path('', views.FacturaListView.as_view(), name='lista'),
    path('nueva/', views.FacturaCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.FacturaDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.FacturaUpdateView.as_view(), name='editar'),
    path('<int:pk>/enviar-sii/', views.enviar_factura_sii, name='enviar_sii'),
    path('<int:pk>/pdf/', views.generar_pdf_factura, name='pdf'),
    path('api/cliente/<int:cliente_id>/', views.obtener_datos_cliente, name='api_cliente'),
    path('<int:pk>/emitir/', views.emitir_factura, name='emitir'),
    path('<int:pk>/eliminar/', views.eliminar_factura, name='eliminar'),
    path('informes/', views.informe_facturas, name='informe'),
    path('<int:pk>/anular/', views.anular_factura, name='anular'),
]