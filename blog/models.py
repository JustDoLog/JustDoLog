from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from user.models import CustomUser
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Blog(models.Model):
    owner = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="blog"
    )

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Post(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="posts"
    )
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="posts")

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True)
    content = HTMLField()
    status = models.CharField(
        max_length=10,
        choices=[("draft", "Draft"), ("published", "Published")],
        default="draft",
    )
    likes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # FTS를 위한 필드
    search_vector = SearchVectorField(null=True)

    # 좋아요한 사용자들
    liked_by = models.ManyToManyField(
        CustomUser, through="PostLike", related_name="liked_posts"
    )

    # 읽은 사용자들
    read_by = models.ManyToManyField(
        CustomUser, through="PostRead", related_name="read_posts"
    )

    class Meta:
        indexes = [GinIndex(fields=["search_vector"], name="post_search_vector_idx")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 새로운 포스트이거나 title이 변경된 경우에만 slug 업데이트
        if (
            not self.pk
            or not self.slug
            or Post.objects.get(pk=self.pk).title != self.title
        ):
            base_slug = slugify(self.title, allow_unicode=True)
            unique_slug = base_slug
            count = 1
            # 현재 객체를 제외한 다른 객체들과 slug 중복 검사
            while Post.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{count}"
                count += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


class PostLike(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-created_at"]


class PostRead(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-updated_at"]
