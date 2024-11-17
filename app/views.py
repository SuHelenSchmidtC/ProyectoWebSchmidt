# views.py
from datetime import datetime, timezone
from pyexpat.errors import messages
from django.contrib import messages

from urllib import request
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LoginView
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views import View
from django.core import serializers
from django.utils import timezone
from datetime import timedelta

from django.http import HttpResponseBadRequest  # Agrega esta línea


from django.contrib.auth.mixins import LoginRequiredMixin
import requests
from .forms import (
    AlumnoForm,
    ConductorDocumentosForm,
    DatosVehiculoForm,
    RegistroConductorForm,
    RegistroApoderadoForm,
    RutaForm,
  
)
from .models import (
    Alumno,
    Colegio,
    Conversacion,
    CustomUser,
    DocumentosPersonales,
    DocumentosVehiculo,
    Mensaje,
    Ruta,
    Solicitud,
    SolicitudVinculacion,
    Conductor,
    Apoderado,
    Vehiculo,
    Viaje,
)

def home(request):
    # Redirigir según el tipo de usuario
    if request.user.is_authenticated:
        if hasattr(request.user, 'conductor'):
            return redirect('home_conductor')
        elif hasattr(request.user, 'apoderado'):
            return redirect('home_apoderado')
    return render(request, 'app/home.html') 


# Nueva vista para elegir entre conductor o apoderado
def elegir_tipo_registro(request):
    return render(request, 'registration/elegir_tipo_registro.html')
# Vista de registro para conductores
def registro_conductor(request):
    if request.method == 'POST':
        form = RegistroConductorForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('subir_documentos')
    else:
        form = RegistroConductorForm()
    return render(request, 'registration/registro_conductor.html', {'form': form})

# Vista de registro para apoderados
def registro_apoderado(request):
    if request.method == 'POST':
        form = RegistroApoderadoForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('crear_alumno')  # Redirigir a home_apoderado después del registro
    else:
        form = RegistroApoderadoForm()
    return render(request, 'registration/registro_apoderado.html', {'form': form})



class CustomLoginView(LoginView):
    template_name = 'registration/login.html' 
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        if hasattr(self.request.user, 'conductor'):
            return HttpResponseRedirect(reverse('home_conductor'))
        elif hasattr(self.request.user, 'apoderado'):
            # Verificar si el apoderado tiene una solicitud aceptada
            apoderado = self.request.user.apoderado
            solicitud_aceptada = SolicitudVinculacion.objects.filter(apoderado=apoderado, estado='aceptada').exists()
            if solicitud_aceptada:
                return HttpResponseRedirect(reverse('home_apoderado'))
            else:
                return HttpResponseRedirect(reverse('home_apoderado'))
        return response


@login_required
@login_required
@login_required
def home_apoderado(request):
    try:
        apoderado = Apoderado.objects.get(user=request.user)
    except Apoderado.DoesNotExist:
        return redirect('registro_apoderado')

    conductores_vinculados = apoderado.conductores.all()
    alumnos = apoderado.alumnos.all()
    alumno_seleccionado = None
    solicitud = None

    if request.method == 'POST':
        alumno_id = request.POST.get('alumno_id')
        alumno_seleccionado = get_object_or_404(Alumno, id=alumno_id)
        solicitud = SolicitudVinculacion.objects.filter(alumnos=alumno_seleccionado, estado='Aceptada').first()

    context = {
        'conductores_vinculados': conductores_vinculados,
        'alumnos': alumnos,
        'alumno_seleccionado': alumno_seleccionado,
        'solicitud': solicitud,
        'nombre_apoderado': request.user.nombre,  # Añadir el nombre del apoderado
        'apellido_apoderado': request.user.apellido,
    }
    return render(request, 'apoderado/home_apoderado.html', context)

@login_required
def home_conductor(request):
    try:
        conductor = Conductor.objects.get(user=request.user)
        apoderados = conductor.apoderados.prefetch_related('alumnos').all()
        rutas = Ruta.objects.filter(conductor=conductor).first() 

        # Obtener todos los alumnos vinculados a los apoderados del conductor
        alumnos_vinculados = Alumno.objects.filter(apoderado__in=apoderados).distinct()
    except Conductor.DoesNotExist:
        raise Http404("El conductor no existe.")

    return render(request, 'conductor/home_conductor.html', {
        'conductor': conductor,
        'apoderados': apoderados,
        'alumnos_vinculados': alumnos_vinculados,
        'ruta': rutas,  # Pasa rutas al contexto

    })

