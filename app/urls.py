from django.http import HttpResponse
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.conf.urls.static import static

from proyectoweb import settings
from .views import (
    BuscarDireccion,
    SolicitudesApoderados,
    Vinculaciones,
    asignar_alumnos,
    buscar_colegios,
    gestion_alumnos,
    gestionar_vehiculos,

    home,
    listar_conductores,
  
    registro_conductor,
    registro_apoderado,
    CustomLoginView,
    home_conductor,
    home_apoderado,
 
    crear_solicitud_vinculacion,
    simulador_recorrido,
    subir_datos_vehiculo,
    subir_documentos,
    ver_alumnos_vinculados,
    ver_conductor_alumno,
    ver_documentos_conductor,
    visualizar_recorrido,

)
from app import views

urlpatterns = [
    path('', home, name='home'),  # Página de inicio
    path('login/', CustomLoginView.as_view(), name='login'),
    path('registro/conductor/', registro_conductor, name='registro_conductor'),
    path('registro/apoderado/', registro_apoderado, name='registro_apoderado'),
    path('home/conductor/', home_conductor, name='home_conductor'),
    path('home/apoderado/', home_apoderado, name='home_apoderado'),
    path('pagina/no_autorizada/', lambda request: HttpResponse("No autorizado"), name='pagina_no_autorizada'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('registro/alumno/', views.crear_alumno, name='crear_alumno'),
    path('buscar/conductor/', views.buscar_conductor, name='buscar_conductor'),  # Asegúrate de que esta línea esté presente
    path('crear/solicitud/<int:conductor_id>/', views.crear_solicitud_vinculacion, name='crear_solicitud_vinculacion'),
    path('vinculaciones/', Vinculaciones.as_view(), name='vinculaciones'),
    path('solicitudes_apoderado/', SolicitudesApoderados.as_view(), name='SolicitudesApoderados'),
    path('ver-conductor-alumno/', ver_conductor_alumno, name='ver_conductor_alumno'),  # Nueva URL
    path('listar_conductores/', listar_conductores, name='listar_conductores'),
    path('gestion_alumnos/', gestion_alumnos, name='gestion_alumnos'),
    path('subir_documentos/', subir_documentos, name='subir_documentos'),
    path('subir_datos_vehiculo/', subir_datos_vehiculo, name='subir_datos_vehiculo'),
    path('conductor/gestionar_documentos/', views.gestionar_documentos, name='gestionar_documentos'),
    path('ver_documentos_conductor/<int:conductor_id>/', ver_documentos_conductor, name='ver_documentos_conductor'),
    path('documentos/conductor/<int:conductor_id>/', views.ver_documentos_conductor, name='ver_documentos_conductor'),
    path('listar_conductores/', listar_conductores, name='listar_conductores'),
    path('chat/<str:chat_id>/', views.chat_view, name='chat_view'),
    path('mensaje/', views.ver_mensajes, name='ver_mensajes'),
    path('mensaje/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('mensaje/<int:conversacion_id>/', views.ver_conversacion, name='ver_conversacion'),
    path('mensaje/enviar/<int:conversacion_id>/', views.enviar_mensaje, name='enviar_mensaje'),
    path('mensaje/cargar_conversacion/<int:conversacion_id>/', views.cargar_conversacion, name='cargar_conversacion'),
    path('elegir-tipo-registro/', views.elegir_tipo_registro, name='elegir_tipo_registro'),
    path('datos-personales/', views.datos_personales, name='datos_personales'),
    path('buscar-colegios/', buscar_colegios, name='buscar_colegios'),
    path('buscar_direccion/', BuscarDireccion.as_view(), name='buscar_direccion'),
    path('quitar_alumno/', views.quitar_alumno, name='quitar_alumno'),

    path('ver_alumnos_vinculados/', ver_alumnos_vinculados, name='ver_alumnos_vinculados'),
    path('gestionar_rutas/', views.gestionar_rutas, name='gestionar_rutas'),
    path('asignar_alumnos/', asignar_alumnos, name='asignar_alumnos'),  # Asegúrate de que esta línea esté presente
    path('visualizar_recorrido/<int:ruta_id>/', visualizar_recorrido, name='visualizar_recorrido'),
    path('elegir-ruta/', views.elegir_ruta, name='elegir_ruta'),
    path('simulador/<int:ruta_id>/', simulador_recorrido, name='simulador_recorrido'),
    path('gestionar_vehiculos/', gestionar_vehiculos, name='gestionar_vehiculos'),

    path('gestionar_vehiculos/<int:vehiculo_id>/', gestionar_vehiculos, name='gestionar_vehiculos_edit'),  # Acepta un ID
    path('ver_rutas_asignadas/', views.ver_rutas_asignadas, name='ver_rutas_asignadas'),
    path('ver_ruta_completa/<int:alumno_id>/', views.ver_ruta_completa_apoderado, name='ver_ruta_completa_apoderado'),
    path('ver_historial_viajes/<int:ruta_id>/', views.ver_historial_viajes, name='ver_historial_viajes'),
    path('iniciar_viaje/<int:ruta_id>/', views.iniciar_viaje, name='iniciar_viaje'),

    # Rutas del apoderado

    # Rutas del conductor


    # Solicitudes de vinculación
    path('crear_solicitud/', crear_solicitud_vinculacion, name='crear_solicitud'),


    # URL para gestionar solicitudes de un conductor

 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
