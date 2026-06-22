# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Módulo Público (Landing Page)
    path('', views.quienes_somos, name='quienes_somos'),
    
    # Módulo de Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='repuestos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Panel Principal de Control (Dashboard)
    path('admin/dashboard/', views.dashboard, name='dashboard'),

    # Módulo de Administración de Clientes
    path('admin/clientes/', views.listar_clientes, name='listar_clientes'),
    path('admin/clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('admin/clientes/eliminar/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    
    # Módulo de Catálogo de Repuestos (Interfaz Unificada)
    path('repuestos/', views.listar_repuestos, name='listar_repuestos'),
    path('repuestos/editar/<int:pk>/', views.editar_repuesto, name='editar_repuesto'),
    path('repuestos/eliminar/<int:pk>/', views.eliminar_repuesto, name='eliminar_repuesto'),
]