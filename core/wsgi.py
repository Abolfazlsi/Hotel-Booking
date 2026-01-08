import os
from decouple import config
from django.core.wsgi import get_wsgi_application

django_env = config("DJANGO_ENV", default="development")

if django_env == "production":
    settings_module = "core.settings.production"
else:
    settings_module = "core.settings.development"

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()
