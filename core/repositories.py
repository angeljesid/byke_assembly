"""
Capa de Acceso a Datos (Repository Pattern).

Principios:
- Encapsula lógica de queries Django ORM
- Usa save() en lugar de update() para disparar signals y validaciones
- Métodos de instancia (no static) para permitir inyección de dependencias
- Retorna None en lugar de lanzar excepciones (excepto get_por_id)
- Type hints para mejor IDE support y documentación
"""

from typing import Optional, List, Dict, Any
from django.db import models
from django.db.models import QuerySet, Q

from .models import Cliente, Repuesto, Categoria


class BaseRepository:
    """
    Repositorio base con operaciones CRUD comunes.
    
    Ventajas de no usar staticmethods:
    - Permite mocking en tests
    - Permite inyección de dependencias
    - Permite herencia y override
    """
    
    def __init__(self, model_class: type[models.Model]):
        self.model_class = model_class
    
    def obtener_todos(self) -> QuerySet:
        """Retorna QuerySet base (lazy) para encadenar filtros."""
        return self.model_class.objects.all()
    
    def obtener_por_id(self, pk: int) -> Optional[models.Model]:
        """
        Obtiene una instancia por PK.
        Retorna None si no existe (no lanza excepción).
        """
        try:
            return self.model_class.objects.get(pk=pk)
        except self.model_class.DoesNotExist:
            return None
    
    def crear(self, **datos) -> models.Model:
        """
        Crea nueva instancia usando save() para:
        - Disparar pre_save/post_save signals
        - Ejecutar validaciones del modelo (full_clean)
        - Mantener consistencia con override de save()
        """
        instancia = self.model_class(**datos)
        instancia.full_clean()  # Valida constraints, clean(), etc.
        instancia.save()
        return instancia
    
    def actualizar(self, pk: int, **datos) -> Optional[models.Model]:
        """
        Actualiza instancia existente usando save().
        
        Por qué save() y NO update():
        - update() salta signals (pre_save, post_save)
        - update() salta validaciones del modelo
        - update() no actualiza fecha_actualizacion (auto_now)
        - save() respeta override de save() en modelo
        """
        instancia = self.obtener_por_id(pk)
        if instancia is None:
            return None
        
        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(instancia, campo):
                setattr(instancia, campo, valor)
        
        # Validar y guardar
        instancia.full_clean()
        instancia.save()
        return instancia
    
    def eliminar(self, pk: int) -> bool:
        """
        Elimina instancia (hard delete).
        Retorna True si se eliminó, False si no existía.
        """
        instancia = self.obtener_por_id(pk)
        if instancia is None:
            return False
        instancia.delete()
        return True


class ClienteRepository(BaseRepository):
    """Repositorio específico para Cliente con queries optimizadas."""
    
    def __init__(self):
        super().__init__(Cliente)
    
    def obtener_todos(self) -> QuerySet:
        """QuerySet optimizado para listados."""
        return super().obtener_todos().order_by('-fecha_registro')
    
    def buscar(self, termino: str) -> QuerySet:
        """
        Búsqueda por nombre o email (case-insensitive, partial).
        """
        if not termino:
            return self.obtener_todos()
        return self.obtener_todos().filter(
            Q(nombre__icontains=termino) | Q(email__icontains=termino)
        )
    
    def existe_email(self, email: str, excluir_pk: Optional[int] = None) -> bool:
        """Verifica si email ya existe (case-insensitive)."""
        qs = Cliente.objects.filter(email__iexact=email)
        if excluir_pk:
            qs = qs.exclude(pk=excluir_pk)
        return qs.exists()


class RepuestoRepository(BaseRepository):
    """Repositorio específico para Repuesto con queries optimizadas."""
    
    def __init__(self):
        super().__init__(Repuesto)
    
    def obtener_todos(self) -> QuerySet:
        """
        QuerySet base optimizado para listados.
        - select_related('categoria') evita N+1 al acceder categoria.nombre
        - Ordenado por fecha descendente (más recientes primero)
        """
        return super().obtener_todos().select_related('categoria').order_by('-fecha_registro')
    
    def filtrar_y_ordenar(
        self,
        busqueda: str = '',
        categoria_filtro: str = '',
        compatibilidad_filtro: str = '',
        orden: str = ''
    ) -> QuerySet:
        """
        Aplica filtros y ordenamiento sobre el QuerySet base.
        Retorna QuerySet lazy (no ejecuta query hasta iterar).
        """
        qs = self.obtener_todos()
        
        # Búsqueda full-text en nombre y descripción
        if busqueda:
            qs = qs.filter(
                Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
            )
        
        # Filtro por categoría (partial match case-insensitive)
        if categoria_filtro:
            qs = qs.filter(categoria__nombre__icontains=categoria_filtro)
        
        # Filtro por compatibilidad (exact match)
        if compatibilidad_filtro in dict(Repuesto.COMPATIBILIDAD_CHOICES):
            qs = qs.filter(compatibilidad=compatibilidad_filtro)
        
        # Ordenamiento
        ordenes_validos = {
            'nombre_asc': 'nombre',
            'nombre_desc': '-nombre',
            'precio_asc': 'precio',
            'precio_desc': '-precio',
            'stock_asc': 'stock',
            'stock_desc': '-stock',
            'fecha_asc': 'fecha_registro',
            'fecha_desc': '-fecha_registro',
        }
        if orden in ordenes_validos:
            qs = qs.order_by(ordenes_validos[orden])
        
        return qs
    
    def stock_bajo(self, umbral: int = 5) -> QuerySet:
        """Repuestos con stock <= umbral."""
        return self.obtener_todos().filter(stock__lte=umbral)
    
    def agotados(self) -> QuerySet:
        """Repuestos con stock = 0."""
        return self.obtener_todos().filter(stock=0)
    
    def por_categoria(self, categoria_id: int) -> QuerySet:
        """Repuestos de una categoría específica."""
        return self.obtener_todos().filter(categoria_id=categoria_id)


class CategoriaRepository(BaseRepository):
    """Repositorio para Categoría."""
    
    def __init__(self):
        super().__init__(Categoria)
    
    def obtener_todos(self) -> QuerySet:
        return super().obtener_todos().order_by('nombre')
    
    def buscar_o_crear(self, nombre: str) -> tuple[Categoria, bool]:
        """
        Busca categoría case-insensitive o la crea.
        Retorna (categoria, created).
        """
        nombre_limpio = nombre.strip().capitalize()
        return Categoria.objects.get_or_create(
            nombre__iexact=nombre_limpio,
            defaults={'nombre': nombre_limpio}
        )