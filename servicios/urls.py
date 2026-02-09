from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    path('', views.servicios_panel, name='servicios_panel'),
    path('lista/', views.servicios_lista, name='servicios_lista'),
    path('nuevo/', views.servicio_form, name='servicio_nuevo'),
    path('editar/<int:pk>/', views.servicio_form, name='servicio_editar'),
    path('detalle/<int:pk>/', views.servicio_detalle, name='servicio_detalle'),
    path('eliminar/<int:pk>/', views.servicio_eliminar, name='servicio_eliminar'),
    path('nuevo-desde-cotizacion/<int:cotizacion_id>/', 
         views.servicio_nuevo_desde_cotizacion, 
         name='servicio_nuevo_desde_cotizacion'),
]