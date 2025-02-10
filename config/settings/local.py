from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Email Backend for Development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Static files
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files - MinIO Storage
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = os.getenv("MINIO_ROOT_USER")
AWS_SECRET_ACCESS_KEY = os.getenv("MINIO_ROOT_PASSWORD")
AWS_STORAGE_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "justdolog-media")
AWS_S3_ENDPOINT_URL = os.getenv("MINIO_URL", "http://minio:9000")

# MinIO 환경별 설정
AWS_S3_CUSTOM_DOMAIN = "localhost:9000"
AWS_DEFAULT_ACL = "public-read"
AWS_S3_VERIFY = False  # 개발 환경에서는 SSL 검증 비활성화
AWS_S3_USE_SSL = False  # 개발 환경에서는 HTTP 사용

# MinIO 접근 설정
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

# 추가 MinIO 설정
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_REGION_NAME = "us-east-1"

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Redis Cache Settings
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/0"),
    }
}

# Cache timeouts
POST_CACHE_TTL = 60 * 15  # 15 minutes
BLOG_CACHE_TTL = 60 * 30  # 30 minutes
LIKES_CACHE_TTL = 60 * 5  # 5 minutes
VIEWS_CACHE_TTL = 60 * 5  # 5 minutes

# Cache key prefix
CACHE_KEY_PREFIX = "jdl"

# Session
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
