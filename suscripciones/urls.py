from django.urls import path
from . import views

app_name = "suscripciones"

urlpatterns = [
    path("planes/", views.planes_list, name="planes_list"),
    path("planes/crear/", views.plan_crear, name="plan_crear"),
    path("planes/<int:plan_id>/editar/", views.plan_editar, name="plan_editar"),
]
