from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_vista(request):
    # Si el usuario ya inició sesión, no tiene sentido que vea el login, lo mandamos al inicio
    if request.user.is_authenticated:
        return redirect('dashboard') # Crearemos esta ruta después

    if request.method == 'POST':
        # Capturamos lo que el usuario escribió en los inputs del HTML
        correo = request.POST.get('username')
        contra = request.POST.get('password')

        # Django verifica encriptado si el usuario y contraseña coinciden en la base de datos
        user = authenticate(request, username=correo, password=contra)

        if user is not None:
            # Si es correcto, iniciamos la sesión
            login(request, user)
            return redirect('dashboard') # Lo enviamos a su panel
        else:
            # Si se equivoca, mandamos un mensaje de error a la pantalla
            messages.error(request, 'Correo o contraseña incorrectos. Intenta de nuevo.')

    return render(request, 'login.html')