@login_required
def crear_alumno(request):
    if request.method == 'POST':
        form = AlumnoForm(request.POST)
        if form.is_valid():
            alumno = form.save(commit=False)
            alumno.apoderado = request.user.apoderado 
            alumno.save()
            if 'agregar_otro' in request.POST:
                return redirect('crear_alumno')
            else:
                return redirect('buscar_conductor')
    else:
        form = AlumnoForm()
    return render(request, 'apoderado/crear_alumno.html', {'form': form})
# Vista para buscar colegios

def buscar_colegios(request):
    if 'term' in request.GET:  # Verifica si hay un término de búsqueda
        term = request.GET.get('term')
        colegios = Colegio.objects.filter(nombre_colegio__icontains=term)  # Filtra colegios que contengan el término
        results = [{'id': colegio.id, 'text': colegio.nombre_colegio} for colegio in colegios]  # Formato para el autocompletar
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)  



class BuscarDireccion(View):
    def get(self, request):
        query = request.GET.get('query', '')  # Obtiene la consulta de la dirección
        api_key = 'AIzaSyCedrHqDHfOCXIrKmE6rOojfIupDj-BKYE'  # Reemplaza con tu clave de API
        url = f'https://maps.googleapis.com/maps/api/place/autocomplete/json?input={query}&key={api_key}'
        
        response = requests.get(url)
        data = response.json()

        # Extrae las direcciones de la respuesta
        direcciones = [
            {
                'nombre': prediction['description'],  # Nombre de la dirección
                'id': prediction['place_id']  # ID del lugar
            } for prediction in data.get('predictions', [])
        ]
        
        return JsonResponse(direcciones, safe=False)
    

    
@login_required
def buscar_conductor(request):
    conductores = Conductor.objects.filter(disponible=True)
    if request.method == 'POST':
        conductor_id = request.POST.get('conductor_id')
        return redirect('crear_solicitud_vinculacion', conductor_id=conductor_id)
    return render(request, 'apoderado/buscar_conductor.html', {'conductores': conductores})


# views.py
####sioc
@login_required
def aceptar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudVinculacion, id=solicitud_id, conductor=request.user.conductor)
    
    if request.method == 'POST':
   
        # Cambiar el estado de la solicitud a aceptada
        solicitud.estado = 'Aceptada'
        solicitud.save()
     # Asumimos que `alumno` está relacionado con la solicitud
        alumnos = solicitud.alumnos.all()  # Obtener todos los alumnos de la solicitud
        
        # Crear o obtener la ruta del conductor
        ruta, created = Ruta.objects.get_or_create(conductor=request.user.conductor)

        # Asignar los alumnos a la ruta
        for alumno in alumnos:
            alumno.ruta = ruta  # Asegúrate de que el modelo Alumno tiene el campo 'ruta'
            alumno.conductor = request.user.conductor  # Asignar el conductor al alumno
            alumno.save()

        return redirect('vinculaciones')  # Redirige a la vista de vinculaciones

    return render(request, 'conductor/aceptar_solicitud.html', {'solicitud': solicitud})

@login_required
def crear_solicitud_vinculacion(request, conductor_id):
    conductor = get_object_or_404(Conductor, id=conductor_id)
    alumnos = request.user.apoderado.alumnos.all()

    if request.method == 'POST':
        solicitud = SolicitudVinculacion(
            apoderado=request.user.apoderado,
            conductor=conductor,
            estado='Pendiente'
        )
        solicitud.save()  

        alumnos_ids = request.POST.getlist('alumnos_ids')
        for alumno_id in alumnos_ids:
            solicitud.alumnos.add(alumno_id)

        solicitud.save()  
        return redirect('SolicitudesApoderados')

    return render(request, 'apoderado/crear_solicitud_vinculacion.html', {'conductor': conductor, 'alumnos': alumnos})

class Vinculaciones(View):
    def get(self, request):
        conductor = request.user.conductor  
        solicitudes_pendientes = SolicitudVinculacion.objects.filter(conductor=conductor, estado='Pendiente')
        apoderados_aceptados = SolicitudVinculacion.objects.filter(conductor=conductor, estado='Aceptada')
        
        return render(request, 'conductor/vinculaciones.html', {
            'solicitudes_pendientes': solicitudes_pendientes,
            'apoderados_aceptados': apoderados_aceptados
        })
    
    def post(self, request):
        conductor = request.user.conductor
        solicitud_id = request.POST.get('solicitud_id')
        accion = request.POST.get('accion')  # 'aceptar' o 'rechazar'

        solicitud = get_object_or_404(SolicitudVinculacion, id=solicitud_id, conductor=conductor)

        if accion == 'aceptar':
            solicitud.estado = 'Aceptada'
            solicitud.save()
            messages.success(request, "La solicitud ha sido aceptada.")



          
            
        

        elif accion == 'rechazar':
            solicitud.estado = 'Rechazada'
            solicitud.save()

        # Mantén la redirección a la misma página de vinculaciones
        return redirect('vinculaciones')



