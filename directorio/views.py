from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Negocio
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Negocio, Producto, Pedido
from .forms import ProductoForm


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
    # 1. Capturamos lo que el usuario escribió en la barra de búsqueda
    query = request.GET.get('q', '')

    # 2. Si el usuario escribió algo, filtramos la base de datos
    if query:
        # Buscamos en el nombre OR (|) en la descripción del negocio
        negocios = Negocio.objects.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        ).distinct()
    else:
        # Si la barra está vacía, mostramos todos los negocios
        negocios = Negocio.objects.all()

    # Enviamos los negocios y la palabra buscada al HTML
    return render(request, 'inicio_cliente.html', {
        'negocios': negocios,
        'query': query
    })


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


@login_required
def panel_emprendedor(request):
    # Buscamos el negocio del usuario logueado
    negocio = Negocio.objects.filter(propietario=request.user).first()

    # Si tiene un negocio registrado, traemos su menú y pedidos pendientes
    productos = Producto.objects.filter(negocio=negocio) if negocio else []
    pedidos = Pedido.objects.filter(negocio=negocio, estado='PENDIENTE') if negocio else []

    context = {
        'negocio': negocio,
        'productos': productos,
        'pedidos': pedidos,
    }
    return render(request, 'panel_emprendedor.html', context)


@login_required
def agregar_producto(request):
    # Buscamos de quién es el negocio
    negocio = Negocio.objects.filter(propietario=request.user).first()

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            # Pausamos el guardado un segundo para inyectarle de quién es el producto
            producto = form.save(commit=False)
            producto.negocio = negocio
            producto.save()  # Ahora sí lo guardamos en MySQL
            return redirect('panel_emprendedor')  # Lo regresamos a su panel
    else:
        form = ProductoForm()  # Mostramos el formulario vacío

    return render(request, 'agregar_producto.html', {'form': form})


# --- VISTA DE PERFIL Y SEGURIDAD ---
def perfil_view(request):
    if request.method == 'POST':
        # Identificamos qué formulario se envió usando un campo oculto 'action'
        action = request.POST.get('action')

        if action == 'perfil':
            # Actualizamos los datos personales
            request.user.first_name = request.POST.get('nombre')
            request.user.last_name = request.POST.get('apellidos')
            nuevo_correo = request.POST.get('correo')

            # Validamos que el correo no esté usado por otro usuario
            if User.objects.filter(username=nuevo_correo).exclude(id=request.user.id).exists():
                messages.error(request, 'Ese correo ya está en uso por otra cuenta.')
            else:
                request.user.email = nuevo_correo
                request.user.username = nuevo_correo  # En nuestro sistema, el username es el correo
                request.user.save()
                messages.success(request, '¡Tus datos personales han sido actualizados!')

        elif action == 'seguridad':
            # Lógica para cambiar contraseña
            actual = request.POST.get('contra_actual')
            nueva1 = request.POST.get('contra_nueva1')
            nueva2 = request.POST.get('contra_nueva2')

            if not request.user.check_password(actual):
                messages.error(request, 'La contraseña actual es incorrecta.')
            elif nueva1 != nueva2:
                messages.error(request, 'Las contraseñas nuevas no coinciden.')
            else:
                request.user.set_password(nueva1)
                request.user.save()
                # Esta línea evita que se cierre la sesión tras cambiar la clave
                update_session_auth_hash(request, request.user)
                messages.success(request, '¡Tu contraseña ha sido cambiada con éxito!')

        return redirect('perfil')

    return render(request, 'perfil_cliente.html')