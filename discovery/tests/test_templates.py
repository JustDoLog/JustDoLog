from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from blog.models import Post, Blog
from user.models import Follow
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class DiscoveryTemplateTests(TestCase):
    def setUp(self):
        """테스트 설정"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.blog = self.user.blog
        self.other_blog = self.other_user.blog

        # 게시글 생성
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )
        self.other_post = Post.objects.create(
            blog=self.other_blog,
            author=self.other_user,
            title='Other Post',
            content='Other Content',
            status='published'
        )

    def test_base_post_list_template(self):
        """기본 포스트 리스트 템플릿 테스트"""
        response = self.client.get(reverse('recent_posts'))
        
        # 게시글 정보 표시 확인
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.blog.owner.username)
        self.assertContains(response, self.post.content[:30])  # 내용 미리보기
        self.assertContains(response, self.post.created_at.strftime('%Y년 %m월 %d일'))
        self.assertContains(response, f'조회수 {self.post.views}')
        self.assertContains(response, f'좋아요 {self.post.likes}')

    def test_search_template(self):
        """검색 템플릿 테스트"""
        # 검색어 없는 경우
        response = self.client.get(reverse('search'))
        self.assertContains(response, '검색어를 입력해주세요')
        self.assertContains(response, '검색어를 입력하세요')  # placeholder

        # 검색어가 있는 경우
        response = self.client.get(reverse('search') + '?q=Test')
        self.assertContains(response, '"Test" 검색 결과')
        self.assertContains(response, 'Test Post')  # 검색된 게시글
        self.assertNotContains(response, 'Other Post')  # 검색되지 않은 게시글

        # 검색 결과 없는 경우
        response = self.client.get(reverse('search') + '?q=NonExistent')
        self.assertContains(response, '"NonExistent"에 대한 검색 결과가 없습니다')

    def test_empty_messages(self):
        """빈 상태 메시지 테스트"""
        # 로그인
        self.client.login(username='testuser', password='testpass123')

        # 좋아요한 글 없는 경우
        response = self.client.get(reverse('liked_posts'))
        self.assertContains(response, '아직 좋아요한 글이 없습니다')

        # 최근 읽은 글 없는 경우
        response = self.client.get(reverse('recent_read_posts'))
        self.assertContains(response, '아직 읽은 글이 없습니다')

        # 팔로잉한 사용자의 글 없는 경우
        response = self.client.get(reverse('following_posts'))
        self.assertContains(response, '아직 팔로우하는 블로거가 없습니다')

    def test_popular_bloggers_template(self):
        """인기 블로거 템플릿 테스트"""
        # 팔로워 추가
        Follow.objects.create(follower=self.user, following=self.other_user)
        
        # 로그인 상태에서 확인
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('popular_bloggers'))
        
        # 블로거 정보 표시 확인
        self.assertContains(response, self.other_user.username)
        self.assertContains(response, '팔로워')
        self.assertContains(response, '최근 30일')  # 인기도 계산 기간
        
        # 팔로우 버튼 상태 확인
        self.assertContains(response, 'hx-post')  # HTMX 사용
        self.assertContains(response, 'follow-button')  # 팔로우 버튼 클래스

    def test_pagination_elements(self):
        """페이지네이션 요소 테스트"""
        # 페이지당 10개의 게시글을 표시하므로, 11개의 게시글 생성
        for i in range(9):  # 이미 2개가 있으므로 9개 더 생성
            Post.objects.create(
                blog=self.blog,
                author=self.user,
                title=f'Pagination Test Post {i}',
                content=f'Content {i}',
                status='published'
            )

        # 첫 페이지 확인
        response = self.client.get(reverse('recent_posts'))
        self.assertContains(response, '다음')
        self.assertContains(response, 'page=2')
        self.assertContains(response, '1 / 2')  # 현재 페이지 / 전체 페이지

        # 두 번째 페이지 확인
        response = self.client.get(reverse('recent_posts') + '?page=2')
        self.assertContains(response, '이전')
        self.assertContains(response, 'page=1')
        self.assertContains(response, '2 / 2')
