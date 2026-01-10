# """
# ASGI config for mysite project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
# """

# import os
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import jobs.routing


# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# django_asgi_app = get_asgi_application()

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             jobs.routing.websocket_urlpatterns
#         )
#     ),
# })


##################option2 #########################
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set the settings module before anything else
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

# 🔑 Initialize Django fully before importing routing
django.setup()

# Import routing AFTER django.setup() to avoid registry errors
import jobs.routing

application = ProtocolTypeRouter({
    # Handles standard HTTP requests
    "http": get_asgi_application(),
    
    # Handles real-time WebSocket connections for your Chat system
    "websocket": AuthMiddlewareStack(
        URLRouter(
            jobs.routing.websocket_urlpatterns
        )
    ),
})
