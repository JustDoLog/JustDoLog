from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


def profile_image_path(instance, filename):
    """프로필 이미지 업로드 경로 생성"""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"user/profiles/images/{filename}"


class CustomUser(AbstractUser):
    # AbstractUser
    # username = models.CharField(max_length=150, unique=True)
    # first_name = models.CharField(max_length=150, blank=True)
    # last_name = models.CharField(max_length=150, blank=True)
    # email = models.EmailField(blank=True)
    # is_staff = models.BooleanField(default=False)
    # is_active = models.BooleanField(default=True)
    # date_joined = models.DateTimeField(default=timezone.now)

    profile_image = models.ImageField(
        upload_to=profile_image_path,
        null=True,
        blank=True,
        verbose_name="프로필 이미지",
    )
    nickname = models.CharField(max_length=100, blank=True)
    bio = models.CharField(max_length=255, blank=True)
    github = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    homepage = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자들"

    def __str__(self):
        return self.username
