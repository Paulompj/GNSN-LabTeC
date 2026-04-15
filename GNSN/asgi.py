"""
ASGI config for GNSN project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from dj_static import Cling, MediaCling
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GNSN.settings')

#application = Cling(MediaCling(get_asgi_application()))
application = get_asgi_application()
