# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='repuestos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('', views.listar_repuestos, name='listar_repuestos'),
    path('nuevo/', views.crear_repuesto, name='crear_repuesto'),
    path('editar/<int:pk>/', views.editar_repuesto, name='editar_repuesto'),
    path('eliminar/<int:pk>/', views.eliminar_repuesto, name='eliminar_repuesto'),
    
    path('admin/dashboard/', views.dashboard, name='dashboard'),
    path('admin/clientes/', views.listar_clientes, name='listar_clientes'),
]