from django.urls import path
from . import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.panel_control, name='dashboard'),
]