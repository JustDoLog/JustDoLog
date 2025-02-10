from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from blog.models import Blog, Post, PostLike
from taggit.models import Tag

User = get_user_model()

class BlogTemplateTests(TestCase):
    def setUp(self):
        """테스트 설정"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.blog = self.user.blog
        self.blog.title = "Test Blog"
        self.blog.description = "Test Description"
        self.blog.save()

        # 게시글 생성
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )
        
        # 태그 추가
        self.post.tags.add("python", "django")

    def test_blog_main_page_elements(self):
        """블로그 메인 페이지 요소 테스트"""
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        content = response.content.decode()

        # 기본 정보 표시 확인
        self.assertTemplateUsed(response, 'blog/user_blog_main.html')
        self.assertContains(response, self.blog.title)
        self.assertContains(response, self.blog.description)
        self.assertContains(response, self.user.username)

        # 태그 리스트 확인
        self.assertContains(response, 'python')
        self.assertContains(response, 'django')

        # 게시글 요소 확인
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.content[:30])  # 내용 미리보기
        self.assertContains(response, '조회수')
        self.assertContains(response, '좋아요')

    def test_post_detail_page_elements(self):
        """게시글 상세 페이지 요소 테스트"""
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        content = response.content.decode()

        # 기본 요소 확인
        self.assertTemplateUsed(response, 'blog/user_post_detail.html')
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.content)
        
        # 메타 정보 확인
        self.assertContains(response, self.post.created_at.strftime('%Y년 %m월 %d일'))
        self.assertContains(response, '조회수')
        self.assertContains(response, '좋아요')

        # 태그 표시 확인
        self.assertContains(response, 'python')
        self.assertContains(response, 'django')

    def test_post_form_elements(self):
        """게시글 작성/수정 폼 요소 테스트"""
        self.client.login(username='testuser', password='testpass123')
        
        # 작성 폼
        response = self.client.get(
            reverse('user_post_create', kwargs={'username': self.user.username})
        )
        self.assertTemplateUsed(response, 'blog/user_post_form.html')
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="content"')
        self.assertContains(response, 'name="status"')
        self.assertContains(response, 'name="tags"')

        # 수정 폼
        response = self.client.get(
            reverse('user_post_update', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.content)
        self.assertContains(response, 'python')
        self.assertContains(response, 'django')

    def test_draft_post_elements(self):
        """임시저장 게시글 표시 테스트"""
        # 임시저장 게시글 생성
        draft_post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Draft Post',
            content='Draft Content',
            status='draft'
        )

        # 작성자로 로그인
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        
        # 임시저장 표시 확인
        self.assertContains(response, 'Draft Post')
        self.assertContains(response, '임시')

        # 다른 사용자로 접근
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        
        # 임시저장 게시글이 보이지 않아야 함
        self.assertNotContains(response, 'Draft Post')

    def test_like_button_states(self):
        """좋아요 버튼 상태 테스트"""
        # 비로그인 상태
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        self.assertContains(response, '/accounts/login/')  # 로그인 링크 확인

        # 로그인 상태
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username='otheruser', password='testpass123')
        
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        self.assertContains(response, 'hx-post')  # HTMX 속성 확인
        self.assertContains(response, 'like-button')  # 좋아요 버튼 클래스 확인

        # 좋아요 후 상태
        PostLike.objects.create(user=other_user, post=self.post)
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        self.assertContains(response, 'text-gray-900')  # 활성화된 좋아요 버튼 스타일

    def test_empty_blog_message(self):
        """게시글이 없는 경우 메시지 테스트"""
        # 모든 게시글 삭제
        Post.objects.all().delete()
        
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        
        # 빈 블로그 메시지 확인
        self.assertContains(response, '아직 작성한 게시글이 없습니다')
        
        # 작성자로 로그인 시 글쓰기 링크 표시
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        self.assertContains(response, '첫 번째 글을 작성해보세요')

    def test_pagination_elements(self):
        """페이지네이션 요소 테스트"""
        # 추가 게시글 생성
        for i in range(11):  # 기본 1개 + 11개 = 12개
            Post.objects.create(
                blog=self.blog,
                author=self.user,
                title=f'Test Post {i}',
                content=f'Test Content {i}',
                status='published'
            )

        # 첫 페이지 확인
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        self.assertContains(response, '다음')
        self.assertContains(response, 'page=2')
        self.assertContains(response, '1 / 2')  # 페이지 번호 확인

        # 두 번째 페이지 확인
        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username}) + '?page=2'
        )
        self.assertContains(response, '이전')
        self.assertContains(response, 'page=1')
        self.assertContains(response, '2 / 2')  # 페이지 번호 확인

    def test_social_links(self):
        """소셜 링크 표시 테스트"""
        # 소셜 링크 추가
        self.user.github_url = 'https://github.com/testuser'
        self.user.twitter_url = 'https://twitter.com/testuser'
        self.user.save()

        response = self.client.get(
            reverse('user_blog_main', kwargs={'username': self.user.username})
        )
        
        # 소셜 링크 확인
        self.assertContains(response, self.user.github_url)
        self.assertContains(response, self.user.twitter_url)
        self.assertContains(response, 'target="_blank"')  # 새 탭에서 열기
        self.assertContains(response, 'rel="noopener noreferrer"')  # 보안 속성 