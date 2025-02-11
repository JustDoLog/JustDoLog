from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from blog.models import Post, PostRead, PostLike, Blog
from user.models import Follow
from django.utils.text import slugify
from freezegun import freeze_time
from django.utils import timezone

User = get_user_model()

class BlogViewTests(TestCase):
    @freeze_time("2024-03-15 12:00:00")
    def setUp(self):
        """테스트 설정"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.blog = self.user.blog
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )

    def test_like_button_redirect_when_not_authenticated(self):
        """비로그인 사용자가 좋아요 버튼 클릭 시 로그인 페이지로 리다이렉션"""

class PostViewTests(TestCase):
    @freeze_time("2024-03-15 12:00:00")
    def setUp(self):
        """테스트 설정"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.blog = self.user.blog
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )

    @freeze_time("2024-03-15 12:00:00")
    def test_post_list_view(self):
        """게시글 목록 뷰 테스트"""
        response = self.client.get(reverse('user_blog_main', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_blog_main.html')
        self.assertContains(response, 'Test Post')

    @freeze_time("2024-03-15 12:00:00")
    def test_post_detail_view(self):
        """게시글 상세 뷰 테스트"""
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_post_detail.html')
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.content)

    @freeze_time("2024-03-15 12:00:00")
    def test_post_create_view(self):
        """게시글 생성 뷰 테스트"""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(
            reverse('user_post_create', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_post_form.html')

        post_data = {
            'title': 'New Test Post',
            'content': 'New test content',
            'status': 'published'
        }
        response = self.client.post(
            reverse('user_post_create', kwargs={'username': self.user.username}),
            post_data
        )
        self.assertEqual(response.status_code, 302)  # 리다이렉션 확인
        
        new_post = Post.objects.get(title='New Test Post')
        self.assertEqual(new_post.created_at, timezone.now())
        self.assertEqual(new_post.updated_at, timezone.now())

    @freeze_time("2024-03-15 12:00:00")
    def test_post_update_view(self):
        """게시글 수정 뷰 테스트"""
        initial_time = timezone.now()
        self.client.login(username=self.user.username, password='testpass123')
        
        with freeze_time("2024-03-15 13:00:00"):  # 1시간 후
            response = self.client.post(
                reverse('user_post_update', kwargs={
                    'username': self.user.username,
                    'slug': self.post.slug
                }),
                {
                    'title': 'Updated Title',
                    'content': 'Updated content',
                    'status': 'published'
                }
            )
            self.assertEqual(response.status_code, 302)  # 리다이렉션 확인
            
            self.post.refresh_from_db()
            self.assertEqual(self.post.title, 'Updated Title')
            self.assertEqual(self.post.content, 'Updated content')
            self.assertEqual(self.post.created_at, initial_time)  # created_at은 변경되지 않음
            self.assertEqual(self.post.updated_at, timezone.now())  # updated_at은 현재 시간으로 변경

    @freeze_time("2024-03-15 12:00:00")
    def test_post_delete_view(self):
        """게시글 삭제 뷰 테스트"""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.post(
            reverse('user_post_delete', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 302)  # 리다이렉션 확인
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    @freeze_time("2024-03-15 12:00:00")
    def test_unauthorized_post_operations(self):
        """권한이 없는 사용자의 게시글 작업 테스트"""
        # 다른 사용자 생성
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client.login(username=other_user.username, password='testpass123')

        # 수정 시도
        response = self.client.get(
            reverse('user_post_update', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 403)

        # 삭제 시도
        response = self.client.post(
            reverse('user_post_delete', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    @freeze_time("2024-03-15 12:00:00")
    def test_draft_post_visibility(self):
        """임시저장 게시글 접근 제한 테스트"""
        draft_post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Draft Post',
            content='Draft Content',
            status='draft'
        )
        
        # 비로그인 사용자
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': draft_post.slug
            })
        )
        self.assertEqual(response.status_code, 404)
        
        # 다른 사용자
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        self.client.login(username='otheruser', password='pass123')
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': draft_post.slug
            })
        )
        self.assertEqual(response.status_code, 404)
        
        # 작성자 본인
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': draft_post.slug
            })
        )
        self.assertEqual(response.status_code, 200)

class PostInteractionViewTests(TestCase):
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
            password='pass123'
        )
        self.blog = self.user.blog
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )

    @freeze_time("2024-03-15 12:00:00")
    def test_post_like_toggle(self):
        """게시글 좋아요 토글 테스트"""
        self.client.login(username='otheruser', password='pass123')
        
        # 좋아요 추가
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            }),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(user=self.other_user, post=self.post).exists())
        
        # 좋아요 취소
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            }),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PostLike.objects.filter(user=self.other_user, post=self.post).exists())

    @freeze_time("2024-03-15 12:00:00")
    def test_post_read_tracking(self):
        """게시글 조회 기록 테스트"""
        self.client.login(username='otheruser', password='pass123')
        
        # 첫 조회
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostRead.objects.filter(user=self.other_user, post=self.post).exists())
        
        # 재조회
        initial_read_count = PostRead.objects.filter(user=self.other_user, post=self.post).count()
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            PostRead.objects.filter(user=self.other_user, post=self.post).count(),
            initial_read_count  # 조회 기록이 중복 생성되지 않아야 함
        )

    @freeze_time("2024-03-15 12:00:00")
    def test_post_interaction_authentication(self):
        """게시글 상호작용 인증 요구 테스트"""
        # 비로그인 상태에서 좋아요 시도
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            }),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 302)  # 로그인 페이지로 리다이렉트
        
        # 비로그인 상태에서 조회 시 PostRead 생성되지 않음
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PostRead.objects.filter(post=self.post).exists()) 

