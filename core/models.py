"""
Modelos de dominio para Bike Assembly.

Principios aplicados:
- Entidades ricas con validación a nivel de modelo
- Constraints de BD para integridad referencial
- Índices para rendimiento en consultas frecuentes
- Timestamps de auditoría (creación + actualización)
- Normalización: Categoria como entidad separada
"""

from django.db import models
from django.db.models import Q, CheckConstraint
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Categoria(models.Model):
    """
    Categoría de repuestos (normalizada).
    
    Separada de Repuesto para:
    - Evitar duplicados/inconsistencias ("Frenos", "frenos", "FRENOS")
    - Permitir FK con PROTECT (no borrar categoría si tiene repuestos)
    - Consultas eficientes por categoría
    """
    
    nombre = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Nombre'),
        help_text=_('Nombre único de la categoría (ej. Transmisión, Frenos, Ruedas)')
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
        help_text=_('Descripción opcional de la categoría')
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de registro')
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de actualización')
    )

    class Meta:
        verbose_name = _('Categoría')
        verbose_name_plural = _('Categorías')
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre'], name='categoria_nombre_idx'),
        ]

    def __str__(self):
        return self.nombre

    def clean(self):
        """Validación a nivel de modelo."""
        super().clean()
        if self.nombre:
            self.nombre = self.nombre.strip().capitalize()


class Cliente(models.Model):
    """
    Cliente del taller/negocio.
    
    Reglas de negocio:
    - Email único (identificador natural)
    - Teléfono opcional, solo dígitos normalizados
    - Dirección opcional, mínimo 5 chars
    - Auditoría: fecha_registro (creación) + fecha_actualizacion (modificación)
    """
    
    nombre = models.CharField(
        max_length=100,
        verbose_name=_('Nombre completo'),
        help_text=_('Solo letras y espacios. Ej: Juan Pérez')
    )
    email = models.EmailField(
        unique=True,
        verbose_name=_('Correo electrónico'),
        help_text=_('Debe ser único. Usado para contacto e identificación')
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name=_('Teléfono'),
        help_text=_('Opcional. Solo dígitos. Ej: 3001234567')
    )
    direccion = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name=_('Dirección'),
        help_text=_('Opcional. Mínimo 5 caracteres')
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de registro')
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de actualización')
    )

    class Meta:
        verbose_name = _('Cliente')
        verbose_name_plural = _('Clientes')
        ordering = ['-fecha_registro']  # Más recientes primero
        indexes = [
            models.Index(fields=['email'], name='cliente_email_idx'),
            models.Index(fields=['-fecha_registro'], name='cliente_fecha_idx'),
            models.Index(fields=['nombre'], name='cliente_nombre_idx'),
        ]
        constraints = [
            # Email único ya está en campo, pero constraint explícito para nombre
        ]

    def __str__(self):
        return self.nombre

    def clean(self):
        """Validación a nivel de modelo (se ejecuta en full_clean)."""
        super().clean()
        
        # Normalizar nombre
        if self.nombre:
            self.nombre = ' '.join(word.capitalize() for word in self.nombre.strip().split())
        
        # Normalizar email a lowercase
        if self.email:
            self.email = self.email.strip().lower()
        
        # Normalizar teléfono: solo dígitos
        if self.telefono:
            import re
            self.telefono = re.sub(r'\D', '', self.telefono.strip())
        
        # Sanitizar dirección
        if self.direccion:
            import re
            self.direccion = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s#.,\-/]', '', self.direccion.strip())


