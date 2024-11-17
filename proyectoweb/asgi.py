import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from app.consumers import ViajeConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoweb.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("iniciar_viaje/", ViajeConsumer.as_asgi()),
        ])
    ),
})
