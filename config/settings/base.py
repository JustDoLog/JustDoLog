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
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "tinymce",
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
ACCOUNT_AUTHENTICATION_METHOD = "email"  # 로그인 인증 방식을 이메일로 설정
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
    },
    "github": {
        "SCOPE": [
            "user",
            "email",
        ],
    },
}

# tinymce
TINYMCE_DEFAULT_CONFIG = {
    "height": "500px",
    "width": "100%",
    "menubar": "file edit view insert format tools table help",
    "plugins": (
        "advlist autolink lists link image imagetools charmap print preview anchor searchreplace "
        "visualblocks code fullscreen insertdatetime media table paste code help wordcount spellchecker "
        "file quickbars emoticons"
    ),
    "toolbar": (
        "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | "
        "alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | "
        "forecolor backcolor casechange permanentpen formatpainter removeformat | pagebreak | "
        "charmap emoticons | fullscreen  preview save print | insertfile image media pageembed template "
        "link anchor codesample | a11ycheck ltr rtl | showcomments addcomment code"
    ),
    "custom_undo_redo_levels": 10,
    "language": "ko_KR",
    # 이미지 업로드 관련 설정
    "images_upload_url": "upload_image",
    "automatic_uploads": True,
    "images_reuse_filename": True,
    "file_picker_types": "image",
    "images_file_types": "jpg,svg,webp,png,gif",
    "image_advtab": True,
    "image_uploadtab": True,
    "file_picker_callback": """
        function(callback, value, meta) {
            var input = document.createElement('input');
            input.setAttribute('type', 'file');
            input.setAttribute('accept', 'image/*');
            input.onchange = function() {
                var file = this.files[0];
                var reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = function() {
                    var id = 'blobid' + (new Date()).getTime();
                    var blobCache = tinymce.activeEditor.editorUpload.blobCache;
                    var base64 = reader.result.split(',')[1];
                    var blobInfo = blobCache.create(id, file, base64);
                    blobCache.add(blobInfo);
                    callback(blobInfo.blobUri(), { title: file.name });
                };
            };
            input.click();
        }
    """,
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
