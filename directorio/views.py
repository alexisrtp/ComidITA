from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse
import json
from .models import Negocio, Producto, Pedido, Perfil, DetallePedido
from .forms import ProductoForm, NegocioForm

def login_vista(request):
    if request.method == 'POST':
        correo = request.POST.get('username')
        contra = request.POST.get('password')
        usuario = authenticate(request, username=correo, password=contra)

        if usuario is not None:
            login(request, usuario)

            # Verificamos qué tipo de usuario es
            if hasattr(usuario, 'negocio'):
                # Si tiene un negocio asociado, es Emprendedor y va a su panel.
                return redirect('panel_emprendedor')
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
def panel_pedidos_emprendedor(request):
    # Verificamos que el usuario tenga un negocio asociado
    negocio = Negocio.objects.filter(propietario=request.user).first()
    if not negocio:
        return redirect('inicio_cliente')

    # Obtenemos los pedidos pendientes y los que ya van en camino al punto ITA
    pedidos_pendientes = Pedido.objects.filter(
        negocio=negocio,
        estado__in=['PENDIENTE', 'EN_CAMINO']
    ).prefetch_related('items__producto').order_by('-fecha_creacion')

    # El historial solo contendrá los pedidos ya completados o cancelados
    pedidos_historial = Pedido.objects.filter(
        negocio=negocio,
        estado__in=['COMPLETADO', 'CANCELADO']
    ).prefetch_related('items__producto').order_by('-fecha_creacion')

    # Calculamos totales para cada pedido
    for p in pedidos_pendientes:
        p.total_calculado = sum(item.subtotal() for item in p.items.all())
    for p in pedidos_historial:
        p.total_calculado = sum(item.subtotal() for item in p.items.all())

    return render(request, 'panel_pedidos.html', {
        'negocio': negocio,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_historial': pedidos_historial,
    })


@login_required
def actualizar_estado_pedido(request, pedido_id):
    if request.method == 'POST':
        negocio = Negocio.objects.filter(propietario=request.user).first()
        pedido = get_object_or_404(Pedido, id=pedido_id, negocio=negocio)

        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')  # 'COMPLETADO' o 'CANCELADO'

            if nuevo_estado in ['EN_CAMINO', 'COMPLETADO', 'CANCELADO']:
                pedido.estado = nuevo_estado
                pedido.save()
                return JsonResponse({'status': 'ok'})

            return JsonResponse({'status': 'error', 'message': 'Estado no válido'}, status=400)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Error al actualizar'}, status=400)

    return JsonResponse({'status': 'error'}, status=405)

@login_required
def agregar_producto(request):
    # Buscamos de quién es el negocio
    negocio = Negocio.objects.filter(propietario=request.user).first()

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
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
    # Buscamos el perfil extra del usuario, o lo creamos si es su primera vez entrando
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'perfil':
            # 1. Guardamos los datos del User nativo
            request.user.first_name = request.POST.get('nombre')
            request.user.last_name = request.POST.get('apellidos')
            nuevo_correo = request.POST.get('correo')

            # 2. ¡GUARDAMOS EL TELÉFONO en nuestra tabla Perfil!
            perfil.telefono = request.POST.get('telefono')
            perfil.save()

            # 3. Validamos el correo
            if User.objects.filter(username=nuevo_correo).exclude(id=request.user.id).exists():
                messages.error(request, 'Ese correo ya está en uso por otra cuenta.')
            else:
                request.user.email = nuevo_correo
                request.user.username = nuevo_correo
                request.user.save()
                messages.success(request, '¡Tus datos y teléfono han sido actualizados!')

        elif action == 'seguridad':
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
                update_session_auth_hash(request, request.user)
                messages.success(request, '¡Tu contraseña ha sido cambiada con éxito!')

        return redirect('perfil')

    # Le enviamos la variable 'perfil' al HTML para que pueda imprimir el teléfono
    return render(request, 'perfil_cliente.html', {'perfil': perfil})


@login_required
def toggle_estado_negocio(request):
    if request.method == 'POST':
        # Buscamos el negocio del usuario actual
        negocio = Negocio.objects.filter(propietario=request.user).first()

        if negocio:
            # Leemos los datos JSON que mandó JavaScript
            data = json.loads(request.body)
            nuevo_estado = data.get('abierto', False)

            # Guardamos en la base de datos
            negocio.abierto = nuevo_estado
            negocio.save()

            return JsonResponse({'status': 'ok', 'abierto': negocio.abierto})

    return JsonResponse({'status': 'error'}, status=400)


def detalle_negocio(request, id):
    # Buscamos el negocio exacto por su ID. Si no existe, muestra error 404
    negocio = get_object_or_404(Negocio, id=id)

    # Traemos todos los productos que le pertenecen a este negocio
    productos = Producto.objects.filter(negocio=negocio)

    return render(request, 'detalle_negocio.html', {
        'negocio': negocio,
        'productos': productos
    })

def eliminar_producto(request, id):
    # Buscamos el producto por su ID, asegurando que pertenezca al usuario actual
    Producto.objects.filter(id=id, negocio__propietario=request.user).delete()
    return redirect('panel_emprendedor')


