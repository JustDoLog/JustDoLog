import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-g14e28^xlic&i2htb8)sbcj+_hna_&k5pci8=0i5n3pqc4g!f2",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "tinymce",
    "taggit",
    "user",
    "blog",
    "discovery",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Custom User Model
AUTH_USER_MODEL = "user.CustomUser"


# allauth
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by email
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True  # 계정 이메일이 필요한가?
ACCOUNT_USERNAME_REQUIRED = True  # 계정 이름이 필요한가?
ACCOUNT_EMAIL_VERIFICATION = "none"  # 이메일 검증 과정이 필요한가?
LOGIN_REDIRECT_URL = "/"  # 로그인 후 리다이렉트 될 URL
LOGOUT_REDIRECT_URL = "/"  # 로그아웃 후 리다이렉트 될 URL
SOCIALACCOUNT_LOGIN_ON_GET = True  # 소셜 로그인 중간 페이지 건너뛰기
ACCOUNT_LOGIN_METHODS = {'email'}  # 로그인 인증 방식을 이메일로 설정
ACCOUNT_UNIQUE_EMAIL = True  # 이메일 중복 방지
SOCIALACCOUNT_AUTO_SIGNUP = True  # 소셜 계정으로 로그인 시 자동 회원가입

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
        "SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
    },
    "github": {
        "SCOPE": [
            "user",
            "email",
        ],
        "CLIENT_ID": os.getenv("GITHUB_CLIENT_ID"),
        "SECRET": os.getenv("GITHUB_CLIENT_SECRET"),
    },
}

# tinymce
TINYMCE_DEFAULT_CONFIG = {
    "height": "500px",
    "width": "100%",
    "menubar": "file edit view insert format tools table help",
    "plugins": (
        "advlist autolink lists link image charmap preview anchor searchreplace "
        "visualblocks code fullscreen insertdatetime media table code help wordcount "
        "quickbars emoticons"
    ),
    "toolbar": (
        "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | "
        "alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist | "
        "forecolor backcolor casechange permanentpen formatpainter removeformat | pagebreak | "
        "charmap emoticons | fullscreen preview | insertfile image media pageembed template "
        "link anchor codesample | code"
    ),
    "custom_undo_redo_levels": 10,
    "language": "ko_KR",
    # 이미지 업로드 관련 설정
    "images_upload_url": "upload_image",
    "automatic_uploads": True,
    "images_reuse_filename": False,
    "file_picker_types": "image",
    "images_file_types": "jpg,svg,webp,png,gif",
    "image_advtab": True,
    "image_uploadtab": True,
    # URL 관련 설정
    "relative_urls": False,
    "remove_script_host": True,
    "document_base_url": os.getenv("SITE_URL", "http://localhost:8000"),
    "convert_urls": True,
    # 기존 스타일 설정 유지
    "content_style": """
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
        body { 
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #212529;
        }
        h1, h2, h3, h4 { 
            font-weight: 700;
            color: #212529;
            margin: 1.5em 0 0.5em;
        }
        h1 { font-size: 2.5em; }
        h2 { font-size: 2em; }
        h3 { font-size: 1.75em; }
        h4 { font-size: 1.5em; }
        p { margin: 1em 0; }
        blockquote { 
            border-left: 4px solid #e9ecef; 
            margin: 1.5em 0; 
            padding: 0.5em 1em; 
            color: #495057;
            background-color: #f8f9fa;
        }
        code {
            background-color: #f8f9fa;
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-family: monospace;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 1em 0;
        }
    """,
}

# MinIO 공통 설정
MINIO_SETTINGS = {
    "DEFAULT_FILE_STORAGE": "storages.backends.s3boto3.S3Boto3Storage",
    "AWS_ACCESS_KEY_ID": os.getenv("MINIO_ROOT_USER"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("MINIO_ROOT_PASSWORD"),
    "AWS_STORAGE_BUCKET_NAME": os.getenv("MINIO_BUCKET_NAME", "justdolog-media"),
    "AWS_S3_ENDPOINT_URL": os.getenv("MINIO_URL", "http://minio:9000"),
    "AWS_S3_ADDRESSING_STYLE": "path",
    "AWS_S3_SIGNATURE_VERSION": "s3v4",
    "AWS_S3_REGION_NAME": "us-east-1",
    "AWS_QUERYSTRING_AUTH": False,
    "AWS_S3_FILE_OVERWRITE": False,
    "FILE_UPLOAD_MAX_MEMORY_SIZE": 5 * 1024 * 1024,
    "MAX_UPLOAD_SIZE": 5 * 1024 * 1024,
}

# MinIO 설정 적용
globals().update(MINIO_SETTINGS)
