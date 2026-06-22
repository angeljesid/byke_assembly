from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Repuesto(models.Model):
    COMPATIBILIDAD_CHOICES = [
        ('S', 'Ruta (S)'),
        ('T', 'Todo Terreno (T)'),
        ('U', 'Universal (U)'),
    ]

    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)  # Marco, Tensor, Llantas, etc.
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    compatibilidad = models.CharField(
        max_length=1, 
        choices=COMPATIBILIDAD_CHOICES, 
        default='U'
    )
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_compatibilidad_display()})"