class SolicitudesApoderados(LoginRequiredMixin, View):
    def get(self, request):
        apoderado = request.user.apoderado
        solicitudes = SolicitudVinculacion.objects.filter(apoderado=apoderado)

        # Verificar si el apoderado tiene al menos un alumno aceptado
        tiene_alumno_aceptado = SolicitudVinculacion.objects.filter(
            apoderado=apoderado, 
            estado='Aceptada'  # Asegúrate de que el estado sea coherente aquí
        ).exists()

        # Redirigir al home_apoderado si hay solicitudes pendientes y no hay alumnos aceptados
        if solicitudes.filter(estado='Pendiente').exists() and not tiene_alumno_aceptado:
            return redirect('home_apoderado')

        return render(request, 'apoderado/solicitudes_apoderados.html', {'solicitudes': solicitudes})



@login_required
def ver_conductor_alumno(request):
    if request.method == 'POST':
        alumno_id = request.POST.get('alumno_id')
        alumno = get_object_or_404(Alumno, id=alumno_id)
        solicitud = SolicitudVinculacion.objects.filter(alumnos=alumno, estado='Aceptada').first()

        context = {
            'alumno': alumno,
            'solicitud': solicitud,
        }
        return render(request, 'apoderado/ver_conductor_alumno.html', context)
    return redirect('home_apoderado')  # Redirigir si no es POST
@login_required


def listar_conductores(request):
    conductores = Conductor.objects.all()  # Obtén todos los conductores

    if request.method == 'POST':
        destinatario_id = request.POST.get('destinatario_id')
        contenido = request.POST.get('contenido')

        try:
            destinatario = Conductor.objects.get(id=destinatario_id)
            # Crea el mensaje
            Mensaje.objects.create(remitente=request.user, destinatario=destinatario.user, contenido=contenido)
            messages.success(request, 'Mensaje enviado con éxito.')
        except Conductor.DoesNotExist:
            messages.error(request, 'El conductor no existe.')

    return render(request, 'apoderado/listar_conductores.html', {'conductores': conductores})


@login_required
def gestion_alumnos(request):
    # Lógica para gestionar alumnos
    alumnos = request.user.apoderado.alumnos.all()  # Por ejemplo, obtener los alumnos del apoderado
    return render(request, 'apoderado/gestion_alumnos.html', {'alumnos': alumnos})

def subir_documentos(request):
    conductor = request.user.conductor  # Obtener el conductor autenticado
    # Usar el related_name 'documentos_personales' en lugar de 'documentospersonales_set'
    if conductor.documentos_personales.exists():  # Verificar si ya subió documentos
        return redirect('subir_datos_vehiculo')  # Si ya subió documentos, redirigir a subir datos del vehículo

    if request.method == 'POST':
        form = ConductorDocumentosForm(request.POST, request.FILES)
        if form.is_valid():
            documentos = form.save(commit=False)
            documentos.conductor = conductor  # Asociar los documentos con el conductor
            documentos.save()
            return redirect('subir_datos_vehiculo')  # Redirigir a la página para subir datos del vehículo
    else:
        form = ConductorDocumentosForm()
    return render(request, 'conductor/subir_documentos.html', {'form': form})

def subir_datos_vehiculo(request):
    conductor = request.user.conductor  # Obtener el conductor autenticado
    if hasattr(conductor, 'vehiculo'):  # Verificar si ya ha registrado el vehículo
        return redirect('home_conductor')  # Si ya se registró el vehículo, redirigir al home

    if request.method == 'POST':
        form = DatosVehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.conductor = conductor
            vehiculo.save()
            return redirect('home_conductor')  # Redirigir al home si todo está completo
    else:
        form = DatosVehiculoForm()
    return render(request, 'conductor/subir_datos_vehiculo.html', {'form': form})


def gestionar_documentos(request):
    documentos_personales, created = DocumentosPersonales.objects.get_or_create(conductor=request.user.conductor)
    vehiculo = Vehiculo.objects.filter(conductor=request.user.conductor).first()  # Asumiendo que un conductor puede tener un vehículo

    # Manejo de eliminación de documentos
    if request.method == 'POST':
        documento_id = request.POST.get('documento_id')
        if 'eliminar_documento_licencia' in request.POST:
            documentos_personales.licencia.delete()  # Eliminar archivo de licencia
            documentos_personales.licencia = None  # Limpiar campo
            documentos_personales.save()
        elif 'eliminar_documento_certificado' in request.POST:
            documentos_personales.certificado.delete()  # Eliminar archivo de certificado
            documentos_personales.certificado = None  # Limpiar campo
            documentos_personales.save()
        elif 'eliminar_documento_vehiculo' in request.POST:
            # Lógica para eliminar documentos de vehículo, si aplica
            pass

    return render(request, 'conductor/gestionar_documentos.html', {
        'documentos_personales': documentos_personales,
        'vehiculo': vehiculo,
        'documentos_vehiculo': DocumentosVehiculo.objects.filter(vehiculo=vehiculo)
    })




