# routing.py
from django.urls import path, re_path
from app.consumers import SeguimientoVehiculo  # Ajusta 'app' si está en otro directorio

websocket_urlpatterns = [
    path('ws/vehiculo/<int:vehiculo_id>/', SeguimientoVehiculo.as_asgi()),
]