def editar_producto(request, id):
    # Buscamos el platillo asegurándonos de que pertenezca a este emprendedor
    producto = Producto.objects.filter(id=id, negocio__propietario=request.user).first()

    if request.method == 'POST':
        # Le pasamos los datos nuevos, la nueva foto (si hay), y el producto original
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('panel_emprendedor')
    else:
        # Si entra por primera vez, el formulario se precarga con los datos del producto
        form = ProductoForm(instance=producto)

    return render(request, 'editar_producto.html', {'form': form})


def editar_perfil_negocio(request):
    # Buscamos el negocio del emprendedor que inició sesión
    negocio = Negocio.objects.filter(propietario=request.user).first()

    if request.method == 'POST':
        # Le pasamos los datos y archivos (request.FILES) para guardar fotos y horarios
        form = NegocioForm(request.POST, request.FILES, instance=negocio)
        if form.is_valid():
            form.save()
            return redirect('panel_emprendedor')
    else:
        # Precargamos los datos que ya tiene el negocio (si es que ya los llenó antes)
        form = NegocioForm(instance=negocio)

    return render(request, 'editar_negocio.html', {'form': form, 'negocio': negocio})


@login_required
def mis_pedidos_view(request):
    # --- IMPRESIÓN DE DEPURACIÓN EN TERMINAL ---
    print(f"DEBUG USUARIO ACTUAL: {request.user} (ID: {request.user.id})")

    todos_los_pedidos = Pedido.objects.filter(comprador=request.user)
    print(f"DEBUG TOTAL PEDIDOS DE ESTE USUARIO EN BD: {todos_los_pedidos.count()}")
    for p in todos_los_pedidos:
        print(f" -> Pedido ID: {p.id} | Folio: {p.folio} | Estado en BD: '{p.estado}'")
    # -------------------------------------------

    pedidos_en_curso = Pedido.objects.filter(
        comprador=request.user,
        estado__in=['PENDIENTE', 'EN_CAMINO']
    ).select_related('negocio').prefetch_related('items__producto').order_by('-fecha_creacion')

    for pedido in pedidos_en_curso:
        pedido.total_calculado = sum(item.subtotal() for item in pedido.items.all())

    historial_pedidos = Pedido.objects.filter(
        comprador=request.user,
        estado__in=['COMPLETADO', 'CANCELADO']
    ).select_related('negocio').prefetch_related('items__producto').order_by('-fecha_creacion')

    for pedido in historial_pedidos:
        pedido.total_calculado = sum(item.subtotal() for item in pedido.items.all())

    return render(request, 'mis_pedidos.html', {
        'pedidos_en_curso': pedidos_en_curso,
        'historial_pedidos': historial_pedidos,
    })


def detalle_negocio(request, id):
    negocio = get_object_or_404(Negocio, id=id)
    # Solo mostramos platillos marcados como disponibles
    productos = Producto.objects.filter(negocio=negocio, disponible=True)

    return render(request, 'detalle_negocio.html', {
        'negocio': negocio,
        'productos': productos,
        'puntos_entrega': Pedido.PUNTOS_ENTREGA,
    })


@login_required
def crear_pedido(request, id):
    if request.method == 'POST':
        negocio = get_object_or_404(Negocio, id=id)

        # Validamos que el negocio esté abierto
        if not negocio.esta_abierto_ahora:
            return JsonResponse({'status': 'error', 'message': 'El negocio acaba de cerrar.'}, status=400)

        try:
            data = json.loads(request.body)
            punto_encuentro = data.get('punto_encuentro')
            horario_entrega = data.get('horario_entrega')
            items = data.get('items', [])

            if not items or not punto_encuentro or not horario_entrega:
                return JsonResponse({'status': 'error', 'message': 'Completa el punto y hora de entrega.'}, status=400)

            # Guardamos todo en una transacción segura
            with transaction.atomic():
                nuevo_pedido = Pedido.objects.create(
                    comprador=request.user,
                    negocio=negocio,
                    punto_encuentro=punto_encuentro,
                    horario_entrega=horario_entrega,
                    estado='PENDIENTE'
                )

                for item in items:
                    producto = get_object_or_404(Producto, id=item['id'], negocio=negocio)
                    cantidad = int(item['cantidad'])

                    # Si el producto tiene límite de unidades, verificamos y descontamos
                    if producto.unidades_disponibles is not None:
                        if cantidad > producto.unidades_disponibles:
                            raise ValueError(
                                f"Solo quedan {producto.unidades_disponibles} unidades de {producto.nombre}.")
                        producto.unidades_disponibles -= cantidad
                        if producto.unidades_disponibles == 0:
                            producto.disponible = False
                        producto.save()

                    DetallePedido.objects.create(
                        pedido=nuevo_pedido,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio
                    )

            return JsonResponse({
                'status': 'ok',
                'folio': nuevo_pedido.folio,
                'redirect_url': reverse('mis_pedidos')
            })

        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'No se pudo procesar tu pedido.'}, status=400)

    return JsonResponse({'status': 'error'}, status=405)