@login_required
def ver_documentos_conductor(request, conductor_id):
    # Obtiene el apoderado y el conductor correspondiente
    apoderado = get_object_or_404(Apoderado, user=request.user)
    conductor = get_object_or_404(Conductor, id=conductor_id)
    
    # Verificar si el apoderado tiene una solicitud aceptada con este conductor
    solicitud_aceptada = SolicitudVinculacion.objects.filter(
        apoderado=apoderado,
        conductor=conductor,
        estado='Aceptada'
    ).exists()
    
    if not solicitud_aceptada:
        # Si no hay solicitud aceptada, redirige o muestra un mensaje
        return redirect('home_apoderado')  # O muestra un mensaje de error

    # Obtener los documentos del conductor
    documentos = DocumentosPersonales.objects.filter(conductor=conductor)

    return render(request, 'apoderado/ver_documentos_conductores.html', {
        'conductor': conductor,
        'documentos': documentos
    })


def chat_view(request, chat_id):
    return render(request, 'mensaje/chat.html', {'chat_id': chat_id, 'user_id': request.user.id})



@login_required
def ver_mensajes(request):
    # Recupera conversaciones donde el usuario actual es parte
    conversaciones = Conversacion.objects.filter(participante_1=request.user) | Conversacion.objects.filter(participante_2=request.user)

    return render(request, 'mensaje/ver_mensajes.html', {
        'conversaciones': conversaciones,
    })

@login_required
def ver_conversacion(request, conversacion_id):
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    
    # Asegúrate de que el usuario es parte de la conversación
    if request.user not in [conversacion.participante_1, conversacion.participante_2]:
        return redirect('ver_mensajes')

    mensajes = Mensaje.objects.filter(conversacion=conversacion).order_by('fecha_enviado')

    # Debug: imprime los mensajes recuperados
    for mensaje in mensajes:
        print(f'Mensaje: {mensaje.contenido}, Remitente: {mensaje.remitente.nombre}, Fecha: {mensaje.fecha_enviado}')

    if request.method == 'POST':
        contenido = request.POST.get('contenido')
        
        # Envía el mensaje
        Mensaje.objects.create(
            remitente=request.user,
            destinatario=conversacion.participante_2 if conversacion.participante_1 == request.user else conversacion.participante_1,
            contenido=contenido,
            conversacion=conversacion
        )
        
        messages.success(request, 'Mensaje enviado con éxito.')
        return redirect('ver_conversacion', conversacion_id=conversacion.id)

    return render(request, 'mensaje/ver_conversacion.html', {
        'conversacion': conversacion,
        'mensajes': mensajes
    })

@login_required
def enviar_mensaje(request):
    if request.method == 'POST':
        contenido = request.POST.get('contenido')
        destinatario_id = request.POST.get('destinatario_id')

        # Verifica si el destinatario existe
        try:
            destinatario = CustomUser.objects.get(id=destinatario_id)
        except CustomUser.DoesNotExist:
            messages.error(request, 'El destinatario no existe.')
            return redirect('ver_mensajes')

        # Verifica si ya existe una conversación
        conversacion, created = Conversacion.objects.get_or_create(
            participante_1=request.user,
            participante_2=destinatario
        )

        # Envía el mensaje
        Mensaje.objects.create(
            remitente=request.user,
            destinatario=destinatario,
            contenido=contenido,
            conversacion=conversacion
        )
        messages.success(request, 'Mensaje enviado con éxito.')
        return redirect('ver_conversacion', conversacion_id=conversacion.id)
  
     # Filtrar los usuarios a los que se puede enviar el mensaje
    if hasattr(request.user, 'conductor'):
        # Obtener apoderados vinculados
        apoderados_vinculados = request.user.conductor.apoderados.all()  # Ajusta esta línea
        context = {'usuarios': apoderados_vinculados}
    else:
        context = {'usuarios': []}  # Si no es conductor, no hay usuarios disponibles
    return render(request, 'mensaje/enviar_mensaje.html', context)


@login_required
def cargar_conversacion(request, conversacion_id):
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    mensajes = Mensaje.objects.filter(conversacion=conversacion).order_by('fecha_enviado')
    
    # Convertir los mensajes a JSON
    data = serializers.serialize('json', mensajes, fields=('remitente', 'contenido', 'fecha_enviado'))
    return JsonResponse({'mensajes': data})



