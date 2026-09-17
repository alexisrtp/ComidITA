from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Categoria, Negocio, Producto, Pedido, DetallePedido

# Esto hará que las tablas sean visibles y editables en /admin/
admin.site.register(Categoria)
admin.site.register(Negocio)
admin.site.register(Producto)
admin.site.register(Pedido)
admin.site.register(DetallePedido)