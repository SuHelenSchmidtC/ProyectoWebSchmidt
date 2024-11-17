# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Mensaje, Apoderado, Conductor
from django.contrib.auth import get_user_model
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f"chat_{self.chat_id}"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        remitente_id = data['remitente_id']
        destinatario_id = data['destinatario_id']

        remitente = get_user_model().objects.get(id=remitente_id)
        destinatario = get_user_model().objects.get(id=destinatario_id)
        
        # Guarda el mensaje en la base de datos
        mensaje = Mensaje.objects.create(
            remitente=remitente,
            destinatario=destinatario,
            contenido=message,
        )

        # Enviar el mensaje a todos en el grupo
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'remitente': remitente.nombre,
                'fecha': str(mensaje.fecha_enviado)
            }
        )

    async def chat_message(self, event):
        message = event['message']
        remitente = event['remitente']
        fecha = event['fecha']

        await self.send(text_data=json.dumps({
            'message': message,
            'remitente': remitente,
            'fecha': fecha
        }))



class SeguimientoVehiculo(AsyncWebsocketConsumer):
    async def connect(self):
        # Conectar al grupo basado en el vehículo
        self.vehicle_group_name = f"vehiculo_{self.scope['url_route']['kwargs']['vehiculo_id']}"
        await self.channel_layer.group_add(self.vehicle_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Desconectar del grupo
        await self.channel_layer.group_discard(self.vehicle_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Broadcast de la posición a todos en el grupo
        await self.channel_layer.group_send(
            self.vehicle_group_name,
            {
                'type': 'update_position',
                'lat': data['lat'],
                'lng': data['lng'],
            }
        )

    async def update_position(self, event):
        # Enviar la posición actualizada a los clientes
        await self.send(text_data=json.dumps({
            'lat': event['lat'],
            'lng': event['lng'],
        }))





class ViajeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'viaje_group'

        # Unirse a un grupo
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo cuando se desconecta
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recibir un mensaje desde WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']

        # Aquí puedes guardar en la base de datos el registro de iniciar viaje
        if action == 'iniciar_viaje':
            # Lógica para guardar en la base de datos, por ejemplo:
            # Viaje.objects.create(conductor=conductor, fecha=datetime.now())
            # o cualquier otra acción relacionada con el viaje

            # Enviar un mensaje al grupo
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'viaje_iniciado',
                    'message': 'Viaje iniciado exitosamente'
                }
            )

    # Recibir mensaje desde el grupo
    async def viaje_iniciado(self, event):
        message = event['message']

        # Enviar mensaje a WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))