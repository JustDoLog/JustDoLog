from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from user.models import CustomUser
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from bs4 import BeautifulSoup
from taggit.managers import TaggableManager
from django.db.models import Count, Q, Prefetch, F
from taggit.models import Tag
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings


class PostManager(models.Manager):
    def get_queryset(self):
        """기본 queryset에 자주 사용되는 관계들을 미리 로드"""
        return super().get_queryset().select_related('author', 'blog').prefetch_related('tags')
    
    def published(self):
        """공개된 포스트만 반환"""
        return self.get_queryset().filter(status="published")
    
    def trending(self, days=7):
        """최근 n일 동안의 트렌딩 포스트"""
        start_date = timezone.now() - timedelta(days=days)
        return self.published().filter(
            created_at__gte=start_date
        ).order_by('-likes', '-created_at')
    
    def by_tag(self, tag_name):
        """특정 태그의 공개된 포스트"""
        return self.published().filter(tags__name=tag_name)
    
    def by_user(self, user):
        """특정 사용자의 공개된 포스트"""
        return self.published().filter(author=user)
    
    def search(self, query):
        """포스트 검색"""
        return self.published().filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )


class BlogManager(models.Manager):
    def get_queryset(self):
        """기본 queryset에 자주 사용되는 관계들을 미리 로드"""
        return super().get_queryset().select_related('owner')
    
    def with_post_counts(self):
        """게시글 수를 포함한 블로그 queryset 반환"""
        return self.get_queryset().annotate(
            total_posts=Count('posts', filter=Q(posts__status='published')),
            total_likes=Count('posts__postlike'),
            total_views=Count('posts__views')
        )
    
    def popular(self, days=30):
        """인기 블로거의 블로그 목록"""
        period_start = timezone.now() - timedelta(days=days)
        return self.get_queryset().annotate(
            followers_count=Count('owner__followers'),
            recent_posts_count=Count(
                'posts',
                filter=Q(posts__updated_at__gte=period_start)
            ),
            recent_likes_count=Count(
                'posts__postlike',
                filter=Q(posts__postlike__created_at__gte=period_start)
            )
        ).filter(posts__isnull=False).distinct().order_by(
            '-followers_count',
            '-recent_posts_count',
            '-recent_likes_count'
        )
    
    def with_tags(self):
        """태그 정보를 포함한 블로그 queryset 반환"""
        return self.get_queryset().prefetch_related(
            Prefetch(
                'posts__tags',
                queryset=Tag.objects.annotate(
                    posts_count=Count('post', filter=Q(post__status='published'))
                ).order_by('-posts_count', 'name')
            )
        )


class Blog(models.Model):
    owner = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="blog"
    )

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BlogManager()

    def __str__(self):
        return self.title

    def get_tags_with_count(self):
        # 해당 블로그의 공개된 게시글에 사용된 태그와 게시글 수를 가져옴
        return Tag.objects.filter(
            post__blog=self,
            post__status='published'
        ).annotate(
            posts_count=Count('post', filter=models.Q(post__status='published'))
        ).order_by('-posts_count', 'name')


