from django.core.cache import cache
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model
from ..models import Post, Blog
from .read_service import ReadService

User = get_user_model()

class PostService:
    @staticmethod
    def get_user_posts(username, user=None, tag=None):
        """
        사용자의 게시글 목록을 반환합니다.
        
        Args:
            username: 블로그 소유자의 사용자명
            user: 현재 요청한 사용자 (선택)
            tag: 필터링할 태그 (선택)
            
        Returns:
            QuerySet: Post 객체 목록
        """
        blog = Blog.objects.get(owner__username=username)
        
        # 현재 사용자가 블로그 소유자인 경우 draft 포함
        if user and user == blog.owner:
            posts = Post.objects.filter(blog=blog)
        else:
            posts = Post.objects.filter(blog=blog, status="published")
        
        # 태그로 필터링
        if tag:
            posts = posts.filter(tags__name=tag)
            
        # N+1 쿼리 최적화
        posts = posts.select_related('author', 'blog').prefetch_related(
            'tags',
            Prefetch(
                'liked_by',
                queryset=User.objects.filter(id=user.id) if user and user.is_authenticated else User.objects.none(),
                to_attr='user_likes'
            )
        ).order_by("-created_at")
        
        return posts

    @staticmethod
    def get_post_detail(username, slug, user=None):
        """
        게시글 상세 정보를 반환합니다.
        
        Args:
            username: 블로그 소유자의 사용자명
            slug: 게시글 슬러그
            user: 현재 요청한 사용자 (선택)
            
        Returns:
            Post: 게시글 객체
        """
        # N+1 쿼리 최적화를 위한 기본 쿼리셋
        queryset = Post.objects.select_related(
            'author', 'blog', 'blog__owner'
        ).prefetch_related(
            'tags',
            Prefetch(
                'liked_by',
                queryset=User.objects.filter(id=user.id) if user and user.is_authenticated else User.objects.none(),
                to_attr='user_likes'
            )
        )
        
        post = queryset.get(
            blog__owner__username=username,
            slug=slug
        )
        
        # draft 상태의 글은 작성자만 볼 수 있음
        if post.status == "draft" and (not user or post.blog.owner != user):
            raise Post.DoesNotExist("이 글을 볼 수 있는 권한이 없습니다.")
        
        # 조회 기록 저장 (작성자가 아닌 경우에만)
        if user and user != post.blog.owner:
            ReadService.record_read(user, post)
        
        return post

    @staticmethod
    def create_post(user, title, content, status="draft", tags=None):
        """
        새 게시글을 생성합니다.
        
        Args:
            user: 작성자
            title: 제목
            content: 내용
            status: 상태 (draft/published)
            tags: 태그 목록 (선택)
            
        Returns:
            Post: 생성된 게시글 객체
        """
        post = Post.objects.create(
            blog=user.blog,
            author=user,
            title=title,
            content=content,
            status=status
        )
        
        if tags:
            post.tags.add(*tags)
            
        return post

    @staticmethod
    def update_post(post, title=None, content=None, status=None, tags=None):
        """
        게시글을 수정합니다.
        
        Args:
            post: 수정할 게시글 객체
            title: 새 제목 (선택)
            content: 새 내용 (선택)
            status: 새 상태 (선택)
            tags: 새 태그 목록 (선택)
            
        Returns:
            Post: 수정된 게시글 객체
        """
        if title:
            post.title = title
        if content:
            post.content = content
        if status:
            post.status = status
            
        post.save()
        
        if tags is not None:  # 빈 리스트도 허용
            post.tags.clear()
            post.tags.add(*tags)
            
        return post