@login_required
def datos_personales(request):
    apoderado = Apoderado.objects.get(user=request.user)  # Obtener el apoderado que está logueado
    context = {
        'apoderado': apoderado
    }
    return render(request, 'apoderado/datos_personales.html', context)




def cambiar_ruta(request, alumno_id):
    alumno = Alumno.objects.get(id=alumno_id)
    rutas_existentes = Ruta.objects.filter(conductor=request.user)

    if request.method == 'POST':
        # Aquí puedes agregar la lógica para cambiar la ruta
        return redirect('listar_alumnos')

    return render(request, 'conductor/listar_alumnos.html', {'alumno': alumno, 'rutas': rutas_existentes})



def asignar_ruta(request, alumno_id):
    alumno = Alumno.objects.get(id=alumno_id)
    rutas_existentes = Ruta.objects.filter(conductor=request.user)

    if request.method == 'POST':
        # Aquí puedes agregar la lógica para asignar la ruta
        nueva_ruta_id = request.POST['nueva_ruta']
        nueva_ruta = Ruta.objects.get(id=nueva_ruta_id)
        nueva_ruta.alumnos.add(alumno)
        return redirect('listar_alumnos')

    return render(request, 'conductor/listar_alumnos.html', {'alumno': alumno, 'rutas': rutas_existentes})

#vwe alumnnos q tiene el conducto



@login_required
def ver_alumnos_vinculados(request):
    try:
        # Obtener el conductor autenticado
        conductor = Conductor.objects.get(user=request.user)
        
        # Obtener las solicitudes aceptadas relacionadas con el conductor
        solicitudes_aceptadas = SolicitudVinculacion.objects.filter(conductor=conductor, estado='Aceptada')
        
        # Obtener los alumnos vinculados a esas solicitudes
        alumnos_vinculados = Alumno.objects.filter(solicitudvinculacion__in=solicitudes_aceptadas).distinct()
        


        # Obtener las rutas del conductor
        rutas = Ruta.objects.filter(conductor=conductor)


    except Conductor.DoesNotExist:
        # Si el usuario autenticado no es un conductor, mostrar un error o redirigir
        return redirect('registro_conductor')

    # Pasar los datos al template
    context = {
        'conductor': conductor,
        'alumnos_vinculados': alumnos_vinculados,
        'rutas': rutas,

    
    }
    return render(request, 'conductor/ver_alumnos_vinculados.html', context)

@login_required
def gestionar_rutas(request):
    # Verifica si el usuario tiene un perfil de conductor
    try:
        conductor = request.user.conductor  # Si usas una relación OneToOne
    except Conductor.DoesNotExist:
        return redirect('home')  # Redirige si el usuario no es un conductor

    # Obtiene todas las rutas del conductor autenticado
    rutas = Ruta.objects.filter(conductor=conductor)

    # Filtra solo los alumnos vinculados al conductor
    solicitudes_aceptadas = SolicitudVinculacion.objects.filter(conductor=conductor, estado='Aceptada')
    alumnos_vinculados = Alumno.objects.filter(solicitudvinculacion__in=solicitudes_aceptadas).distinct()
    vehiculos = Vehiculo.objects.filter(conductor=conductor)  # Obtiene los vehículos del conductor
    
    # Inicializa el formulario
    form = RutaForm()

    if request.method == 'POST':
        if 'crear_ruta' in request.POST:
            form = RutaForm(request.POST)
            if form.is_valid():
                nueva_ruta = form.save(commit=False)
                nueva_ruta.conductor = conductor  # Asocia la ruta al conductor autenticado
                
                # Asegúrate de obtener el ID del vehículo del POST
                vehiculo_id = request.POST.get('vehiculo_id')  # Cambia 'vehiculo_id' por el nombre real que usas en tu formulario
                if vehiculo_id:  # Verifica si se ha proporcionado un ID de vehículo
                    nueva_ruta.vehiculo = Vehiculo.objects.get(id=vehiculo_id)  # Asocia el vehículo
                
                nueva_ruta.save()  # Guarda la nueva ruta
                return redirect('gestionar_rutas')

        elif 'editar_ruta' in request.POST:
            ruta_id = request.POST.get('ruta_id')
            ruta = get_object_or_404(Ruta, id=ruta_id, conductor=conductor)
            form = RutaForm(request.POST, instance=ruta)
            if form.is_valid():
                form.save()
                return redirect('gestionar_rutas')

        elif 'eliminar_ruta' in request.POST:
            ruta_id = request.POST.get('ruta_id')
            ruta = get_object_or_404(Ruta, id=ruta_id, conductor=conductor)
            ruta.delete()
            return redirect('gestionar_rutas')

        elif 'asignar_alumnos' in request.POST:
            ruta_id = request.POST.get('ruta_id')  # Obtener el ID de la ruta seleccionada
            ruta = get_object_or_404(Ruta, id=ruta_id)  # Obtener la ruta
            alumnos_seleccionados = request.POST.getlist('alumnos')  # Obtener los IDs de los alumnos seleccionados

            # Asignar los alumnos seleccionados a la ruta
            for alumno_id in alumnos_seleccionados:
                alumno = Alumno.objects.get(id=alumno_id)
                ruta.alumnos.add(alumno)  # Agregar el alumno a la ruta

            return redirect('gestionar_rutas')  # Redirigir después de asignar alumnos

    # Construir la lista de rutas con alumnos asignados
    rutas_con_alumnos = []
    for ruta in rutas:
        alumnos_asignados = ruta.alumnos.all()
        rutas_con_alumnos.append({
            'ruta': ruta,
            'alumnos': ruta.alumnos.all(),
            'vehiculo': ruta.vehiculo, 
            'direcciones': [alumno.direccion for alumno in alumnos_asignados]  # Lista de direcciones
        })
    rutas_con_alumnos = [{'ruta': ruta, 'alumnos': ruta.alumnos.all(), 'vehiculo': ruta.vehiculo} for ruta in rutas]

    return render(request, 'conductor/gestionar_rutas.html', {
        'form': form,
        'rutas_con_alumnos': rutas_con_alumnos,
        'alumnos': alumnos_vinculados,
        'vehiculos': vehiculos,  # Agrega los vehículos disponibles al contexto para el formulario
    })



    # Vista para asignar alumnos a una ruta
