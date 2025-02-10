from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from blog.models import Post, PostRead, PostLike
from django.utils.text import slugify

User = get_user_model()

class BlogViewTests(TestCase):
    def setUp(self):
        """테스트 사용자 및 블로그 생성"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 블로그는 signals.py에서 자동으로 생성되므로 직접 생성하지 않음
        self.blog = self.user.blog  # OneToOne 관계를 통해 접근
        
        self.post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Test Post',
            content='Test Content',
            status='published'
        )
        self.client = Client()

    def test_integration_scenario(self):
        """통합 시나리오 테스트: 계정 생성부터 게시글 상호작용까지"""
        # 1. 새로운 사용자 생성 및 블로그 자동 생성 확인
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        self.assertTrue(hasattr(new_user, 'blog'))
        self.assertIsNotNone(new_user.blog)

        # 2. 로그인
        self.client.login(username='newuser', password='newpass123')

        # 3. 이미지가 포함된 새 게시글 작성
        post_data = {
            'title': 'New Post with Image',
            'content': '<p>Test content</p><img src="https://example.com/image.jpg"><p>More content</p>',
            'status': 'published'
        }
        response = self.client.post(
            reverse('user_post_create', kwargs={'username': new_user.username}),
            post_data
        )
        self.assertEqual(response.status_code, 302)  # 리다이렉트 확인

        # 4. 생성된 게시글 확인
        new_post = Post.objects.get(title='New Post with Image')
        self.assertEqual(new_post.author, new_user)
        self.assertEqual(new_post.blog, new_user.blog)
        self.assertEqual(new_post.thumbnail, 'https://example.com/image.jpg')  # 썸네일 자동 추출 확인

        # 5. 다른 사용자 생성 및 게시글 상호작용
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')

        # 6. 게시글 조회 (PostRead 생성)
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': new_user.username,
                'slug': new_post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostRead.objects.filter(user=other_user, post=new_post).exists())

        # 7. 게시글 좋아요 (PostLike 생성)
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': new_user.username,
                'slug': new_post.slug
            }),
            HTTP_HX_REQUEST='true'  # HTMX 요청 시뮬레이션
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(user=other_user, post=new_post).exists())
        
        # 8. 게시글 상태 확인
        new_post.refresh_from_db()
        self.assertEqual(new_post.likes, 1)  # 좋아요 수 증가
        self.assertEqual(new_post.views, 1)  # 조회수 증가

        # 9. 중복 좋아요 방지 확인
        response = self.client.post(
            reverse('toggle_like', kwargs={
                'username': new_user.username,
                'slug': new_post.slug
            }),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PostLike.objects.filter(user=other_user, post=new_post).count(), 0)  # 좋아요 취소됨

        # 10. 중복 조회 확인 (같은 사용자가 다시 조회)
        response = self.client.get(
            reverse('user_post_detail', kwargs={
                'username': new_user.username,
                'slug': new_post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PostRead.objects.filter(user=other_user, post=new_post).count(), 1)  # 중복 조회 기록 없음
        new_post.refresh_from_db()
        self.assertEqual(new_post.views, 1)  # 조회수 증가 없음

    def test_like_button_redirect_when_not_authenticated(self):
        """비로그인 사용자가 좋아요 버튼 클릭 시 로그인 페이지로 리다이렉션""" 

class PostViewTests(TestCase):
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

    def test_post_list_view(self):
        """게시글 목록 뷰 테스트"""
        response = self.client.get(reverse('user_blog_main', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_blog_main.html')
        self.assertContains(response, 'Test Post')

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
        self.assertTrue(Post.objects.filter(title='New Test Post').exists())

    def test_post_update_view(self):
        """게시글 수정 뷰 테스트"""
        self.client.login(username=self.user.username, password='testpass123')
        response = self.client.get(
            reverse('user_post_update', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_post_form.html')

        updated_data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'status': 'published'
        }
        response = self.client.post(
            reverse('user_post_update', kwargs={
                'username': self.user.username,
                'slug': self.post.slug
            }),
            updated_data
        )
        self.assertEqual(response.status_code, 302)  # 리다이렉션 확인
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')
        self.assertEqual(self.post.content, 'Updated content')

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