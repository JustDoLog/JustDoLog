from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from blog.models import Blog, Post
from ..models import Follow

User = get_user_model()


class UserTemplateTests(TestCase):
    def setUp(self):
        """테스트 설정"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )
        self.user_blog = Blog.objects.get(owner=self.user)
        self.other_blog = Blog.objects.get(owner=self.other_user)

    def test_profile_page_elements(self):
        """프로필 페이지 필수 요소 테스트"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("profile"))
        content = response.content.decode()

        # 필수 UI 요소 확인
        self.assertIn("프로필 설정", content)  # 페이지 제목
        self.assertIn("프로필 수정", content)  # 수정 버튼
        self.assertIn("계정 정보", content)  # 섹션 제목
        self.assertIn("블로그 정보", content)  # 섹션 제목
        self.assertIn("계정 삭제", content)  # 섹션 제목

        # 사용자 정보 표시 확인
        self.assertIn(self.user.username, content)
        self.assertIn(self.user.email, content)

    def test_profile_edit_form_elements(self):
        """프로필 수정 폼 요소 테스트"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("profile_edit"))
        content = response.content.decode()

        # 폼 필드 존재 확인
        self.assertIn('name="github_url"', content)
        self.assertIn('name="twitter_url"', content)
        self.assertIn('name="facebook_url"', content)
        self.assertIn('name="homepage_url"', content)
        self.assertIn('name="blog_title"', content)
        self.assertIn('name="blog_description"', content)
        self.assertIn('name="profile_image"', content)

        # CSRF 토큰 확인
        self.assertIn("csrfmiddlewaretoken", content)

    def test_follow_button_states(self):
        """팔로우 버튼 상태 테스트"""
        self.client.login(username="testuser", password="testpass123")

        # 팔로우하기 전
        response = self.client.get(
            reverse("user_blog_main", kwargs={"username": self.other_user.username})
        )
        self.assertIn("팔로우", response.content.decode())
        self.assertNotIn("팔로잉", response.content.decode())

        # 팔로우 후
        Follow.objects.create(follower=self.user, following=self.other_user)
        response = self.client.get(
            reverse("user_blog_main", kwargs={"username": self.other_user.username})
        )
        self.assertIn("팔로잉", response.content.decode())
        self.assertNotIn("팔로우", response.content.decode())

    def test_conditional_elements(self):
        """조건부 요소 표시 테스트"""
        # 로그인하지 않은 상태
        response = self.client.get(
            reverse("user_blog_main", kwargs={"username": self.other_user.username})
        )
        content = response.content.decode()
        self.assertNotIn("프로필 수정", content)  # 수정 버튼 없음
        self.assertNotIn("계정 삭제", content)  # 삭제 버튼 없음

        # 자신의 프로필
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("profile"))
        content = response.content.decode()
        self.assertIn("프로필 수정", content)  # 수정 버튼 있음
        self.assertIn("계정 삭제", content)  # 삭제 버튼 있음

        # 다른 사용자의 프로필
        response = self.client.get(
            reverse("user_blog_main", kwargs={"username": self.other_user.username})
        )
        content = response.content.decode()
        self.assertNotIn("프로필 수정", content)  # 수정 버튼 없음
        self.assertNotIn("계정 삭제", content)  # 삭제 버튼 없음

    def test_social_links_display(self):
        """소셜 링크 표시 테스트"""
        # 소셜 링크가 없는 경우
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("profile"))
        content = response.content.decode()
        self.assertNotIn('href="https://github.com"', content)
        self.assertNotIn('href="https://twitter.com"', content)

        # 소셜 링크 추가 후
        self.user.github_url = "https://github.com/testuser"
        self.user.twitter_url = "https://twitter.com/testuser"
        self.user.save()

        response = self.client.get(reverse("profile"))
        content = response.content.decode()
        self.assertIn(self.user.github_url, content)
        self.assertIn(self.user.twitter_url, content)

    def test_error_messages(self):
        """에러 메시지 표시 테스트"""
        self.client.login(username="testuser", password="testpass123")

        # 잘못된 URL로 프로필 수정 시도
        data = {
            "github_url": "not-a-url",
            "twitter_url": "not-a-url",
            "blog_title": "Test Blog",
            "blog_description": "Test Description",
        }
        response = self.client.post(reverse("profile_edit"), data, follow=True)

        # 프로필 페이지로 리다이렉트되었는지 확인
        self.assertRedirects(response, reverse("profile"))

        # 메시지가 세션에 저장되었는지 확인
        messages = list(response.context["messages"])
        self.assertTrue(len(messages) > 0)

    def test_htmx_elements(self):
        """HTMX 관련 요소 테스트"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_blog_main", kwargs={"username": self.other_user.username})
        )
        content = response.content.decode()

        # HTMX 속성 확인
        self.assertIn("hx-post", content)
        self.assertIn("hx-swap", content)
        self.assertIn("hx-headers", content)  # CSRF 토큰을 위한 헤더

    def test_blog_post_elements(self):
        """블로그 포스트 표시 테스트"""
        # 포스트 생성
        post = Post.objects.create(
            blog=self.other_blog,
            author=self.other_user,
            title="Test Post",
            content="Test Content",
            status="published",
        )

        # 포스트 목록 확인
        response = self.client.get(
            reverse("user_blog_main", kwargs={"username": self.other_user.username})
        )
        content = response.content.decode()

        # 포스트 요소 확인
        self.assertIn(post.title, content)
        self.assertIn("Test Content", content)
        self.assertIn("조회수", content)
        self.assertIn("좋아요", content)
