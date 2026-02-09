from django.urls import path
from . import views

app_name = "operaciones"

urlpatterns = [
    path("tablero/", views.tablero_diario, name="tablero_diario"),
    path("crear/", views.crear_rapido, name="crear_rapido"),

    # edición multiusuario
    path("registro/<int:pk>/detalle/", views.registro_detalle_json, name="registro_detalle_json"),
    path("registro/<int:pk>/lock/", views.registro_lock, name="registro_lock"),
    path("registro/<int:pk>/unlock/", views.registro_unlock, name="registro_unlock"),
    path("registro/<int:pk>/guardar/", views.registro_guardar, name="registro_guardar"),

    # ✅ mantener bloqueo vivo (modal abierto)
    path("registro/<int:pk>/heartbeat/", views.registro_heartbeat, name="registro_heartbeat"),

    # ✅ presencia multiusuario
    path("presencia/ping/", views.presencia_ping, name="presencia_ping"),
    path("presencia/lista/", views.presencia_lista, name="presencia_lista"),

    # ✅ refresh liviano
    path("tablero/refresh/", views.tablero_refresh, name="tablero_refresh"),
]
