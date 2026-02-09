from django.urls import path
from . import views

app_name = "parametros"

urlpatterns = [
    path("", views.panel, name="panel"),

    path("empresa/editar/", views.empresa_update, name="empresa_editar"),
    path("empresa/logo/", views.empresa_logo_update, name="empresa_logo_update"),

    path("sucursal/crear/", views.sucursal_create, name="sucursal_crear"),
    path("sucursal/<int:pk>/editar/", views.sucursal_update, name="sucursal_editar"),
    path("sucursal/<int:pk>/eliminar/", views.sucursal_delete, name="sucursal_eliminar"),

    path("usuario/<int:pk>/eliminar/", views.usuario_delete, name="usuario_eliminar"),
    path("usuarios/crear/", views.usuario_create, name="usuario_crear"),
    path("usuarios/<int:pk>/editar/", views.usuario_update, name="usuario_editar"),

    path("empresas/", views.empresas_panel, name="empresas_panel"),
    path("empresas/crear/", views.empresa_create, name="empresa_crear"),
    path("empresas/<int:pk>/editar/", views.empresa_admin_update, name="empresa_admin_editar"),
    path("empresas/<int:pk>/logo/", views.empresa_admin_logo_update, name="empresa_admin_logo_update"),

    # ✅ NUEVO: cambiar empresa activa (tenant) + reset
    path("empresas/<int:pk>/entrar/", views.empresa_switch, name="empresa_entrar"),
    path("empresas/salir/", views.empresa_switch_clear, name="empresa_salir"),
    path("empresas/<int:pk>/entrar/", views.empresa_entrar, name="empresa_entrar"),
    path("empresas/<int:empresa_id>/cambiar-plan/", views.empresa_cambiar_plan, name="empresa_cambiar_plan"),

    # parametros/urls.py (AGREGA)
    path("planes/", views.planes_panel, name="planes_panel"),
    path("planes/crear/", views.plan_crear, name="plan_crear"),
    path("planes/<int:plan_id>/editar/", views.plan_editar, name="plan_editar"),
    path("planes/<int:plan_id>/eliminar/", views.plan_eliminar, name="plan_eliminar"),
    

]
