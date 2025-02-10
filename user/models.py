from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import uuid
from PIL import Image
import io


def validate_image_size(file):
    """이미지 파일 크기 검증"""
    # 5MB 제한
    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError('이미지 크기는 5MB를 초과할 수 없습니다.')


def validate_image(file):
    """이미지 파일 유효성 검사"""
    if file:
        try:
            # 파일 크기 검증
            validate_image_size(file)
            # 파일 포인터를 처음으로 되돌림
            file.seek(0)
            img = Image.open(io.BytesIO(file.read()))
            img.verify()  # 이미지 파일 검증
            file.seek(0)  # 파일 포인터를 다시 처음으로
            return file
        except Exception:
            raise ValidationError("유효한 이미지 파일이 아닙니다.")


def validate_url(value):
    """URL 유효성 검사"""
    validator = URLValidator(
        schemes=['http', 'https'],
        message='올바른 URL을 입력해주세요. (예: https://example.com)'
    )
    validator(value)


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
        validators=[validate_image]
    )
    github_url = models.URLField(
        max_length=200,
        blank=True,
        validators=[validate_url]
    )
    twitter_url = models.URLField(
        max_length=200,
        blank=True,
        validators=[validate_url]
    )
    facebook_url = models.URLField(
        max_length=200,
        blank=True,
        validators=[validate_url]
    )
    homepage_url = models.URLField(
        max_length=200,
        blank=True,
        validators=[validate_url]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자들"

    def __str__(self):
        return self.username
    
    @property
    def get_profile_image(self):
        """프로필 이미지 URL 반환"""
        if self.profile_image:
            return self.profile_image.url
        return None

    def save(self, *args, **kwargs):
        if self.profile_image:
            validate_image(self.profile_image)
        super().save(*args, **kwargs)


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

    def clean(self):
        if self.follower == self.following:
            raise ValidationError("자기 자신을 팔로우할 수 없습니다.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"    
