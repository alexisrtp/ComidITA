import uuid
from django.db import models
from django.contrib.auth.models import User


# 1. Catálogo de Categorías
class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

# 2. Perfil del Negocio
class Negocio(models.Model):
    propietario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(help_text="Descripción general del negocio o su menú")
    abierto = models.BooleanField(default=True, help_text="Interruptor manual (apágalo si estás en clase)")

    # --- CAMPOS NUEVOS (Logos y Horarios) ---
    logo = models.ImageField(upload_to='negocios/logos/', null=True, blank=True)
    portada = models.ImageField(upload_to='negocios/portadas/', null=True, blank=True)
    hora_apertura = models.TimeField(null=True, blank=True, help_text="Ej: 08:00")
    hora_cierre = models.TimeField(null=True, blank=True, help_text="Ej: 16:00")

    # ----------------------------------------

    def __str__(self):
        return self.nombre

    @property
    def esta_abierto_ahora(self):
        from django.utils import timezone

        # 1. Si apagaste el switch manual del panel, se queda cerrado sin importar la hora.
        if not self.abierto:
            return False

        # 2. Si aún no has configurado horarios, dependemos solo de tu switch manual.
        if not self.hora_apertura or not self.hora_cierre:
            return self.abierto

        # 3. Si hay horarios definidos, comparamos con la hora actual de México.
        hora_actual = timezone.localtime(timezone.now()).time()
        return self.hora_apertura <= hora_actual <= self.hora_cierre


# 3. Catálogo de Productos
class Producto(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='productos')

    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200,
                                   help_text="Breve descripción del producto (ej. 'Con queso extra y aderezo')")
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)

    # --- AQUÍ ESTÁN LOS CAMPOS NUEVOS ---
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    unidades_disponibles = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Deja en blanco si es ilimitado, o pon el número de unidades"
    )
    # ------------------------------------

    OPCIONES_CATEGORIA = [
        ('Tacos & Antojitos', 'Tacos & Antojitos'),
        ('Comida Rápida', 'Comida Rápida'),
        ('Postres dulces', 'Postres dulces'),
        ('Bebidas frías', 'Bebidas frías'),
        ('Bebidas Calientes', 'Bebidas Calientes'),
        ('Saludable', 'Saludable'),
        ('Otro', 'Otro'),
    ]

    categoria = models.CharField(
        max_length=50,
        choices=OPCIONES_CATEGORIA,
        default='Otro',
        verbose_name='Categoría del Platillo'
    )

    def __str__(self):
        return f"{self.nombre} - {self.negocio.nombre}"

# 4. El Ticket Digital (Cabecera del Pedido)
class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de entrega'),
        ('COMPLETADO', 'Entregado y confirmado'),
        ('CANCELADO', 'Cancelado'),
    ]

    PUNTOS_ENTREGA = [
        ('SISTEMAS', 'Edificio de Sistemas'),
        ('ISOPTICA', 'Sala Isóptica'),
        ('CAFETERIA', 'Cafetería Principal'),
        ('BIBLIOTECA', 'Biblioteca'),
        ('PLAZA', 'Plaza Cívica'),
    ]

    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos_realizados')
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='pedidos_recibidos')

    # Datos operativos de la entrega
    folio = models.CharField(max_length=8, unique=True, editable=False)
    punto_encuentro = models.CharField(max_length=50, choices=PUNTOS_ENTREGA, default='CAFETERIA', help_text="Punto seleccionado en el mapa")
    horario_entrega = models.TimeField(help_text="Hora exacta acordada para la entrega")

    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.folio:
            self.folio = str(uuid.uuid4()).upper()[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Folio: {self.folio} - {self.estado}"


# 5. Las Partidas del Ticket (Detalle)
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2,
                                          help_text="Congela el precio al momento de la venta")

    def subtotal(self):
        return self.cantidad * self.precio_unitario

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"