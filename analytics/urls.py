from django.urls import path
from . import views

app_name = 'analytics'
urlpatterns = [

    path('dashboard/', views.dashboard_estadisticas, name='dashboard'),
    path('cargar/combustible/', views.cargar_combustible, name='cargar_combustible'),
    path('cargar/peaje/', views.cargar_peaje, name='cargar_peaje'),
    path('cargar/costo-viaje/', views.cargar_costo_viaje, name='cargar_costo_viaje'),
    path('lista-gastos/', views.lista_gastos, name='lista_gastos'),
    ]