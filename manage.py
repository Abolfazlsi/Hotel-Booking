import os
import sys
from decouple import config


def main():
    """Run administrative tasks."""
    django_env = config("DJANGO_ENV", default="development")

    if django_env == "production":
        settings_module = "core.settings.production"
    else:
        settings_module = "core.settings.development"

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
