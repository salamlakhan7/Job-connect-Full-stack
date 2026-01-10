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

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

# 🔑 THIS MUST COME BEFORE importing routing / consumers
django.setup()

import jobs.routing  # <-- import AFTER django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            jobs.routing.websocket_urlpatterns
        )
    ),
})
