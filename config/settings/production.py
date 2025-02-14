from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", ".justdolog.com").split(",")

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"

# Media files - MinIO Storage
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = os.getenv("MINIO_ROOT_USER")
AWS_SECRET_ACCESS_KEY = os.getenv("MINIO_ROOT_PASSWORD")
AWS_STORAGE_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "justdolog-media")
AWS_S3_ENDPOINT_URL = os.getenv("MINIO_URL", "http://minio:9000")
AWS_S3_CUSTOM_DOMAIN = (
    f"minio.{ALLOWED_HOSTS[0]}/justdolog-media" if ALLOWED_HOSTS else None
)

AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

# 추가 MinIO 설정
AWS_S3_VERIFY = True  # 프로덕션 환경에서는 SSL 검증 활성화
AWS_S3_USE_SSL = True  # 프로덕션 환경에서는 HTTPS 사용
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_REGION_NAME = "us-east-1"

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

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