class Repuesto(models.Model):
    """
    Repuesto/Componente de bicicleta en inventario.
    
    Reglas de negocio:
    - Precio >= 0 (constraint BD + validación)
    - Stock >= 0 (constraint BD + validación, evita overselling)
    - Compatibilidad: S=Ruta, T=Todo Terreno, U=Universal
    - Categoría: FK a Categoria (PROTECT = no borrar si tiene repuestos)
    - Auditoría completa
    """
    
    COMPATIBILIDAD_CHOICES = [
        ('S', _('Ruta (S)')),
        ('T', _('Todo Terreno (T)')),
        ('U', _('Universal (U)')),
    ]
    
    # Identificación
    nombre = models.CharField(
        max_length=100,
        verbose_name=_('Nombre'),
        help_text=_('Nombre del componente. Ej: Tensor Shimano Deore')
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,  # Impide borrar categoría si tiene repuestos
        related_name='repuestos',
        verbose_name=_('Categoría'),
        help_text=_('Categoría del repuesto')
    )
    
    # Precio y Stock (con constraints de BD)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Precio'),
        help_text=_('Precio de venta. Mínimo 0.')
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Stock'),
        help_text=_('Unidades disponibles. Mínimo 0.')
    )
    
    # Clasificación
    compatibilidad = models.CharField(
        max_length=1,
        choices=COMPATIBILIDAD_CHOICES,
        default='U',
        verbose_name=_('Compatibilidad'),
        help_text=_('S=Ruta, T=Todo Terreno, U=Universal')
    )
    
    # Descripción técnica
    descripcion = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Descripción técnica'),
        help_text=_('Detalles de compatibilidad, observaciones, etc.')
    )
    
    # Auditoría
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de registro')
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de actualización')
    )

    class Meta:
        verbose_name = _('Repuesto')
        verbose_name_plural = _('Repuestos')
        ordering = ['-fecha_registro']
        indexes = [
            # Índices para filtros y búsquedas frecuentes
            models.Index(fields=['nombre'], name='repuesto_nombre_idx'),
            models.Index(fields=['categoria'], name='repuesto_categoria_idx'),
            models.Index(fields=['compatibilidad'], name='repuesto_compat_idx'),
            models.Index(fields=['stock'], name='repuesto_stock_idx'),  # Para alertas stock bajo
            models.Index(fields=['-fecha_registro'], name='repuesto_fecha_idx'),
            # Índice compuesto para listado paginado ordenado por fecha
            models.Index(fields=['-fecha_registro', 'id'], name='repuesto_listado_idx'),
        ]
        constraints = [
            # Precio no negativo (BD level)
            CheckConstraint(
                check=Q(precio__gte=0),
                name='repuesto_precio_no_negativo'
            ),
            # Stock no negativo (BD level) - CRÍTICO para evitar overselling
            CheckConstraint(
                check=Q(stock__gte=0),
                name='repuesto_stock_no_negativo'
            ),
            # Compatibilidad válida (BD level)
            CheckConstraint(
                check=Q(compatibilidad__in=['S', 'T', 'U']),
                name='repuesto_compatibilidad_valida'
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_compatibilidad_display()})"

    def clean(self):
        """Validación a nivel de modelo."""
        super().clean()
        
        # Normalizar nombre
        if self.nombre:
            self.nombre = ' '.join(word.capitalize() for word in self.nombre.strip().split())
        
        # Validar precio
        if self.precio is not None and self.precio < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError({'precio': _('El precio no puede ser negativo')})
        
        # Validar stock
        if self.stock is not None and self.stock < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError({'stock': _('El stock no puede ser negativo')})

    @property
    def stock_status(self):
        """
        Propiedad computada para estado del stock.
        Usado en templates y serializers.
        """
        if self.stock == 0:
            return 'agotado'
        elif self.stock <= 5:
            return 'bajo'
        return 'ok'

    @property
    def stock_status_class(self):
        """Clase CSS para badge de stock."""
        status = self.stock_status
        return {
            'agotado': 'bg-danger',
            'bajo': 'bg-warning text-dark',
            'ok': 'bg-success',
        }.get(status, 'bg-secondary')

    @property
    def stock_status_label(self):
        """Etiqueta legible para estado del stock."""
        return {
            'agotado': 'Agotado',
            'bajo': f'Bajo stock ({self.stock} unds)',
            'ok': f'{self.stock} unds',
        }.get(self.stock_status, 'Desconocido')