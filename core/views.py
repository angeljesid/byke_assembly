from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
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

@login_required
def listar_repuestos(request):
    if request.method == 'POST':
        datos = {k: request.POST.get(k) for k in ['nombre', 'categoria', 'precio', 'stock', 'compatibilidad', 'descripcion']}
        RepuestoRepository.crear(datos)
        return redirect('listar_repuestos')

    return render(request, 'repuestos/listar.html', {
        'repuestos': RepuestoRepository.obtener_todos(),
        'choices': Repuesto.COMPATIBILIDAD_CHOICES,
        'seccion': 'repuestos'
    })

@login_required
def editar_repuesto(request, pk):
    repuesto = get_object_or_404(Repuesto, id=pk)
    if request.method == 'POST':
        datos = {k: request.POST.get(k) for k in ['nombre', 'categoria', 'precio', 'stock', 'compatibilidad', 'descripcion']}
        RepuestoRepository.actualizar(pk, datos)
        return redirect('listar_repuestos')
    
    return render(request, 'repuestos/listar.html', {
        'repuesto': repuesto,
        'repuestos': RepuestoRepository.obtener_todos(),
        'choices': Repuesto.COMPATIBILIDAD_CHOICES,
        'seccion': 'repuestos'
    })

@login_required
def eliminar_repuesto(request, pk):
    if request.method == 'POST':
        RepuestoRepository.eliminar(pk)
    return redirect('listar_repuestos')