def asignar_alumnos(request):
    rutas = Ruta.objects.all()  # Obtener todas las rutas
    alumnos = Alumno.objects.filter(conductor=request.user)  # Obtener los alumnos asignados al conductor actual

    if request.method == 'POST':
        ruta_id = request.POST.get('ruta_id')  # Obtener el ID de la ruta seleccionada
        ruta = get_object_or_404(Ruta, id=ruta_id)  # Obtener la ruta o lanzar un error 404 si no existe
        alumnos_seleccionados = request.POST.getlist('alumnos')  # Obtener los IDs de los alumnos seleccionados

        # Asignar los alumnos seleccionados a la ruta
        for alumno_id in alumnos_seleccionados:
            alumno = Alumno.objects.get(id=alumno_id)
            ruta.alumnos.add(alumno)  # Agregar el alumno a la ruta

        return redirect('gestionar_rutas')  # Redirigir después de asignar alumnos

    context = {
        'rutas': rutas,
        'alumnos': alumnos
    }
    return render(request, 'conductor/gestionar_rutas.html', context)



def quitar_alumno(request):
    if request.method == "POST":
        ruta_id = request.POST.get('ruta_id')
        alumno_id = request.POST.get('alumno_id')
        ruta = Ruta.objects.get(id=ruta_id)
        alumno = Alumno.objects.get(id=alumno_id)
        ruta.alumnos.remove(alumno)
        return JsonResponse({'success': True})

@login_required
def visualizar_recorrido(request, ruta_id):
    # Verifica si el usuario tiene un perfil de conductor
    try:
        conductor = request.user.conductor
    except Conductor.DoesNotExist:
        return redirect('home')

    # Obtiene la ruta específica
    ruta = get_object_or_404(Ruta, id=ruta_id, conductor=conductor)
    
    # Obtiene los alumnos asignados a la ruta
    alumnos_asignados = ruta.alumnos.all()

    # Obtiene las direcciones de los alumnos
    direcciones = [alumno.direccion for alumno in alumnos_asignados]
    vehiculo = ruta.vehiculo  # Obtener el vehículo asignado a la ruta

    return render(request, 'conductor/visualizar_recorrido.html', {
        'ruta': ruta,
        'alumnos_asignados': alumnos_asignados,
        'vehiculo': vehiculo,
        'direcciones': direcciones,
    })

@login_required
def elegir_ruta(request):
    try:
        # Intenta obtener el objeto Conductor asociado al usuario actual
        conductor = request.user.conductor
    except Conductor.DoesNotExist:
        # Si no existe, devuelve un error 403
        return JsonResponse({'error': 'No tienes permiso para ver estas rutas.'}, status=403)

    # Obtiene las rutas asociadas al conductor
    rutas = Ruta.objects.filter(conductor=conductor)

    # Renderiza la plantilla con las rutas disponibles
    return render(request, 'conductor/elegir_ruta.html', {'rutas': rutas})



