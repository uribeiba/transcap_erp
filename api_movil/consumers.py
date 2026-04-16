import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import UbicacionChofer
from taller.models import Conductor

class UbicacionesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'ubicaciones_choferes'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        accion = data.get('accion')
        
        if accion == 'nueva_ubicacion':
            await self.guardar_ubicacion(data)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'ubicacion_actualizada',
                    'data': data
                }
            )
    
    @database_sync_to_async
    def guardar_ubicacion(self, data):
        try:
            conductor = Conductor.objects.get(id=data.get('conductor_id'))
            UbicacionChofer.objects.create(
                conductor=conductor,
                latitud=data.get('latitud'),
                longitud=data.get('longitud'),
                velocidad=data.get('velocidad', 0),
            )
        except Conductor.DoesNotExist:
            pass

    async def ubicacion_actualizada(self, event):
        await self.send(text_data=json.dumps(event['data']))