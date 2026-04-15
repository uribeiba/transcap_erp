from django.urls import path
from . import views

app_name = 'roles'
urlpatterns = [
    path('', views.panel_roles, name='panel'),
    path('asignar/', views.asignar_rol, name='asignar_rol'),
    path('crear/', views.crear_rol, name='crear_rol'),
    path('crear-usuario/', views.crear_usuario, name='crear_usuario'),  # ← Nueva
    path('editar-usuario/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),  # ← Nueva
    path('eliminar-usuario/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),  # ← Nueva
]