from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Cliente, Repuesto
from .repositories import RepuestoRepository


def quienes_somos(request):
    return render(request, 'repuestos/quienes_somos.html')


def home(request):
    return render(request, 'inicio.html')


@login_required
def dashboard(request):
    return render(request, 'repuestos/inicio.html', {'seccion': 'home'})


@login_required
def listar_clientes(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        if nombre and email:
            Cliente.objects.create(
                nombre=nombre,
                email=email,
                telefono=request.POST.get('telefono'),
                direccion=request.POST.get('direccion')
            )
            return redirect('listar_clientes')

    return render(request, 'repuestos/clientes.html', {
        'clientes': Cliente.objects.all(),
        'seccion': 'clientes'
    })


@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, id=pk)
    if request.method == 'POST':
        cliente.nombre = request.POST.get('nombre')
        cliente.email = request.POST.get('email')
        cliente.telefono = request.POST.get('telefono')
        cliente.direccion = request.POST.get('direccion')
        cliente.save()
        return redirect('listar_clientes')

    return render(request, 'repuestos/clientes.html', {
        'clientes': Cliente.objects.all(),
        'cliente_editar': cliente,
        'seccion': 'clientes'
    })


@login_required
def eliminar_cliente(request, pk):
    if request.method == 'POST':
        get_object_or_404(Cliente, id=pk).delete()
    return redirect('listar_clientes')


def _filtrar_y_ordenar_repuestos(request, repuestos):
    """
    Aplica búsqueda, filtrado por categoría/compatibilidad
    y ordenamiento sobre el queryset de repuestos.
    """
    busqueda = request.GET.get('busqueda', '').strip()
    categoria_filtro = request.GET.get('categoria_filtro', '').strip()
    compatibilidad_filtro = request.GET.get('compatibilidad_filtro', '').strip()
    orden = request.GET.get('orden', '').strip()

    if busqueda:
        repuestos = repuestos.filter(
            Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    if categoria_filtro:
        repuestos = repuestos.filter(categoria__icontains=categoria_filtro)

    if compatibilidad_filtro:
        repuestos = repuestos.filter(compatibilidad=compatibilidad_filtro)

    ordenes_validos = {
        'nombre_asc': 'nombre',
        'nombre_desc': '-nombre',
        'precio_asc': 'precio',
        'precio_desc': '-precio',
        'stock_asc': 'stock',
        'stock_desc': '-stock',
    }
    if orden in ordenes_validos:
        repuestos = repuestos.order_by(ordenes_validos[orden])

    contexto_filtros = {
        'busqueda': busqueda,
        'categoria_filtro': categoria_filtro,
        'compatibilidad_filtro': compatibilidad_filtro,
        'orden': orden,
    }
    return repuestos, contexto_filtros


@login_required
def listar_repuestos(request):
    if request.method == 'POST':
        datos = {k: request.POST.get(k) for k in ['nombre', 'categoria', 'precio', 'stock', 'compatibilidad', 'descripcion']}
        RepuestoRepository.crear(datos)
        return redirect('listar_repuestos')

    repuestos = RepuestoRepository.obtener_todos()
    repuestos, contexto_filtros = _filtrar_y_ordenar_repuestos(request, repuestos)

    contexto = {
        'repuestos': repuestos,
        'choices': Repuesto.COMPATIBILIDAD_CHOICES,
        'seccion': 'repuestos',
    }
    contexto.update(contexto_filtros)
    return render(request, 'repuestos/listar.html', contexto)


@login_required
def editar_repuesto(request, pk):
    repuesto = get_object_or_404(Repuesto, id=pk)
    if request.method == 'POST':
        datos = {k: request.POST.get(k) for k in ['nombre', 'categoria', 'precio', 'stock', 'compatibilidad', 'descripcion']}
        RepuestoRepository.actualizar(pk, datos)
        return redirect('listar_repuestos')

    repuestos = RepuestoRepository.obtener_todos()
    repuestos, contexto_filtros = _filtrar_y_ordenar_repuestos(request, repuestos)

    contexto = {
        'repuesto': repuesto,
        'repuestos': repuestos,
        'choices': Repuesto.COMPATIBILIDAD_CHOICES,
        'seccion': 'repuestos',
    }
    contexto.update(contexto_filtros)
    return render(request, 'repuestos/listar.html', contexto)


@login_required
def eliminar_repuesto(request, pk):
    if request.method == 'POST':
        RepuestoRepository.eliminar(pk)
    return redirect('listar_repuestos')