def simulador_recorrido(request, ruta_id):
    # Recuperar la ruta por su ID
    ruta = get_object_or_404(Ruta, id=ruta_id)
     # Verificar si el usuario es un apoderado
    if not request.user.is_apoderado:
        return redirect('home')  # Redirigir a la página de inicio si no es apoderado
    
    # Suponiendo que cada Ruta tiene una relación con los Alumnos asignados
    alumnos_asignados = ruta.alumnos.all()  # Cambia esto según tu relación


    # Filtrar los alumnos asignados para obtener solo los que pertenecen a este apoderado
    alumnos_apoderado = alumnos_asignados.filter(apoderado=request.user.apoderado)

    # Si el apoderado no tiene alumnos en esta ruta, redirigir
    if not alumnos_apoderado:
        return redirect('home')  # O la página que consideres más apropiada
    # Renderizar la plantilla con el contexto necesario
    return render(request, 'conductor/visualizar_recorrido.html', {
        'ruta': ruta,
        'alumnos_asignados': alumnos_asignados,
        'ws_url': 'ws://localhost:8000/ws/seguimiento/'  # Asegúrate de que esta URL sea correcta para producción

    })



def gestionar_vehiculos(request, vehiculo_id=None):
    # Verifica si se está editando un vehículo específico
    if vehiculo_id:
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    else:
        vehiculo = None

    # Manejar eliminación de vehículo
    if request.method == 'POST' and 'eliminar' in request.POST:
        vehiculo_a_eliminar = get_object_or_404(Vehiculo, id=request.POST['eliminar'])
        vehiculo_a_eliminar.delete()
        return redirect('gestionar_vehiculos')  # Redirigir a la misma página después de eliminar

    # Manejar creación y actualización de vehículo
    if request.method == 'POST':
        if vehiculo:
            form = DatosVehiculoForm(request.POST, request.FILES, instance=vehiculo)
        else:
            form = DatosVehiculoForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('gestionar_vehiculos')  # Redirigir a la misma página después de guardar

    else:
        form = DatosVehiculoForm(instance=vehiculo)

    # Obtener todos los vehículos para mostrarlos
    vehiculos = Vehiculo.objects.all()

    return render(request, 'conductor/gestionar_vehiculos.html', {'form': form, 'vehiculos': vehiculos})


@login_required
def ver_rutas_apoderado(request):
    try:
        # Verifica si el usuario tiene un perfil de apoderado
        apoderado = request.user.apoderado
    except Apoderado.DoesNotExist:
        return redirect('home')  # Redirige si el usuario no es apoderado

    # Obtener los alumnos vinculados al apoderado
    alumnos_vinculados = Alumno.objects.filter(apoderado=apoderado)

    # Filtrar las rutas de los alumnos vinculados (solo las rutas asignadas)
    rutas = Ruta.objects.filter(alumnos__in=alumnos_vinculados).distinct()

    # Si un alumno no tiene ruta asignada, no aparecerá en la lista de rutas
    # Se puede hacer una consulta para comprobar si la ruta es None en los alumnos
    alumnos_sin_ruta = alumnos_vinculados.filter(ruta__isnull=True)

    return render(request, 'apoderado/home_apoderado.html', {
        'rutas': rutas,
        'alumnos': alumnos_vinculados,
        'alumnos_sin_ruta': alumnos_sin_ruta,
    })


@login_required
def ver_rutas_asignadas(request):
    # Asegúrate de que el usuario tiene perfil de apoderado
    try:
        apoderado = request.user.apoderado
    except Apoderado.DoesNotExist:
        return redirect('home')

    # Obtén los alumnos del apoderado actual
    alumnos = Alumno.objects.filter(apoderado=apoderado)

# Asegúrate de que `alumnos` es una lista válida de alumnos con un `id`
    alumnos_apoderado = Alumno.objects.filter(apoderado=request.user.apoderado)

    # Obtén las rutas asociadas a estos alumnos
    rutas_asignadas = []
    for alumno in alumnos:
        rutas = Ruta.objects.filter(alumnos=alumno)  # Filtrar rutas donde está asignado el alumno
        rutas_asignadas.append({
            'alumno': alumno,
            'rutas': rutas
        })

    return render(request, 'apoderado/ver_rutas_asignadas.html', {
        'rutas_asignadas': rutas_asignadas,
        'ws_url': 'ws://localhost:8000/ws/seguimiento/'  # Asegúrate de que esta URL sea correcta para producción

    })


@login_required
def ver_ruta_completa_apoderado(request, alumno_id):
    try:
        apoderado = request.user.apoderado  # Verifica si el usuario tiene perfil de apoderado
    except Apoderado.DoesNotExist:
        return redirect('home')  # Redirige si no es apoderado

    # Obtiene al alumno
    alumno = get_object_or_404(Alumno, id=alumno_id, apoderado=apoderado)

    # Obtiene las rutas del alumno
    rutas = Ruta.objects.filter(alumnos=alumno)  # Filtra las rutas donde está asignado el alumno

    if not rutas.exists():
        return redirect('home')  # Si no hay rutas asignadas, redirige

    # Puedes agregar más detalles aquí si es necesario
    ruta = rutas.first()  # Solo tomar la primera ruta, si hay más de una

    # Obtiene las direcciones de los alumnos en la ruta
    direcciones = [alumno.direccion for alumno in ruta.alumnos.all()]

    return render(request, 'apoderado/ver_ruta_completa_apoderado.html', {
        'ruta': ruta,
        'alumno': alumno,
        'direcciones': direcciones,
        'vehiculo': ruta.vehiculo,  # Incluye el vehículo asignado a la ruta
    })

