import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class LiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id   = self.scope['url_route']['kwargs']['room_id']
        self.room_group = f'live_{self.room_id}'
        self.user_id    = None
        self.role       = 'participant'  # 'host' | 'participant' | 'spectator'

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        logger.info(f"[LIVE] Connexion salle {self.room_id}")

    async def disconnect(self, close_code):
        # Notifier les autres participants du départ
        if self.user_id:
            await self.channel_layer.group_send(self.room_group, {
                'type': 'peer_left',
                'peer_id': self.user_id,
            })
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')

            # ── JOIN ──────────────────────────────────────────────────
            if msg_type == 'join':
                self.user_id = data.get('peer_id')
                self.role    = data.get('role', 'participant')
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'peer_joined',
                    'peer_id': self.user_id,
                    'role':    self.role,
                    'name':    data.get('name', 'Anonyme'),
                })

            # ── OFFER WebRTC ──────────────────────────────────────────
            elif msg_type == 'offer':
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'webrtc_offer',
                    'offer':   data.get('offer'),
                    'from_id': self.user_id,
                    'to_id':   data.get('to_id'),
                })

            # ── ANSWER WebRTC ─────────────────────────────────────────
            elif msg_type == 'answer':
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'webrtc_answer',
                    'answer':  data.get('answer'),
                    'from_id': self.user_id,
                    'to_id':   data.get('to_id'),
                })

            # ── ICE CANDIDATE ─────────────────────────────────────────
            elif msg_type == 'ice_candidate':
                await self.channel_layer.group_send(self.room_group, {
                    'type':      'ice_candidate',
                    'candidate': data.get('candidate'),
                    'from_id':   self.user_id,
                    'to_id':     data.get('to_id'),
                })

            # ── CHAT ──────────────────────────────────────────────────
            elif msg_type == 'chat':
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'chat_message',
                    'message': data.get('message'),
                    'from_id': self.user_id,
                    'name':    data.get('name', 'Anonyme'),
                })

            # ── RÉACTION ─────────────────────────────────────────────
            elif msg_type == 'reaction':
                await self.channel_layer.group_send(self.room_group, {
                    'type':     'reaction',
                    'emoji':    data.get('emoji'),
                    'from_id':  self.user_id,
                    'name':     data.get('name', 'Anonyme'),
                })

            # ── MUTE/UNMUTE ───────────────────────────────────────────
            elif msg_type == 'media_state':
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'media_state',
                    'peer_id': self.user_id,
                    'audio':   data.get('audio', True),
                    'video':   data.get('video', True),
                })

            # ── PARTAGE ÉCRAN ─────────────────────────────────────────
            elif msg_type == 'screen_share':
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'screen_share',
                    'peer_id': self.user_id,
                    'active':  data.get('active', False),
                })

            # ── SONDAGE ──────────────────────────────────────────────
            elif msg_type == 'poll':
                await self.channel_layer.group_send(self.room_group, {
                    'type':      'poll',
                    'question':  data.get('question'),
                    'options':   data.get('options', []),
                    'from_id':   self.user_id,
                })

            # ── VOTE SONDAGE ──────────────────────────────────────────
            elif msg_type == 'poll_vote':
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'poll_vote',
                    'option':  data.get('option'),
                    'from_id': self.user_id,
                })

            # ── LEVER LA MAIN ─────────────────────────────────────────
            elif msg_type == 'raise_hand':
                await self.channel_layer.group_send(self.room_group, {
                    'type':    'raise_hand',
                    'peer_id': self.user_id,
                    'name':    data.get('name', 'Anonyme'),
                    'raised':  data.get('raised', True),
                })

        except Exception as e:
            logger.error(f"[LIVE] Erreur receive: {e}")

    # ── Handlers envoi aux clients ──────────────────────────────────────
    async def peer_joined(self, event):
        await self.send(text_data=json.dumps({'type': 'peer_joined', **event}))

    async def peer_left(self, event):
        await self.send(text_data=json.dumps({'type': 'peer_left', **event}))

    async def webrtc_offer(self, event):
        if event.get('to_id') == self.user_id or event.get('to_id') is None:
            await self.send(text_data=json.dumps({'type': 'offer', **event}))

    async def webrtc_answer(self, event):
        if event.get('to_id') == self.user_id or event.get('to_id') is None:
            await self.send(text_data=json.dumps({'type': 'answer', **event}))

    async def ice_candidate(self, event):
        if event.get('to_id') == self.user_id or event.get('to_id') is None:
            await self.send(text_data=json.dumps({'type': 'ice_candidate', **event}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'chat', **event}))

    async def reaction(self, event):
        await self.send(text_data=json.dumps({'type': 'reaction', **event}))

    async def media_state(self, event):
        await self.send(text_data=json.dumps({'type': 'media_state', **event}))

    async def screen_share(self, event):
        await self.send(text_data=json.dumps({'type': 'screen_share', **event}))

    async def poll(self, event):
        await self.send(text_data=json.dumps({'type': 'poll', **event}))

    async def poll_vote(self, event):
        await self.send(text_data=json.dumps({'type': 'poll_vote', **event}))

    async def raise_hand(self, event):
        await self.send(text_data=json.dumps({'type': 'raise_hand', **event}))
