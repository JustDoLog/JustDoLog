from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", ".justdolog.com").split(",")

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"

# Media files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Email Backend for Production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# Email settings will be configured later
