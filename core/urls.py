# core/urls.py
"""
Configuración de URLs para la aplicación core.

Organización:
- Vistas públicas (sin login)
- Autenticación (Django built-in)
- Dashboard
- CRUD Clientes (CBV)
- CRUD Repuestos (CBV)
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ==========================================
    # Módulo Público (Landing Page)
    # ==========================================
    path('', views.QuienesSomosView.as_view(), name='quienes_somos'),
    path('inicio/', views.HomeView.as_view(), name='home'),
    
    # ==========================================
    # Módulo de Autenticación (Django Built-in)
    # ==========================================
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='repuestos/login.html',
            redirect_authenticated_user=True  # Si ya logueado, redirige a dashboard
        ),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='login'),
        name='logout'
    ),
    
    # ==========================================
    # Panel Principal (Dashboard)
    # ==========================================
    path('admin/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # ==========================================
    # CRUD Clientes (Class-Based Views)
    # ==========================================
    path(
        'admin/clientes/',
        views.ClienteListView.as_view(),
        name='cliente_listar'
    ),
    path(
        'admin/clientes/crear/',
        views.ClienteCreateView.as_view(),
        name='cliente_crear'
    ),
    path(
        'admin/clientes/editar/<int:pk>/',
        views.ClienteUpdateView.as_view(),
        name='cliente_editar'
    ),
    path(
        'admin/clientes/eliminar/<int:pk>/',
        views.ClienteDeleteView.as_view(),
        name='cliente_eliminar'
    ),
    
    # ==========================================
    # CRUD Repuestos (Class-Based Views)
    # ==========================================
    path(
        'repuestos/',
        views.RepuestoListView.as_view(),
        name='repuesto_listar'
    ),
    path(
        'repuestos/crear/',
        views.RepuestoCreateView.as_view(),
        name='repuesto_crear'
    ),
    path(
        'repuestos/editar/<int:pk>/',
        views.RepuestoUpdateView.as_view(),
        name='repuesto_editar'
    ),
    path(
        'repuestos/eliminar/<int:pk>/',
        views.RepuestoDeleteView.as_view(),
        name='repuesto_eliminar'
    ),
    path(
        'repuestos/<int:pk>/',
        views.RepuestoDetailView.as_view(),
        name='repuesto_detalle'
    ),
]