class Post(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="posts"
    )
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="posts")

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True)
    content = HTMLField()
    thumbnail = models.URLField(max_length=500, blank=True, null=True)
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

    # 태그 관리자
    tags = TaggableManager(blank=True)

    objects = PostManager()

    class Meta:
        indexes = [GinIndex(fields=["search_vector"], name="post_search_vector_idx")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def _generate_unique_slug(self):
        """고유한 slug를 생성합니다."""
        if (not self.pk or not self.slug or 
            Post.objects.get(pk=self.pk).title != self.title):
            base_slug = slugify(self.title, allow_unicode=True)
            unique_slug = base_slug
            count = 1
            while Post.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{count}"
                count += 1
            return unique_slug
        return self.slug

    def _extract_thumbnail(self):
        """content에서 첫 번째 이미지를 썸네일로 추출합니다."""
        if self.content:
            soup = BeautifulSoup(self.content, 'html.parser')
            img = soup.find('img')
            return img['src'] if img and img.get('src') else None
        return None

    def clean(self):
        """데이터 유효성 검사를 수행합니다."""
        if self.status not in dict(self._meta.get_field('status').choices):
            raise ValueError(f"Invalid status value: {self.status}")
        super().clean()

    def save(self, *args, **kwargs):
        # clean 메서드 호출하여 유효성 검사 수행
        self.clean()
        
        # slug 생성
        self.slug = self._generate_unique_slug()
        
        # 썸네일 추출
        self.thumbnail = self._extract_thumbnail()

        super().save(*args, **kwargs)

    def get_like_url(self):
        """좋아요 토글 URL 반환"""
        return reverse('toggle_like', kwargs={
            'username': self.blog.owner.username,
            'slug': self.slug
        })

    def get_cache_key(self, suffix=''):
        """캐시 키 생성"""
        return f"{settings.CACHE_KEY_PREFIX}:post:{self.id}:{suffix}"

    def get_likes_count(self):
        """좋아요 수 조회 (캐시 적용)"""
        cache_key = self.get_cache_key('likes')
        count = cache.get(cache_key)
        
        if count is None:
            count = self.likes
            cache.set(cache_key, count, settings.LIKES_CACHE_TTL)
        
        return count

    def get_views_count(self):
        """조회수 조회 (캐시 적용)"""
        cache_key = self.get_cache_key('views')
        count = cache.get(cache_key)
        
        if count is None:
            count = self.views
            cache.set(cache_key, count, settings.VIEWS_CACHE_TTL)
        
        return count

    def increment_likes(self):
        """좋아요 수 증가"""
        Post.objects.filter(id=self.id).update(likes=F('likes') + 1)
        self.refresh_from_db()
        return self.likes

    def decrement_likes(self):
        """좋아요 수 감소"""
        Post.objects.filter(id=self.id).update(likes=F('likes') - 1)
        self.refresh_from_db()
        return self.likes

    def increment_views(self):
        """조회수 증가"""
        Post.objects.filter(id=self.id).update(views=F('views') + 1)
        self.refresh_from_db()
        return self.views

    def get_absolute_url(self):
        """게시글의 상세 페이지 URL을 반환"""
        return reverse('user_post_detail', kwargs={
            'username': self.blog.owner.username,
            'slug': self.slug
        })


class PostLikeManager(models.Manager):
    def get_queryset(self):
        """기본 queryset에 자주 사용되는 관계들을 미리 로드"""
        return super().get_queryset().select_related('user', 'post')
    
    def toggle(self, user, post):
        """좋아요 토글: 없으면 생성, 있으면 삭제"""
        like, created = self.get_or_create(user=user, post=post)
        if not created:
            like.delete()
            post.likes = models.F('likes') - 1
            post.save()
            return None
        post.likes = models.F('likes') + 1
        post.save()
        return like
    
    def get_user_likes(self, user):
        """특정 사용자의 좋아요 목록"""
        return self.get_queryset().filter(user=user).order_by('-created_at')
    
    def get_post_likes(self, post):
        """특정 게시글의 좋아요 목록"""
        return self.get_queryset().filter(post=post).order_by('-created_at')
    
    def get_recent_likes(self, days=7):
        """최근 n일 동안의 좋아요 목록"""
        start_date = timezone.now() - timedelta(days=days)
        return self.get_queryset().filter(created_at__gte=start_date).order_by('-created_at')


class PostReadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def record_read(self, user, post):
        """사용자의 게시글 조회를 기록"""
        read_record, created = self.get_or_create(
            user=user,
            post=post,
            defaults={'updated_at': timezone.now()}
        )
        if not created:
            read_record.updated_at = timezone.now()
            read_record.save(update_fields=['updated_at'])
        return read_record

    def get_user_reads(self, user):
        """사용자가 읽은 게시글 목록"""
        return self.filter(user=user).select_related('post')

    def get_post_reads(self, post):
        """게시글을 읽은 사용자 목록"""
        return self.filter(post=post).select_related('user')

    def get_recent_reads(self, days=7):
        """최근 읽은 게시글 목록"""
        start_date = timezone.now() - timedelta(days=days)
        return self.filter(updated_at__gte=start_date)


class PostLike(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PostLikeManager()

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"


class PostRead(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostReadManager()

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} read {self.post.title}"
