from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", ".justdolog.com").split(",")

# Database
# Production database settings will be configured later

# Email Backend for Production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# Email settings will be configured later
