"""
Formularios Django (ModelForms) para validación server-side.

Los ModelForms proporcionan:
- Validación automática basada en campos del modelo
- Limpieza y normalización de datos (clean_*)
- Integración con templates (renderizado de errores)
- Protección CSRF automática
- Manejo de campos unique, constraints, etc.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Cliente, Repuesto, Categoria


class ClienteForm(forms.ModelForm):
    """
    Formulario para crear/editar Cliente.
    
    Validaciones incluidas:
    - nombre: solo letras y espacios, 2-100 chars
    - email: formato válido + único en BD
    - telefono: opcional, solo dígitos/espacios, máx 20 chars
    - direccion: opcional, min 5 chars si se proporciona
    """
    
    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
                'pattern': '[A-Za-zÁ-ú\\s]+',
                'title': 'Solo se permiten letras y espacios',
                'autocomplete': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'juan@ejemplo.com',
                'autocomplete': 'email',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '3001234567',
                'inputmode': 'tel',
                'pattern': '[0-9\\s]+',
                'title': 'Solo se permiten números y espacios',
                'maxlength': '20',
                'autocomplete': 'tel',
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Calle 123 # 45-67',
                'minlength': '5',
            }),
        }
        labels = {
            'nombre': 'Nombre Completo',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección de residencia',
        }
        help_texts = {
            'email': 'Debe ser único en el sistema',
            'telefono': 'Opcional. Máximo 20 dígitos',
            'direccion': 'Opcional. Mínimo 5 caracteres',
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio',
                'max_length': 'Máximo 100 caracteres',
            },
            'email': {
                'required': 'El email es obligatorio',
                'unique': 'Ya existe un cliente con este email',
                'invalid': 'Formato de email inválido',
            },
        }

    def clean_nombre(self):
        """
        Validación personalizada para nombre.
        - Solo letras, espacios y acentos
        - Mínimo 2 caracteres
        - Normaliza: strip, capitaliza cada palabra
        """
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError(_('El nombre es obligatorio'))
        
        if len(nombre) < 2:
            raise ValidationError(_('El nombre debe tener al menos 2 caracteres'))
        
        # Validar caracteres permitidos
        import re
        if not re.match(r'^[A-Za-zÁ-ú\s]+$', nombre):
            raise ValidationError(_('Solo se permiten letras y espacios'))
        
        # Normalizar: capitalizar cada palabra
        return ' '.join(word.capitalize() for word in nombre.split())

    def clean_email(self):
        """
        Validación personalizada para email.
        - Formato válido (EmailField ya valida)
        - Unicidad case-insensitive
        - Normaliza a lowercase
        """
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError(_('El email es obligatorio'))
        
        # Verificar unicidad (excluyendo instancia actual en edición)
        queryset = Cliente.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError(_('Ya existe un cliente registrado con este email'))
        
        return email

    def clean_telefono(self):
        """
        Validación personalizada para teléfono.
        - Opcional
        - Solo dígitos, espacios, guiones, paréntesis, +
        - Máximo 20 caracteres
        - Normaliza: solo dígitos
        """
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        if not telefono:
            return ''  # Opcional
        
        import re
        # Permitir formato: +57 300 123 4567, 3001234567, (300) 123-4567, etc.
        if not re.match(r'^[\d\s\-\+\(\)]+$', telefono):
            raise ValidationError(_('Formato de teléfono inválido'))
        
        if len(telefono) > 20:
            raise ValidationError(_('Máximo 20 caracteres'))
        
        # Normalizar: solo dígitos para almacenamiento
        digitos = re.sub(r'\D', '', telefono)
        return digitos

    def clean_direccion(self):
        """
        Validación personalizada para dirección.
        - Opcional
        - Mínimo 5 caracteres si se proporciona
        - Sanitiza caracteres peligrosos
        """
        direccion = self.cleaned_data.get('direccion', '').strip()
        
        if not direccion:
            return ''
        
        if len(direccion) < 5:
            raise ValidationError(_('La dirección debe tener al menos 5 caracteres'))
        
        # Sanitizar: permitir alfanumérico, espacios, #, ., ,, -, /, acentos
        import re
        direccion_limpia = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s#.,\-/]', '', direccion)
        
        return direccion_limpia


class RepuestoForm(forms.ModelForm):
    """
    Formulario para crear/editar Repuesto.
    
    Validaciones incluidas:
    - nombre: requerido, 2-100 chars
    - categoria: FK a Categoria (select) o nueva categoría
    - precio: decimal >= 0, máx 10 dígitos, 2 decimales
    - stock: entero >= 0
    - compatibilidad: choice obligatorio (S, T, U)
    - descripcion: opcional, texto libre
    """
    
    # Campo para permitir crear nueva categoría inline
    categoria_nueva = forms.CharField(
        required=False,
        max_length=50,
        label='Nueva Categoría',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'O escriba una nueva categoría...',
        }),
        help_text='Deje vacío para seleccionar una existente'
    )
    
    class Meta:
        model = Repuesto
        fields = ['nombre', 'categoria', 'precio', 'stock', 'compatibilidad', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Tensor Shimano Deore',
                'autocomplete': 'off',
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select',
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'value': '0',
            }),
            'compatibilidad': forms.Select(attrs={
                'class': 'form-select',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalles de compatibilidad adicional u observaciones...',
            }),
        }
        labels = {
            'nombre': 'Nombre del Repuesto',
            'categoria': 'Categoría',
            'precio': 'Precio ($)',
            'stock': 'Stock (unidades)',
            'compatibilidad': 'Compatibilidad',
            'descripcion': 'Descripción Técnica',
        }
        help_texts = {
            'precio': 'Precio de venta. Mínimo 0.',
            'stock': 'Unidades disponibles. Mínimo 0.',
            'compatibilidad': 'S=Ruta, T=Todo Terreno, U=Universal',
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio',
                'max_length': 'Máximo 100 caracteres',
            },
            'precio': {
                'required': 'El precio es obligatorio',
                'min_value': 'El precio no puede ser negativo',
                'max_digits': 'Máximo 10 dígitos (incluyendo decimales)',
                'max_decimal_places': 'Máximo 2 decimales',
            },
            'stock': {
                'required': 'El stock es obligatorio',
                'min_value': 'El stock no puede ser negativo',
            },
            'compatibilidad': {
                'required': 'Debe seleccionar una compatibilidad',
            },
        }

    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y configura el queryset de categorías."""
        super().__init__(*args, **kwargs)
        
        # Ordenar categorías alfabéticamente
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nombre')
        self.fields['categoria'].empty_label = 'Seleccione una categoría...'
        self.fields['categoria'].required = False  # Puede usar categoria_nueva
        
        # Configurar choices de compatibilidad desde el modelo
        self.fields['compatibilidad'].choices = Repuesto.COMPATIBILIDAD_CHOICES

    def clean_nombre(self):
        """Valida y normaliza el nombre del repuesto."""
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError(_('El nombre es obligatorio'))
        
        if len(nombre) < 2:
            raise ValidationError(_('El nombre debe tener al menos 2 caracteres'))
        
        if len(nombre) > 100:
            raise ValidationError(_('Máximo 100 caracteres'))
        
        # Capitalizar primera letra de cada palabra
        return ' '.join(word.capitalize() for word in nombre.split())

    def clean_precio(self):
        """Valida que el precio sea >= 0."""
        precio = self.cleaned_data.get('precio')
        
        if precio is None:
            raise ValidationError(_('El precio es obligatorio'))
        
        if precio < 0:
            raise ValidationError(_('El precio no puede ser negativo'))
        
        # Redondear a 2 decimales
        from decimal import Decimal, ROUND_HALF_UP
        return Decimal(str(precio)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def clean_stock(self):
        """Valida que el stock sea >= 0."""
        stock = self.cleaned_data.get('stock')
        
        if stock is None:
            raise ValidationError(_('El stock es obligatorio'))
        
        if stock < 0:
            raise ValidationError(_('El stock no puede ser negativo'))
        
        return stock

    def clean(self):
        """
        Validación a nivel de formulario (cross-field).
        - Debe tener categoría (existente o nueva)
        """
        cleaned_data = super().clean()
        categoria = cleaned_data.get('categoria')
        categoria_nueva = cleaned_data.get('categoria_nueva', '').strip()
        
        if not categoria and not categoria_nueva:
            raise ValidationError({
                'categoria': _('Debe seleccionar una categoría existente o ingresar una nueva'),
                'categoria_nueva': _('Debe seleccionar una categoría existente o ingresar una nueva'),
            })
        
        return cleaned_data

    def save(self, commit=True):
        """
        Guarda el repuesto manejando la creación de nueva categoría si aplica.
        """
        instance = super().save(commit=False)
        
        # Manejar nueva categoría
        categoria_nueva = self.cleaned_data.get('categoria_nueva', '').strip()
        if categoria_nueva and not self.cleaned_data.get('categoria'):
            # Buscar o crear categoría (case-insensitive)
            categoria, created = Categoria.objects.get_or_create(
                nombre__iexact=categoria_nueva,
                defaults={'nombre': categoria_nueva.capitalize()}
            )
            instance.categoria = categoria
        
        if commit:
            instance.save()
        
        return instance


class RepuestoFiltroForm(forms.Form):
    """
    Formulario para filtros y ordenamiento del listado de repuestos.
    Se usa en GET requests, no es ModelForm.
    """
    
    busqueda = forms.CharField(
        required=False,
        max_length=100,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Nombre o descripción...',
        })
    )
    
    categoria_filtro = forms.CharField(
        required=False,
        max_length=50,
        label='Categoría',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Ej. Frenos',
        })
    )
    
    compatibilidad_filtro = forms.ChoiceField(
        required=False,
        label='Compatibilidad',
        choices=[('', 'Todas')] + Repuesto.COMPATIBILIDAD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
        })
    )
    
    orden = forms.ChoiceField(
        required=False,
        label='Ordenar por',
        choices=[
            ('', 'Sin ordenar'),
            ('nombre_asc', 'Nombre (A-Z)'),
            ('nombre_desc', 'Nombre (Z-A)'),
            ('precio_asc', 'Precio (menor a mayor)'),
            ('precio_desc', 'Precio (mayor a menor)'),
            ('stock_asc', 'Stock (menor a mayor)'),
            ('stock_desc', 'Stock (mayor a menor)'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
        })
    )

    def get_orden_field(self):
        """Convierte la opción de orden a campo de ordenamiento Django."""
        orden_map = {
            'nombre_asc': 'nombre',
            'nombre_desc': '-nombre',
            'precio_asc': 'precio',
            'precio_desc': '-precio',
            'stock_asc': 'stock',
            'stock_desc': '-stock',
        }
        return orden_map.get(self.cleaned_data.get('orden', ''), '')