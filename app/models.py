from datetime import timezone
from pyexpat.errors import messages
from django.db import models
from django.contrib.auth import get_user_model

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from proyectoweb import settings
# Gestor de usuario personalizado
class CustomUserManager(BaseUserManager):
    def create_user(self, rut, email, nombre, apellido, password=None, **extra_fields):
        if not rut:
            raise ValueError('El usuario debe tener un RUT')
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico')
        if not nombre:
            raise ValueError('El usuario debe tener un nombre')
        if not apellido:
            raise ValueError('El usuario debe tener un apellido')

        email = self.normalize_email(email)
        user = self.model(rut=rut, email=email, nombre=nombre, apellido=apellido, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, rut, email, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(rut, email, nombre, apellido, password, **extra_fields)

# Modelo de usuario personalizado
class CustomUser(AbstractBaseUser):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=30, null=False, default='Desconocido')  # Añade un valor por defecto
    apellido = models.CharField(max_length=30, null=False, default='Desconocido')  # Añade un valor por defecto
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'rut'
    REQUIRED_FIELDS = ['email', 'nombre', 'apellido']
    def __str__(self):
        return f'{self.nombre} {self.apellido} ({self.rut})'

# Modelo Apoderado
class Apoderado(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    relacion_alumno = models.CharField(max_length=50)
    conductores = models.ManyToManyField('Conductor', related_name='apoderado_conductores')  # Cambiado el related_name
    nombre = models.CharField(max_length=100, blank=True, null=True)  
    apellido = models.CharField(max_length=100, null=True)
    def __str__(self):
        return f"{self.user.rut} - Apoderado"

# Modelo Conductor
class Conductor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100, blank=True, null=True)  
    apellido = models.CharField(max_length=100, null=True)
    disponible = models.BooleanField(default=True)  # Eliminar esta línea

    licencia_conduccion = models.CharField(max_length=20)
    licencia = models.FileField(upload_to='licencias/', blank=True, null=True)
    certificado = models.FileField(upload_to='certificados/', blank=True, null=True)
    apoderados = models.ManyToManyField('Apoderado', related_name='conductor_apoderados')  # Cambiado el related_name
    documentos_personales_subidos = models.BooleanField(default=False)
    datos_vehiculo_subidos = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.rut} - Conductor"
    
class Vehiculo(models.Model):
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE, related_name='vehiculos')
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    patente = models.CharField(max_length=10)
    revision_tecnica = models.FileField(upload_to='documentos_vehiculo/')
    seguro_obligatorio = models.FileField(upload_to='documentos_vehiculo/')
    lat = models.FloatField()
    lng = models.FloatField()
    def __str__(self):
        return f"{self.marca} {self.modelo} - Patente: {self.patente}"

class Colegio(models.Model):
    nombre_rbd = models.CharField(max_length=255)
    nombre_region = models.CharField(max_length=255)
    nombre_comuna = models.CharField(max_length=255)
    nombre_deprov = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()

    def __str__(self):
        return self.nombre_rbd
    
    # Modelo Alumno
class Alumno(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='alumnos')
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE, related_name='alumnos')
    rutas = models.ManyToManyField('Ruta', related_name='alumnos_rutas', blank=True)  # Asegúrate de que esto esté aquí
    direccion = models.CharField(max_length=255, null=True, blank=True)  # Nuevo campo para la dirección
    conductor = models.ForeignKey(Conductor, null=True, blank=True, on_delete=models.SET_NULL, related_name='alumnos')
    latitud = models.FloatField(null=True, blank=True)  # Permitir nulos si es necesario
    longitud = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.nombre
    




