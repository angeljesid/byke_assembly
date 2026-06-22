from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Cliente
from .repositories import RepuestoRepository
from .models import Repuesto

# Listar
def listar_repuestos(request):
    repuestos = RepuestoRepository.obtener_todos()
    return render(request, 'repuestos/listar.html', {'repuestos': repuestos})

# Crear
def crear_repuesto(request):
    if request.method == 'POST':
        datos = {
            'nombre': request.POST.get('nombre'),
            'categoria': request.POST.get('categoria'),
            'precio': request.POST.get('precio'),
            'stock': request.POST.get('stock'),
            'compatibilidad': request.POST.get('compatibilidad'),
            'descripcion': request.POST.get('descripcion'),
        }
        RepuestoRepository.crear(datos)
        return redirect('listar_repuestos')
    
    return render(request, 'repuestos/formulario.html', {'choices': Repuesto.COMPATIBILIDAD_CHOICES})

# Editar
def editar_repuesto(request, pk):
    repuesto = get_object_or_404(Repuesto, id=pk)
    if request.method == 'POST':
        datos = {
            'nombre': request.POST.get('nombre'),
            'categoria': request.POST.get('categoria'),
            'precio': request.POST.get('precio'),
            'stock': request.POST.get('stock'),
            'compatibilidad': request.POST.get('compatibilidad'),
            'descripcion': request.POST.get('descripcion'),
        }
        RepuestoRepository.actualizar(pk, datos)
        return redirect('listar_repuestos')
    
    return render(request, 'repuestos/formulario.html', {
        'repuesto': repuesto, 
        'choices': Repuesto.COMPATIBILIDAD_CHOICES
    })

# Eliminar
def eliminar_repuesto(request, pk):
    if request.method == 'POST':
        RepuestoRepository.eliminar(pk)
    return redirect('listar_repuestos')



def home(request):
    return render(request, 'inicio.html')

#login
@login_required
def dashboard(request):
    return render(request, 'repuestos/inicio.html', {'seccion': 'home'})

@login_required
def listar_clientes(self, request):
    clientes = Cliente.objects.all()
    if request.method == 'POST':
        # Lógica rápida para agregar un cliente desde la misma pantalla o un modal
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        
        if nombre and email:
            Cliente.objects.create(nombre=nombre, email=email, telefono=telefono, direccion=direccion)
            return redirect('listar_clientes')
            
    return render(request, 'repuestos/clientes.html', {
        'clientes': clientes,
        'seccion': 'clientes'
    })