@login_required
def iniciar_viaje(request, ruta_id):
    try:
        conductor = request.user.conductor
    except Conductor.DoesNotExist:
        return redirect('home')

    # Recuperar todas las rutas asociadas al conductor
    rutas = Ruta.objects.filter(conductor=conductor)

    # Si el método es GET, obtenemos la ruta por el id de la URL
    ruta = get_object_or_404(Ruta, id=ruta_id, conductor=conductor)


 # Lista de direcciones de los alumnos
    direcciones_alumnos = [alumno.direccion for alumno in ruta.alumnos.all()]

    if request.method == 'POST':
        # Obtener la ruta seleccionada desde el formulario
        ruta_id = request.POST.get('ruta')
        ruta = get_object_or_404(Ruta, id=ruta_id, conductor=conductor)
          # Recopilar las direcciones de los alumnos asociados a esta ruta
        direcciones_alumnos = [alumno.direccion for alumno in ruta.alumnos.all()]
        vehiculo = Vehiculo.objects.get(ruta=ruta)

        # Datos de la ruta, conductor, vehículo y alumnos
        vehiculo = ruta.vehiculo
        apoderado = ruta.apoderados.first()  # Puede haber más de un apoderado, toma el primero o adapta según sea necesario
        alumnos = ruta.alumnos.all()

        # Captura la hora actual y ajusta la hora de inicio
        hora_inicio = timezone.now()
        hora_ajustada = hora_inicio + timedelta(hours=1)  # Añadir una hora

        # Crear el viaje
        viaje = Viaje.objects.create(
            conductor=conductor,
            apoderado=apoderado,
            vehiculo=vehiculo,
            ruta=ruta,
            direccion=ruta.destino,  # Asume que la dirección es el destino de la ruta
            fecha_salida=hora_ajustada  # Hora ajustada de inicio
        )

        # Relacionar los alumnos con el viaje
        viaje.alumnos.set(alumnos)

              # No redirigir a otra vista, solo mostrar el mapa con las direcciones
        return render(request, 'conductor/iniciar_viaje.html', {
            'rutas': rutas,
            'ruta': ruta,
            'direcciones_alumnos': direcciones_alumnos,  # Pasamos las direcciones de los alumnos al template
            'viaje_iniciado': True,  # Indicador de que el viaje ha sido iniciado
        })

    # Si el método no es POST, solo renderiza la página de inicio de viaje
    return render(request, 'conductor/iniciar_viaje.html', {
        'rutas': rutas,
        'ruta': ruta,
        'direcciones_alumnos': direcciones_alumnos,  # Pasamos las direcciones de los alumnos al template
    })






@login_required
def ver_historial_viajes(request, ruta_id):
    # Verifica si el usuario tiene un perfil de conductor
    try:
        conductor = request.user.conductor
    except Conductor.DoesNotExist:
        return redirect('home')

    # Obtiene todos los viajes relacionados con el conductor autenticado
    viajes = Viaje.objects.filter(conductor=conductor).select_related('ruta', 'vehiculo').order_by('-fecha_salida')


       # Filtrado por fecha si se pasa un parámetro de fecha en la solicitud
    fecha_filtro = request.GET.get('fecha')  # El usuario puede enviar una fecha en formato 'YYYY-MM-DD'
    if fecha_filtro:
        try:
            fecha = datetime.strptime(fecha_filtro, '%Y-%m-%d')
            viajes = viajes.filter(fecha_salida__date=fecha)
        except ValueError:
            pass  # Si la fec
        
    # Construir la información de las rutas, alumnos y vehículos
    historial = []
    for viaje in viajes:
        ruta = viaje.ruta
        if ruta:
            alumnos = ruta.alumnos.all()
            historial.append({
                'fecha_salida': viaje.fecha_salida,
                'estado_viaje': viaje.estado_viaje,
                'direccion': viaje.direccion,
                'ruta_nombre': ruta.nombre,
                'vehiculo': ruta.vehiculo,
                'alumnos': alumnos,
                'direcciones': [alumno.direccion for alumno in alumnos]  # Lista de direcciones de los alumnos
            })

    return render(request, 'conductor/ver_historial_viajes.html', {'historial': historial})