"""ASGI config for the example project.

It is not required for the SDK examples (the callback views are sync), so this
file exists only to make `ASGI_APPLICATION`-based tooling happy.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mpesa_proj.settings")

application = get_asgi_application()