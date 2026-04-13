# urls.py - VERSIÓN CORREGIDA (PDF ANTES DE DETALLE)
# Reemplaza todo el contenido de tu urls.py con este código

from django.urls import path
from . import views

app_name = "centro_comercio"

urlpatterns = [
    # =========================
    # HOME / PANEL PRINCIPAL
    # =========================
    path("", views.centro_home, name="home"),

    # =========================
    # CLIENTES (TODAS LAS RUTAS EXISTENTES SE MANTIENEN)
    # =========================
    path("clientes/", views.clientes_panel, name="clientes_panel"),
    path("clientes/lista/", views.clientes_lista, name="clientes_lista"),
    path("clientes/nuevo/", views.cliente_form, name="cliente_nuevo"),
    path("clientes/<int:pk>/", views.cliente_detalle, name="cliente_detalle"),
    path("clientes/<int:pk>/editar/", views.cliente_form, name="cliente_editar"),
    path("clientes/<int:pk>/eliminar/", views.cliente_eliminar, name="cliente_eliminar"),

    # =========================
    # COTIZACIONES
    # =========================
    # Panel y listado
    path("cotizaciones/", views.cotizaciones_panel, name="cotizaciones_panel"),
    path("cotizaciones/lista/", views.cotizaciones_lista, name="cotizaciones_lista"),

    # Crear (mantiene compatibilidad)
    path("cotizaciones/nuevo/", views.cotizacion_form, name="cotizacion_nuevo"),

    # =========================
    # RUTAS ESPECÍFICAS CON <int:pk> - DEBEN IR EN ORDEN CORRECTO
    # =========================
    # 1. PDF (más específica, debe ir primero)
    path("cotizaciones/<int:pk>/pdf/", 
         views.cotizacion_pdf, 
         name="cotizacion_pdf"),
    
    # 2. Resumen API
    path("cotizaciones/<int:pk>/resumen/", 
         views.cotizacion_resumen_api, 
         name="cotizacion_resumen_api"),
    
    # 3. Duplicar
    path("cotizaciones/<int:pk>/duplicar/", 
         views.cotizacion_duplicar, 
         name="cotizacion_duplicar"),
    
    # 4. Cambiar estado
    path("cotizaciones/<int:pk>/cambiar-estado/", 
         views.cotizacion_cambiar_estado, 
         name="cotizacion_cambiar_estado"),
    
    # 5. Editar
    path("cotizaciones/<int:pk>/editar/", 
         views.cotizacion_form, 
         name="cotizacion_editar"),
    
    # 6. Eliminar
    path("cotizaciones/<int:pk>/eliminar/", 
         views.cotizacion_eliminar, 
         name="cotizacion_eliminar"),
    
    # 7. Formulario con pk
    path("cotizaciones/<int:pk>/form/", 
         views.cotizacion_form, 
         name="cotizacion_form"),
    
    # 8. Detalle (la más genérica, debe ir al final)
    path("cotizaciones/<int:pk>/", 
         views.cotizacion_detalle, 
         name="cotizacion_detalle"),

    # =========================
    # FORMULARIO SIN PK (DEBE IR DESPUÉS DE LAS RUTAS CON PK)
    # =========================
    path("cotizaciones/form/", 
         views.cotizacion_form, 
         name="cotizacion_form"),

    # =========================
    # API DE CLIENTE (NO TIENE PK, PUEDE IR EN CUALQUIER LUGAR)
    # =========================
    path("cotizaciones/cliente/<int:cliente_id>/info/", 
         views.cotizacion_cliente_info, 
         name="cotizacion_cliente_info"),

    # =========================
    # VENDEDORES
    # =========================
    path("vendedores/api/", 
         views.vendedores_lista_api, 
         name="vendedores_api"),
]

# =========================
# NOTAS IMPORTANTES:
# =========================
# 1. El ORDEN de las rutas con <int:pk> es CRÍTICO
# 2. Las rutas más específicas (como /pdf/) deben ir ANTES
# 3. La ruta genérica <int:pk>/ debe ir al FINAL
# 4. URL del PDF: /centro_comercio/cotizaciones/26/pdf/