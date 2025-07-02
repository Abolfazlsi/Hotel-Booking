import os

ENV = os.getenv('DJANGO_ENV', 'development')

if ENV == 'production':
    from .production import *
else:
    from .development import *
