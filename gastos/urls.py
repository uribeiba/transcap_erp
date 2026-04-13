# gastos/urls.py
from django.urls import path
from . import views

app_name = 'gastos'
urlpatterns = [
    # Gastos normales
    path('', views.GastoListView.as_view(), name='lista'),
    path('nuevo/', views.GastoCreateView.as_view(), name='crear'),
    path('<int:pk>/', views.GastoDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.GastoUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.GastoDeleteView.as_view(), name='eliminar'),

    # Gastos recurrentes
    path('recurrentes/', views.RecurrenteListView.as_view(), name='recurrentes'),
    path('recurrentes/nuevo/', views.RecurrenteCreateView.as_view(), name='recurrente_crear'),
    path('recurrentes/<int:pk>/editar/', views.RecurrenteUpdateView.as_view(), name='recurrente_editar'),
    path('recurrentes/<int:pk>/eliminar/', views.RecurrenteDeleteView.as_view(), name='recurrente_eliminar'),
    path('dashboard/', views.dashboard_gastos, name='dashboard'),

    # Categorías de gastos (nuevo)
    path('categorias/', views.CategoriaListView.as_view(), name='categorias'),
    path('categorias/nueva/', views.CategoriaCreateView.as_view(), name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_eliminar'),
]