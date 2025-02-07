from django.contrib.auth.models import AbstractUser
from django.db import models


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
        upload_to="profile_images/", null=True, blank=True
    )
    nickname = models.CharField(max_length=100, blank=True)
    bio = models.CharField(max_length=255, blank=True)
    github = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    homepage = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
