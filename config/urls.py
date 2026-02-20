from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core.views import dashboard, salir


urlpatterns = [
    path("admin/", admin.site.urls),

    # Dashboard principal
    path("", dashboard, name="dashboard"),

    # Auth
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="auth/login.html"),
        name="login",
    ),
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

