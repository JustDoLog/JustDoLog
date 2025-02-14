from django.core.cache import cache
from django.db.models import F
from ..models import Post, PostRead


class ReadService:
    @staticmethod
    def record_read(user, post):
        """
        사용자의 게시글 조회를 기록합니다.

        Args:
            user: 조회한 사용자 (AnonymousUser 가능)
            post: 조회한 게시글
        """
        # 로그인한 사용자의 경우
        if user.is_authenticated:
            # 자신의 글은 조회수를 증가시키지 않음
            if post.author != user:
                # PostRead 레코드 생성 또는 업데이트
                PostRead.objects.record_read(user=user, post=post)
                # 조회수 증가
                Post.objects.filter(id=post.id).update(views=F("views") + 1)
                post.refresh_from_db()
        # 익명 사용자의 경우
        else:
            Post.objects.filter(id=post.id).update(views=F("views") + 1)
            post.refresh_from_db()

        # 캐시 업데이트
        cache_key = post.get_cache_key("views")
        cache.set(cache_key, post.views)

    @staticmethod
    def get_views_count(post):
        """
        게시글의 조회수를 반환합니다.
        캐시된 값이 있으면 캐시에서, 없으면 DB에서 조회합니다.

        Args:
            post: 대상 게시글

        Returns:
            int: 조회수
        """
        cache_key = post.get_cache_key("views")
        views_count = cache.get(cache_key)

        if views_count is None:
            views_count = post.views
            cache.set(cache_key, views_count)

        return views_count

    @staticmethod
    def get_read_status(user, post):
        """
        사용자의 게시글 조회 여부를 확인합니다.

        Args:
            user: 확인할 사용자
            post: 대상 게시글

        Returns:
            bool: 조회 여부
        """
        if not user.is_authenticated:
            return False
        return post.read_by.filter(id=user.id).exists()

    @staticmethod
    def get_recent_reads(user, days=7):
        """
        사용자의 최근 읽은 게시글 목록을 반환합니다.

        Args:
            user: 대상 사용자
            days: 조회할 기간 (일)

        Returns:
            QuerySet: PostRead 객체 목록
        """
        return PostRead.objects.get_user_reads(user).filter(post__status="published")