class PaginatedListMixinTests(TestCase):
    @freeze_time("2024-03-15 12:00:00")
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.blog = self.user.blog

        # 페이지네이션 테스트를 위한 게시글 생성
        for i in range(15):  # 15개의 게시글 생성
            Post.objects.create(
                blog=self.blog,
                author=self.user,
                title=f'Test Post {i}',
                content=f'Content {i}',
                status='published'
            )

    def test_pagination_with_valid_page(self):
        """유효한 페이지 번호로 페이지네이션 테스트"""
        response = self.client.get(reverse('user_blog_main', kwargs={'username': self.user.username}) + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['object_list']), 5)  # 두 번째 페이지에는 5개의 게시글

    def test_pagination_with_invalid_page(self):
        """잘못된 페이지 번호로 페이지네이션 테스트"""
        response = self.client.get(reverse('user_blog_main', kwargs={'username': self.user.username}) + '?page=999')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['page_obj'].number, 2)  # 마지막 페이지로 이동

    def test_pagination_with_non_integer_page(self):
        """숫자가 아닌 페이지 값으로 페이지네이션 테스트"""
        response = self.client.get(reverse('user_blog_main', kwargs={'username': self.user.username}) + '?page=abc')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['page_obj'].number, 1)  # 첫 페이지로 이동 

class UserContextMixinTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.blog = self.user.blog
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )

    def test_following_context(self):
        """팔로우 컨텍스트 테스트"""
        # 다른 사용자로 로그인
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        
        # 팔로우하기 전
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_following'])
        
        # 팔로우 후
        Follow.objects.create(follower=other_user, following=self.user)
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertTrue(response.context['is_following'])

    def test_like_context(self):
        """좋아요 컨텍스트 테스트"""
        # 다른 사용자로 로그인
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        
        # 좋아요하기 전
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertFalse(response.context['has_liked'])
        
        # 좋아요 후
        self.post.liked_by.add(other_user)
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertTrue(response.context['has_liked'])

    def test_unauthenticated_user_context(self):
        """비인증 사용자에 대한 컨텍스트 테스트"""
        # 로그아웃 상태에서 접근
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_owner'])
        self.assertFalse(response.context['has_liked'])
        self.assertFalse(response.context['is_following'])

class HtmxResponseMixinTests(TestCase):
    def setUp(self):
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
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )
        # 로그인
        self.assertTrue(
            self.client.login(username='otheruser', password='otherpass123')
        )

    def test_htmx_like_toggle_response(self):
        """HTMX 좋아요 토글 응답 테스트"""
        # HTMX 헤더 추가
        headers = {
            'HTTP_HX_REQUEST': 'true',
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'
        }
        
        # 좋아요 요청
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            }),
            **headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('좋아요 취소', response.content.decode())
        self.assertIn('HX-Trigger', response.headers)
        
        # 좋아요 취소 요청
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            }),
            **headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('좋아요', response.content.decode())

    def test_non_htmx_request_handling(self):
        """비 HTMX 요청 처리 테스트"""
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 400)

    def test_htmx_trigger_headers(self):
        """HTMX 트리거 헤더 테스트"""
        headers = {
            'HTTP_HX_REQUEST': 'true',
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'
        }
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            }),
            **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        self.assertIn('likesUpdated', response.headers['HX-Trigger']) 

class PostDetailViewTest(TestCase):
    def setUp(self):
        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Blog는 User 생성 시 자동으로 생성되므로 따로 생성하지 않음
        self.blog = self.user.blog  # 직접 접근
        
        # 테스트 포스트 생성
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            blog=self.blog,
            author=self.user,
            status='published'
        )
        
        self.client = Client()
        
        # URL 패턴
        self.post_url = reverse('user_post_detail', kwargs={
            'username': self.user.username,
            'slug': self.post.slug
        })

    def test_post_detail_edit_delete_buttons_for_author(self):
        """작성자로 로그인했을 때 수정/삭제 버튼이 보이는지 테스트"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.post_url)
        
        self.assertEqual(response.status_code, 200)
        # 수정 버튼 URL이 포함되어 있는지 확인
        self.assertContains(
            response,
            reverse('user_post_update', kwargs={'username': self.user.username, 'slug': self.post.slug})
        )
        # 삭제 버튼 URL이 포함되어 있는지 확인
        self.assertContains(
            response,
            reverse('user_post_delete', kwargs={'username': self.user.username, 'slug': self.post.slug})
        )

    def test_post_detail_no_edit_delete_buttons_for_other_user(self):
        """다른 사용자로 로그인했을 때 수정/삭제 버튼이 보이지 않는지 테스트"""
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(self.post_url)
        
        self.assertEqual(response.status_code, 200)
        # 수정 버튼 URL이 없는지 확인
        self.assertNotContains(
            response,
            reverse('user_post_update', kwargs={'username': self.user.username, 'slug': self.post.slug})
        )
        # 삭제 버튼 URL이 없는지 확인
        self.assertNotContains(
            response,
            reverse('user_post_delete', kwargs={'username': self.user.username, 'slug': self.post.slug})
        )

    def test_post_detail_no_edit_delete_buttons_for_anonymous(self):
        """비로그인 사용자일 때 수정/삭제 버튼이 보이지 않는지 테스트"""
        response = self.client.get(self.post_url)
        
        self.assertEqual(response.status_code, 200)
        # 수정 버튼 URL이 없는지 확인
        self.assertNotContains(
            response,
            reverse('user_post_update', kwargs={'username': self.user.username, 'slug': self.post.slug})
        )
        # 삭제 버튼 URL이 없는지 확인
        self.assertNotContains(
            response,
            reverse('user_post_delete', kwargs={'username': self.user.username, 'slug': self.post.slug})
        ) 