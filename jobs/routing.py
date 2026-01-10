from django.urls import re_path
from . import consumers

# websocket_urlpatterns = [
#     # text chat group
#     re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),

#     # WebRTC signaling for call
#     re_path(r'ws/signaling/(?P<room_name>\w+)/$', consumers.SignalingConsumer.as_asgi()),
# ]

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]