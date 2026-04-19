from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core.views import salir
from dashboard.views import panel_control

urlpatterns = [
    path("admin/", admin.site.urls),

    # Dashboard principal
    path("", panel_control, name="dashboard"),

    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", salir, name="logout"),

    # Apps
    path("taller/", include("taller.urls")),
    path("inventario/", include("inventario.urls")),
    path("operaciones/", include("operaciones.urls")),
    path("centro-comercio/", include("centro_comercio.urls")),
    path("servicios/", include(("servicios.urls", "servicios"), namespace="servicios")),
    path("edp/", include(("edp.urls", "edp"), namespace="edp")),
    path("bitacora/", include(("bitacora.urls", "bitacora"), namespace="bitacora")),
    path("parametros/", include("parametros.urls")),
    path("suscripciones/", include("suscripciones.urls")),
    path('remuneraciones/', include('remuneraciones.urls')),
    path('facturacion/', include('facturacion.urls')),
    path('gastos/', include('gastos.urls')),
    path('compras/', include('compras.urls')),   # ← NUEVO: módulo de compras
    
    #Gestión de Roles (nuevo)
    path('roles/', include('roles.urls')),
  
    path('api/movil/', include(('api_movil.urls', 'api_movil'), namespace='api_movil')),
    path('analytics/', include('analytics.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)