from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_vista, name='login'),
    path('inicio/', views.inicio_cliente_view, name='inicio_cliente'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('panel-emprendedor/', views.panel_emprendedor, name='panel_emprendedor'),
    path('panel-emprendedor/agregar/', views.agregar_producto, name='agregar_producto'),

]