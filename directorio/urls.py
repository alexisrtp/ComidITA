from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('login/', views.login_vista, name='login'),
    path('inicio/', views.inicio_cliente_view, name='inicio_cliente'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('panel-emprendedor/', views.panel_emprendedor, name='panel_emprendedor'),
    path('panel-emprendedor/agregar/', views.agregar_producto, name='agregar_producto'),
    path('panel-emprendedor/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('toggle-estado/', views.toggle_estado_negocio, name='toggle_estado'),
    path('negocio/<int:id>/', views.detalle_negocio, name='detalle_negocio'),
    path('panel-emprendedor/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('panel-emprendedor/editar-perfil/', views.editar_perfil_negocio, name='editar_perfil_negocio'),
    path('mis_pedidos/', views.mis_pedidos_view, name='mis_pedidos'),
    path('negocio/<int:id>/pedir/', views.crear_pedido, name='crear_pedido'),
    path('panel-emprendedor/pedidos/', views.panel_pedidos_emprendedor, name='panel_pedidos_emprendedor'),
    path('pedido/<int:pedido_id>/actualizar/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
]