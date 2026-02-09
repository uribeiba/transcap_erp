from django.contrib import admin
from django.urls import path, include
from core.views import dashboard
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Dashboard principal
    path("", dashboard, name="dashboard"),

    # Auth propio
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="auth/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),

    # Apps
    path("taller/", include("taller.urls")),
    path("inventario/", include("inventario.urls")),
    path("operaciones/", include("operaciones.urls")),
    path("centro-comercio/", include("centro_comercio.urls")),
    path("servicios/", include("servicios.urls", namespace="servicios")),
    path("edp/", include(("edp.urls", "edp"), namespace="edp")),
    path("bitacora/", include(("bitacora.urls", "bitacora"), namespace="bitacora")),
    path("parametros/", include("parametros.urls")),
    path("suscripciones/", include("suscripciones.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
