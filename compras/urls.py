from django.urls import path
from . import views

app_name = 'compras'
urlpatterns = [
    # Proveedores
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedores'),
    path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor_crear'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor_editar'),
    path('proveedores/<int:pk>/eliminar/', views.ProveedorDeleteView.as_view(), name='proveedor_eliminar'),

    # Órdenes de Compra
    path('ordenes/', views.OrdenCompraListView.as_view(), name='ordenes'),
    path('ordenes/nueva/', views.OrdenCompraCreateView.as_view(), name='orden_crear'),
    path('ordenes/<int:pk>/', views.OrdenCompraDetailView.as_view(), name='orden_detalle'),
    path('ordenes/<int:pk>/editar/', views.OrdenCompraUpdateView.as_view(), name='orden_editar'),
    path('ordenes/<int:pk>/eliminar/', views.OrdenCompraDeleteView.as_view(), name='orden_eliminar'),

    # Dashboard y Exportaciones
    path('dashboard/', views.dashboard_compras, name='dashboard'),
    path('exportar/excel/', views.exportar_ordenes_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_ordenes_pdf, name='exportar_pdf'),
]