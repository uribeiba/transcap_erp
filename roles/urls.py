from django.urls import path
from . import views

app_name = 'roles'
urlpatterns = [
    path('', views.panel_roles, name='panel'),
    path('asignar/', views.asignar_rol, name='asignar_rol'),
    path('crear/', views.crear_rol, name='crear_rol'),
    path('crear-usuario/', views.crear_usuario, name='crear_usuario'),  # ← Nueva
]