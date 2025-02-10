from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from blog.models import Post, Blog
from user.models import Follow
from django.utils import timezone
from datetime import timedelta
from taggit.models import Tag
from freezegun import freeze_time

User = get_user_model()

class DiscoveryViewTests(TestCase):
    @freeze_time("2024-03-15 12:00:00")
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

        # 태그 추가
        self.post.tags.add("python", "django")
        self.other_post.tags.add("python", "test")

    @freeze_time("2024-03-15 12:00:00")
    def test_trending_posts_view(self):
        """트렌딩 포스트 뷰 테스트"""
        # 현재 시간을 2024-03-15 12:00:00로 고정
        frozen_time = timezone.now()
        today = frozen_time.date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        
        # 오늘 작성된 게시글들의 시간 설정
        self.post.created_at = today_start
        self.post.updated_at = today_start
        self.post.likes = 10
        self.post.save()
        
        self.other_post.created_at = today_start
        self.other_post.updated_at = today_start
        self.other_post.likes = 5
        self.other_post.save()

        # 일간 트렌딩 테스트
        response = self.client.get(reverse('trending_day'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'discovery/trending_posts.html')
        posts = list(response.context['posts'])
        self.assertEqual(posts[0], self.post)  # 좋아요가 많은 게시글이 먼저
        self.assertEqual(posts[1], self.other_post)

        # 4일 전 게시글 생성
        with freeze_time(frozen_time - timedelta(days=4)):
            old_post = Post.objects.create(
                blog=self.blog,
                author=self.user,
                title='Old Post',
                content='Old Content',
                status='published'
            )
        
        # 일간 필터링 테스트 - 오늘 작성된 글만 포함되어야 함
        response = self.client.get(reverse('trending_day') + '?period=day')
        self.assertNotIn(old_post, response.context['posts'])
        self.assertEqual(len(response.context['posts']), 2)

        # 주간 필터링 테스트 - 일주일 내 작성된 글 모두 포함
        response = self.client.get(reverse('trending_day') + '?period=week')
        self.assertIn(old_post, response.context['posts'])
        self.assertEqual(len(response.context['posts']), 3)

    @freeze_time("2024-03-15 12:00:00")
    def test_recent_posts_view(self):
        """최신 포스트 뷰 테스트"""
        response = self.client.get(reverse('recent_posts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'discovery/recent_posts.html')
        self.assertIn(self.post, response.context['posts'])
        self.assertIn(self.other_post, response.context['posts'])

    @freeze_time("2024-03-15 12:00:00")
    def test_liked_posts_view(self):
        """좋아요한 포스트 뷰 테스트"""
        # 비로그인 상태
        response = self.client.get(reverse('liked_posts'))
        self.assertEqual(response.status_code, 302)  # 로그인 페이지로 리다이렉트

        # 로그인 상태
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('liked_posts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'discovery/liked_posts.html')

        # 좋아요 추가 후 테스트
        self.other_post.liked_by.add(self.user)
        response = self.client.get(reverse('liked_posts'))
        self.assertIn(self.other_post, response.context['posts'])

    @freeze_time("2024-03-15 12:00:00")
    def test_recent_read_posts_view(self):
        """최근 읽은 포스트 뷰 테스트"""
        # 비로그인 상태
        response = self.client.get(reverse('recent_read_posts'))
        self.assertEqual(response.status_code, 302)  # 로그인 페이지로 리다이렉트

        # 로그인 상태
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('recent_read_posts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'discovery/recent_read_posts.html')

        # 읽은 포스트 추가 후 테스트
        self.other_post.read_by.add(self.user)
        response = self.client.get(reverse('recent_read_posts'))
        self.assertIn(self.other_post, response.context['posts'])

    @freeze_time("2024-03-15 12:00:00")
    def test_popular_bloggers_view(self):
        """인기 블로거 뷰 테스트"""
        response = self.client.get(reverse('popular_bloggers'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'discovery/popular_bloggers.html')

        # 팔로워 추가
        Follow.objects.create(follower=self.user, following=self.other_user)
        
        # 로그인 상태에서 팔로잉 정보 확인
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('popular_bloggers'))
        self.assertTrue(response.context['following_dict'][self.other_user.id])

    @freeze_time("2024-03-15 12:00:00")
    def test_search_view(self):
        """검색 뷰 테스트"""
        # 검색어 없는 경우
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['posts']), 0)

        # 검색어가 있는 경우
        response = self.client.get(reverse('search') + '?q=Test')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.post, response.context['posts'])
        self.assertNotIn(self.other_post, response.context['posts'])

    @freeze_time("2024-03-15 12:00:00")
    def test_following_posts_view(self):
        """팔로잉 포스트 뷰 테스트"""
        # 비로그인 상태
        response = self.client.get(reverse('following_posts'))
        self.assertEqual(response.status_code, 302)  # 로그인 페이지로 리다이렉트

        # 로그인 상태
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('following_posts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'discovery/following_posts.html')

        # 팔로잉 추가 후 테스트
        Follow.objects.create(follower=self.user, following=self.other_user)
        response = self.client.get(reverse('following_posts'))
        self.assertIn(self.other_post, response.context['posts'])
        self.assertEqual(response.context['following_count'], 1)

    @freeze_time("2024-03-15 12:00:00")
    def test_tagged_posts_view(self):
        """태그별 포스트 뷰 테스트"""
        response = self.client.get(reverse('tagged_posts', kwargs={'tag_name': 'python'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'discovery/tagged_posts.html')
        self.assertIn(self.post, response.context['posts'])
        self.assertIn(self.other_post, response.context['posts'])
        self.assertEqual(response.context['tag_name'], 'python')

        # django 태그로 필터링
        response = self.client.get(reverse('tagged_posts', kwargs={'tag_name': 'django'}))
        self.assertIn(self.post, response.context['posts'])
        self.assertNotIn(self.other_post, response.context['posts'])
