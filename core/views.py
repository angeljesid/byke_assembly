"""
Vistas basadas en clases (Class-Based Views - CBV) para Bike Assembly.

Ventajas de CBV sobre FBV:
- Separación clara de GET/POST (métodos get/post)
- Herencia y reutilización (Mixin, genéricas)
- Paginación automática (ListView)
- Form handling automático (CreateView, UpdateView)
- Menos código repetitivo (boilerplate)
- Mejor testabilidad (métodos aislados)
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.db.models import Q
from django.contrib import messages

from .models import Cliente, Repuesto, Categoria
from .forms import (
    ClienteForm,
    RepuestoForm,
    RepuestoFiltroForm,
)
from .repositories import ClienteRepository, RepuestoRepository, CategoriaRepository


# ==========================================
# Mixins Comunes
# ==========================================

class SeccionContextMixin:
    """
    Mixin para agregar 'seccion' al contexto.
    Usado para marcar item activo en sidebar.
    """
    seccion: str = ''
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = self.seccion
        return context


class RepositorioMixin:
    """
    Mixin para inyectar repositorios en vistas.
    Facilita testing (mock repositorio).
    """
    cliente_repo = ClienteRepository()
    repuesto_repo = RepuestoRepository()
    categoria_repo = CategoriaRepository()


# ==========================================
# Vistas Públicas (Sin login)
# ==========================================

class QuienesSomosView(TemplateView):
    """
    Landing page pública - ¿Quiénes Somos?
    
    Template: repuestos/quienes_somos.html
    No requiere autenticación.
    """
    template_name = 'repuestos/quienes_somos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'publico'
        return context


class HomeView(TemplateView):
    """
    Página de inicio alternativa (redirige a landing).
    
    Template: repuestos/inicio.html (legacy)
    """
    template_name = 'repuestos/inicio.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'home'
        return context


# ==========================================
# Vistas Autenticadas - Dashboard
# ==========================================

class DashboardView(LoginRequiredMixin, SeccionContextMixin, TemplateView):
    """
    Panel principal tras login.
    
    Template: repuestos/inicio.html
    Requiere: LoginRequiredMixin
    """
    template_name = 'repuestos/inicio.html'
    seccion = 'home'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Estadísticas rápidas para el dashboard
        context['stats'] = {
            'total_clientes': Cliente.objects.count(),
            'total_repuestos': Repuesto.objects.count(),
            'stock_bajo': Repuesto.objects.filter(stock__lte=5).count(),
            'agotados': Repuesto.objects.filter(stock=0).count(),
        }
        return context


# ==========================================
# Vistas CRUD - Clientes
# ==========================================

class ClienteListView(LoginRequiredMixin, SeccionContextMixin, RepositorioMixin, ListView):
    """
    Listado paginado de clientes con búsqueda.
    
    Template: repuestos/clientes.html
    Context: page_obj (Paginator), clientes (page_obj.object_list), form (ClienteForm)
    Paginación: 25 por página
    Búsqueda: GET ?q=termino
    """
    model = Cliente
    template_name = 'repuestos/clientes.html'
    context_object_name = 'clientes'
    paginate_by = 25
    seccion = 'clientes'
    login_url = 'login'
    
    def get_queryset(self):
        """Aplica búsqueda si hay parámetro 'q'."""
        queryset = self.cliente_repo.obtener_todos()
        busqueda = self.request.GET.get('q', '').strip()
        if busqueda:
            queryset = self.cliente_repo.buscar(busqueda)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Formulario para crear/editar en mismo template
        context['form'] = ClienteForm()
        context['busqueda'] = self.request.GET.get('q', '')
        return context


class ClienteCreateView(LoginRequiredMixin, SuccessMessageMixin, RepositorioMixin, CreateView):
    """
    Crear nuevo cliente.
    
    Form: ClienteForm (validación server-side)
    Template: repuestos/clientes.html (mismo que listado)
    Success: Redirect a listado con mensaje
    """
    model = Cliente
    form_class = ClienteForm
    template_name = 'repuestos/clientes.html'
    success_url = reverse_lazy('cliente_listar')
    success_message = 'Cliente "%(nombre)s" creado correctamente'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'clientes'
        context['es_crear'] = True
        # Pasar listado para template compartido
        context['clientes'] = self.cliente_repo.obtener_todos()[:25]
        return context
    
    def form_invalid(self, form):
        """Agrega errores a messages framework para toast."""
        messages.error(self.request, 'Por favor corrija los errores en el formulario')
        return super().form_invalid(form)


class ClienteUpdateView(LoginRequiredMixin, SuccessMessageMixin, RepositorioMixin, UpdateView):
    """
    Editar cliente existente.
    
    Form: ClienteForm (pre-poblado con instance)
    Template: repuestos/clientes.html
    Success: Redirect a listado con mensaje
    """
    model = Cliente
    form_class = ClienteForm
    template_name = 'repuestos/clientes.html'
    success_url = reverse_lazy('cliente_listar')
    success_message = 'Cliente "%(nombre)s" actualizado correctamente'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'clientes'
        context['es_editar'] = True
        context['cliente_editar'] = self.object
        context['clientes'] = self.cliente_repo.obtener_todos()[:25]
        return context


class ClienteDeleteView(LoginRequiredMixin, SuccessMessageMixin, RepositorioMixin, DeleteView):
    """
    Eliminar cliente (con confirmación).
    
    Template: repuestos/clientes_confirm_delete.html (modal/inline)
    Success: Redirect a listado con mensaje
    """
    model = Cliente
    template_name = 'repuestos/clientes_confirm_delete.html'
    success_url = reverse_lazy('cliente_listar')
    success_message = 'Cliente "%(nombre)s" eliminado correctamente'
    login_url = 'login'
    
    def delete(self, request, *args, **kwargs):
        """Captura nombre antes de borrar para mensaje."""
        self.object = self.get_object()
        nombre = self.object.nombre
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Cliente "{nombre}" eliminado correctamente')
        return response


# ==========================================
# Vistas CRUD - Repuestos
# ==========================================

class RepuestoListView(LoginRequiredMixin, SeccionContextMixin, RepositorioMixin, ListView):
    """
    Listado paginado de repuestos con filtros avanzados.
    
    Template: repuestos/listar.html
    Context: page_obj, repuestos, filtro_form, choices (compatibilidad)
    Paginación: 20 por página
    Filtros: GET ?busqueda=...&categoria_filtro=...&compatibilidad_filtro=...&orden=...
    """
    model = Repuesto
    template_name = 'repuestos/listar.html'
    context_object_name = 'repuestos'
    paginate_by = 20
    seccion = 'repuestos'
    login_url = 'login'
    
    def get_queryset(self):
        """Aplica filtros y ordenamiento usando RepuestoRepository."""
        # Obtener parámetros GET
        busqueda = self.request.GET.get('busqueda', '').strip()
        categoria_filtro = self.request.GET.get('categoria_filtro', '').strip()
        compatibilidad_filtro = self.request.GET.get('compatibilidad_filtro', '').strip()
        orden = self.request.GET.get('orden', '').strip()
        
        # Delegar a repositorio
        return self.repuesto_repo.filtrar_y_ordenar(
            busqueda=busqueda,
            categoria_filtro=categoria_filtro,
            compatibilidad_filtro=compatibilidad_filtro,
            orden=orden
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formulario de filtros (para mantener valores en template)
        context['filtro_form'] = RepuestoFiltroForm(self.request.GET)
        
        # Choices para select de compatibilidad
        context['choices'] = Repuesto.COMPATIBILIDAD_CHOICES
        
        # Formulario para crear/editar en mismo template
        context['form'] = RepuestoForm()
        
        # Valores actuales de filtros (para template)
        context['busqueda'] = self.request.GET.get('busqueda', '')
        context['categoria_filtro'] = self.request.GET.get('categoria_filtro', '')
        context['compatibilidad_filtro'] = self.request.GET.get('compatibilidad_filtro', '')
        context['orden'] = self.request.GET.get('orden', '')
        
        # Categorías para select en formulario
        context['categorias'] = self.categoria_repo.obtener_todos()
        
        return context


class RepuestoCreateView(LoginRequiredMixin, SuccessMessageMixin, RepositorioMixin, CreateView):
    """
    Crear nuevo repuesto.
    
    Form: RepuestoForm (maneja categoria_nueva inline)
    Template: repuestos/listar.html (mismo que listado)
    Success: Redirect a listado con mensaje
    """
    model = Repuesto
    form_class = RepuestoForm
    template_name = 'repuestos/listar.html'
    success_url = reverse_lazy('repuesto_listar')
    success_message = 'Repuesto "%(nombre)s" creado correctamente'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'repuestos'
        context['es_crear'] = True
        # Pasar listado filtrado para template compartido
        context['repuestos'] = self.get_queryset()[:20]
        context['filtro_form'] = RepuestoFiltroForm()
        context['choices'] = Repuesto.COMPATIBILIDAD_CHOICES
        context['categorias'] = self.categoria_repo.obtener_todos()
        return context
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario')
        return super().form_invalid(form)


class RepuestoUpdateView(LoginRequiredMixin, SuccessMessageMixin, RepositorioMixin, UpdateView):
    """
    Editar repuesto existente.
    
    Form: RepuestoForm (pre-poblado, maneja categoria_nueva)
    Template: repuestos/listar.html
    Success: Redirect a listado con mensaje (preservando filtros)
    """
    model = Repuesto
    form_class = RepuestoForm
    template_name = 'repuestos/listar.html'
    success_message = 'Repuesto "%(nombre)s" actualizado correctamente'
    login_url = 'login'
    
    def get_success_url(self):
        """Preserva filtros actuales en redirect."""
        # Construir URL con parámetros GET actuales
        from urllib.parse import urlencode
        params = self.request.GET.copy()
        # Remover página para volver a primera
        params.pop('page', None)
        base_url = reverse_lazy('repuesto_listar')
        if params:
            return f'{base_url}?{urlencode(params)}'
        return base_url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seccion'] = 'repuestos'
        context['es_editar'] = True
        context['repuesto'] = self.object
        context['repuestos'] = self.get_queryset()[:20]
        context['filtro_form'] = RepuestoFiltroForm(self.request.GET)
        context['choices'] = Repuesto.COMPATIBILIDAD_CHOICES
        context['categorias'] = self.categoria_repo.obtener_todos()
        # Valores de filtros actuales
        context['busqueda'] = self.request.GET.get('busqueda', '')
        context['categoria_filtro'] = self.request.GET.get('categoria_filtro', '')
        context['compatibilidad_filtro'] = self.request.GET.get('compatibilidad_filtro', '')
        context['orden'] = self.request.GET.get('orden', '')
        return context


class RepuestoDeleteView(LoginRequiredMixin, SuccessMessageMixin, RepositorioMixin, DeleteView):
    """
    Eliminar repuesto (con confirmación).
    
    Template: repuestos/repuestos_confirm_delete.html
    Success: Redirect a listado preservando filtros
    """
    model = Repuesto
    template_name = 'repuestos/repuestos_confirm_delete.html'
    success_message = 'Repuesto "%(nombre)s" eliminado correctamente'
    login_url = 'login'
    
    def get_success_url(self):
        """Preserva filtros actuales en redirect."""
        from urllib.parse import urlencode
        params = self.request.GET.copy()
        params.pop('page', None)
        base_url = reverse_lazy('repuesto_listar')
        if params:
            return f'{base_url}?{urlencode(params)}'
        return base_url
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre = self.object.nombre
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Repuesto "{nombre}" eliminado correctamente')
        return response


# ==========================================
# Vistas Auxiliares
# ==========================================

class RepuestoDetailView(LoginRequiredMixin, DetailView):
    """
    Vista detalle de repuesto (para modal/ajax futuro).
    """
    model = Repuesto
    template_name = 'repuestos/partials/repuesto_detail.html'
    context_object_name = 'repuesto'
    login_url = 'login'