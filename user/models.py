from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from urllib.request import urlretrieve
from django.core.files import File
import tempfile
import os


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
    profile_image_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="프로필 이미지 URL"
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
    
    def follow(self, user):
        if user != self:
            Follow.objects.get_or_create(follower=self, following=user)

    def unfollow(self, user):
        Follow.objects.filter(follower=self, following=user).delete()

    def is_following(self, user):
        return self.following.filter(following=user).exists()

    def get_followers_count(self):
        return self.followers.count()

    def get_following_count(self):
        return self.following.count()    

    @property
    def get_profile_image(self):
        """프로필 이미지 URL 반환 (로컬 이미지 또는 소셜 이미지)"""
        if self.profile_image:
            return self.profile_image.url
        elif self.profile_image_url:
            return self.profile_image_url
        return None


class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "팔로잉"
        verbose_name_plural = "팔로잉"
        # 동일한 팔로잉 관계가 중복되지 않도록
        unique_together = ('follower', 'following')
        # 자기 자신을 팔로우할 수 없도록 제약조건 추가 가능
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F('following')),
                name='no_self_following'
            )
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"    


@receiver(post_save, sender=SocialAccount)
def save_profile_image_url(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        if not user.profile_image and not user.profile_image_url:
            if instance.provider == 'google':
                picture_url = instance.extra_data.get('picture')
            elif instance.provider == 'github':
                picture_url = instance.extra_data.get('avatar_url')
            
            if picture_url:
                user.profile_image_url = picture_url
                user.save()    
