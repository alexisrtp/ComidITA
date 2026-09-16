from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Negocio
from django.contrib.auth.models import User


def login_vista(request):
    if request.method == 'POST':
        correo = request.POST.get('username')
        contra = request.POST.get('password')
        usuario = authenticate(request, username=correo, password=contra)

        if usuario is not None:
            login(request, usuario)

            # MAGIA DE DJANGO: Verificamos qué tipo de usuario es
            if hasattr(usuario, 'negocio'):
                # Si tiene un negocio asociado, es Emprendedor.
                # (Por ahora lo mandamos al panel de admin, luego crearemos su propio dashboard)
                return redirect('/admin/')
            else:
                # Si NO tiene negocio, es un Cliente (Estudiante). Lo mandamos al inicio.
                return redirect('inicio_cliente')
        else:
            messages.error(request, 'Correo o contraseña incorrectos. Intenta de nuevo.')

    return render(request, 'login.html')


# --- VISTA PARA CERRAR SESIÓN ---
def logout_view(request):
    logout(request) # Django borra la sesión de forma segura
    return redirect('login') # Lo regresamos a la pantalla de inicio de sesión

# --- NUEVA VISTA PARA EL CLIENTE ---
def inicio_cliente_view(request):
    # Extraemos todos los negocios registrados en MySQL para mostrarlos en la pantalla
    negocios = Negocio.objects.all()

    # Enviamos los datos al HTML
    return render(request, 'inicio_cliente.html', {'negocios': negocios})


def registro_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        contra1 = request.POST.get('contra1')
        contra2 = request.POST.get('contra2')
        tipo_cuenta = request.POST.get('tipo_cuenta')  # 'cliente' o 'emprendedor'
        nombre_negocio = request.POST.get('nombre_negocio')

        # 1. Validar que las contraseñas coincidan
        if contra1 != contra2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'registro.html')

        # 2. Validar que el correo no exista ya en la base de datos
        if User.objects.filter(username=correo).exists():
            messages.error(request, 'Este correo ya está registrado.')
            return render(request, 'registro.html')

        # 3. Crear el usuario base (sirve para ambos tipos)
        nuevo_usuario = User.objects.create_user(username=correo, email=correo, password=contra1, first_name=nombre)

        # 4. Si eligió ser Emprendedor, le creamos su perfil de Negocio vinculado
        if tipo_cuenta == 'emprendedor':
            # Si se le olvidó poner nombre, le ponemos uno por defecto
            if not nombre_negocio:
                nombre_negocio = f"Negocio de {nombre}"
            Negocio.objects.create(propietario=nuevo_usuario, nombre=nombre_negocio,
                                   descripcion="¡Nuevo negocio en ComidITA!")

        # 5. Éxito: Lo mandamos al login con un mensaje positivo
        messages.success(request, '¡Cuenta creada exitosamente! Por favor, inicia sesión.')
        return redirect('login')

    # Si entra por primera vez, solo mostramos la página web
    return render(request, 'registro.html')