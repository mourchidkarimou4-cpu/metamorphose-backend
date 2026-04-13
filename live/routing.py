from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/live/(?P<room_id>[^/]+)/$', consumers.LiveConsumer.as_asgi()),
]