class Ruta(models.Model):
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)  # Identificación de la ruta
    apoderados = models.ManyToManyField(Apoderado)  # Relación de muchos a muchos con Apoderado
    destino = models.CharField(max_length=255)  # Destino final de la ruta
    puntos_intermedios = models.JSONField(null=True, blank=True)  # Puntos por donde debe pasar
    hora_inicio = models.TimeField(null=True)  # Hora estimada de inicio de la ruta (opcional ahora)
    hora_fin = models.TimeField(null=True, blank=True)  # Hora estimada de fin de la ruta
    paradas = models.JSONField(default=list)  # Almacena las coordenadas de las paradas en formato JSON
    dias = models.JSONField(default=list)  # Almacena una lista de días: ["lunes", "martes", "miércoles", ...]

    estado = models.CharField(max_length=10, choices=[
        ('activa', 'Activa'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ], default='activa')
    capacidad_maxima = models.IntegerField(default=10)  # Capacidad del vehículo
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)  # Vehículo asignado
    frecuencia = models.CharField(max_length=50, choices=[
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual')
    ], default='diaria')  # Frecuencia de la ruta
    alumnos = models.ManyToManyField(Alumno, related_name="rutas_alumnos")  # Alumnos asignados a la ruta
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.conductor.nombre} {self.conductor.apellido}"



class Viaje(models.Model):
    # Campos del viaje
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE)  # Relación con el modelo Conductor
    apoderado = models.ForeignKey('Apoderado', on_delete=models.CASCADE, null=True, blank=True)  # Permitir nulos
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE)  # Relación con el modelo Vehículo
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    alumnos = models.ManyToManyField(Alumno, related_name='viajes')  # Relación con alumnos

    # Otros campos del viaje
    fecha_salida = models.DateTimeField(default=timezone.now)  # Fecha y hora de salida, con valor por defecto
    fecha_llegada = models.DateTimeField(null=True, blank=True)  # Fecha y hora de llegada, puede ser nulo
    direccion = models.CharField(max_length=255)  # Campo para la dirección en lugar de ubicación
    estado_viaje = models.CharField(max_length=50, choices=[
        ('en_progreso', 'En progreso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ], default='en_progreso')  # Estado del viaje

    # Otros campos según sea necesario

    def __str__(self):
        return f"Viaje {self.id} - {self.estado_viaje}"

    class Meta:
        verbose_name = 'Viaje'
        verbose_name_plural = 'Viajes'





###########

class SolicitudVinculacion(models.Model):
    apoderado = models.ForeignKey('Apoderado', on_delete=models.CASCADE)
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE)
    alumnos = models.ManyToManyField('Alumno')  # Relación con los alumnos

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    def __str__(self):
        return f"Solicitud de {self.apoderado} para {self.conductor} - Estado: {self.estado}"

    class Meta:
        verbose_name = "Solicitud de Vinculación"
        verbose_name_plural = "Solicitudes de Vinculación"
    


class SubirDumentoImagen(models.Model):
    documento = models.FileField(upload_to='documents/')
    imagen = models.ImageField(upload_to='images/')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE, related_name='documentos', null=True, blank=True)

    class Meta:
        db_table = "¨files"
        ordering = ['-created_at']



class DocumentosPersonales(models.Model):
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE, related_name='documentos_personales')
    licencia = models.FileField(upload_to='documentos_personales/licencia/', blank=True, null=True)
    certificado = models.FileField(upload_to='documentos_personales/certificado/', blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Documentos de {self.conductor.nombre}"
class DocumentosVehiculo(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='documentos_vehiculo')
    tipo_documento = models.CharField(max_length=20, choices=[('revision', 'Revisión Técnica'), ('seguro', 'Seguro')])
    archivo = models.FileField(upload_to='documentos_vehiculo/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_documento} del vehículo {self.vehiculo.marca} {self.vehiculo.modelo}"


# models.py
class Solicitud(models.Model):
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE)
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=[('pendiente', 'Pendiente'), ('aceptada', 'Aceptada'), ('rechazada', 'Rechazada')])
    fecha_creacion = models.DateTimeField(auto_now_add=True)



class Conversacion(models.Model):
    participante_1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='conversaciones_participante_1', on_delete=models.CASCADE)
    participante_2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='conversaciones_participante_2', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participante_1} - {self.participante_2}"
# Modelo Mensaje para la comunicación entre conductor y apoderado
class Mensaje(models.Model):
    conversacion = models.ForeignKey(Conversacion, related_name='mensajes', on_delete=models.CASCADE, default=1)  # Cambia '1' por el ID de una conversación válida

    remitente = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='mensajes_recibidos')
    contenido = models.TextField()
    fecha_enviado = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    def __str__(self):
        return f"Mensaje de {self.remitente} a {self.destinatario} - {self.contenido[:30]}"
    


