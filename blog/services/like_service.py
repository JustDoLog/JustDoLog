from django.core.cache import cache
from django.db.models import F
from ..models import Post

class LikeService:
    @staticmethod
    def toggle_like(user, post):
        """
        사용자의 게시글 좋아요를 토글하고 결과를 반환합니다.
        
        Args:
            user: 좋아요를 토글하는 사용자
            post: 대상 게시글
            
        Returns:
            tuple: (좋아요 상태, 업데이트된 좋아요 수)
        """
        # 캐시 키 생성
        cache_key = post.get_cache_key('likes')
        
        # 좋아요 상태 확인 및 토글
        if post.liked_by.filter(id=user.id).exists():
            post.liked_by.remove(user)
            Post.objects.filter(id=post.id).update(likes=F('likes') - 1)
            has_liked = False
        else:
            post.liked_by.add(user)
            Post.objects.filter(id=post.id).update(likes=F('likes') + 1)
            has_liked = True
        
        # 객체 새로고침
        post.refresh_from_db()
        likes_count = post.likes
        
        # 캐시 업데이트
        cache.set(cache_key, likes_count)
        
        return has_liked, likes_count

    @staticmethod
    def get_like_status(user, post):
        """
        사용자의 게시글 좋아요 상태를 확인합니다.
        
        Args:
            user: 확인할 사용자
            post: 대상 게시글
            
        Returns:
            bool: 좋아요 여부
        """
        if not user.is_authenticated:
            return False
        return post.liked_by.filter(id=user.id).exists()

    @staticmethod
    def get_likes_count(post):
        """
        게시글의 좋아요 수를 반환합니다.
        캐시된 값이 있으면 캐시에서, 없으면 DB에서 조회합니다.
        
        Args:
            post: 대상 게시글
            
        Returns:
            int: 좋아요 수
        """
        cache_key = post.get_cache_key('likes')
        likes_count = cache.get(cache_key)
        
        if likes_count is None:
            likes_count = post.likes
            cache.set(cache_key, likes_count)
            
        return likes_count
