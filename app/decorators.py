from pyexpat.errors import messages
from django.shortcuts import redirect, render

def conductor_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'conductor'):
            return view_func(request, *args, **kwargs)
        else:
            return redirect('pagina_no_autorizada')  # Redirige si no es conductor
    return _wrapped_view

def apoderado_required(view_func):
    def wrapper (request, *args, **kwargs):
        if hasattr(request.user, 'apoderado'):
            return view_func(request, *args, **kwargs)
        else:
             messages.error(request, 'No tienes permiso para acceder a esta página.')
             return render(request, 'error_permiso.html')
    return wrapper