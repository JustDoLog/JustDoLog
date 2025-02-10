from django.test import TestCase
from django.contrib.auth import get_user_model
from blog.models import Blog, Post, PostLike, PostRead
from blog.services.like_service import LikeService
from blog.services.read_service import ReadService
from blog.services.post_service import PostService
from django.core.cache import cache
from freezegun import freeze_time

User = get_user_model()

class LikeServiceTests(TestCase):
    @freeze_time("2024-03-15 12:00:00")
    def setUp(self):
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

    def tearDown(self):
        cache.clear()

    def test_toggle_like(self):
        """좋아요 토글 테스트"""
        # 좋아요 추가
        has_liked, likes_count = LikeService.toggle_like(self.other_user, self.post)
        self.assertTrue(has_liked)
        self.assertEqual(likes_count, 1)
        self.assertTrue(self.post.liked_by.filter(id=self.other_user.id).exists())

        # 좋아요 취소
        has_liked, likes_count = LikeService.toggle_like(self.other_user, self.post)
        self.assertFalse(has_liked)
        self.assertEqual(likes_count, 0)
        self.assertFalse(self.post.liked_by.filter(id=self.other_user.id).exists())

    def test_get_like_status(self):
        """좋아요 상태 확인 테스트"""
        self.assertFalse(LikeService.get_like_status(self.other_user, self.post))
        
        self.post.liked_by.add(self.other_user)
        self.assertTrue(LikeService.get_like_status(self.other_user, self.post))

    def test_get_likes_count(self):
        """좋아요 수 조회 테스트"""
        self.assertEqual(LikeService.get_likes_count(self.post), 0)
        
        # LikeService를 통해 좋아요 추가
        LikeService.toggle_like(self.other_user, self.post)
        self.assertEqual(LikeService.get_likes_count(self.post), 1)


class ReadServiceTests(TestCase):
    @freeze_time("2024-03-15 12:00:00")
    def setUp(self):
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

    def tearDown(self):
        cache.clear()

    def test_record_read(self):
        """조회 기록 테스트"""
        # 다른 사용자가 조회
        ReadService.record_read(self.other_user, self.post)
        self.assertTrue(PostRead.objects.filter(user=self.other_user, post=self.post).exists())
        self.assertEqual(self.post.views, 1)

        # 작성자가 조회 (조회수 증가하지 않음)
        ReadService.record_read(self.user, self.post)
        self.assertEqual(self.post.views, 1)

    def test_get_views_count(self):
        """조회수 확인 테스트"""
        self.assertEqual(ReadService.get_views_count(self.post), 0)
        
        # ReadService를 통해 조회수 증가
        ReadService.record_read(self.other_user, self.post)
        self.assertEqual(ReadService.get_views_count(self.post), 1)

    def test_get_read_status(self):
        """조회 여부 확인 테스트"""
        self.assertFalse(ReadService.get_read_status(self.other_user, self.post))
        
        PostRead.objects.create(user=self.other_user, post=self.post)
        self.assertTrue(ReadService.get_read_status(self.other_user, self.post))


class PostServiceTests(TestCase):
    @freeze_time("2024-03-15 12:00:00")
    def setUp(self):
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
        self.draft_post = Post.objects.create(
            blog=self.blog,
            author=self.user,
            title='Draft Post',
            content='Draft Content',
            status='draft'
        )

    def test_get_user_posts(self):
        """사용자 게시글 목록 조회 테스트"""
        # 작성자 조회 (draft 포함)
        posts = PostService.get_user_posts(self.user.username, user=self.user)
        self.assertEqual(posts.count(), 2)

        # 다른 사용자 조회 (published만)
        posts = PostService.get_user_posts(self.user.username, user=self.other_user)
        self.assertEqual(posts.count(), 1)
        self.assertEqual(posts.first(), self.post)

    def test_get_post_detail(self):
        """게시글 상세 조회 테스트"""
        # published 게시글
        post = PostService.get_post_detail(self.user.username, self.post.slug)
        self.assertEqual(post, self.post)

        # draft 게시글 (작성자)
        post = PostService.get_post_detail(
            self.user.username, 
            self.draft_post.slug,
            user=self.user
        )
        self.assertEqual(post, self.draft_post)

        # draft 게시글 (다른 사용자)
        with self.assertRaises(Post.DoesNotExist):
            PostService.get_post_detail(
                self.user.username,
                self.draft_post.slug,
                user=self.other_user
            )

    def test_create_post(self):
        """게시글 생성 테스트"""
        post = PostService.create_post(
            user=self.user,
            title="New Post",
            content="New Content",
            status="published",
            tags=["tag1", "tag2"]
        )
        self.assertEqual(post.title, "New Post")
        self.assertEqual(post.content, "New Content")
        self.assertEqual(post.status, "published")
        self.assertEqual(list(post.tags.names()), ["tag1", "tag2"])

    def test_update_post(self):
        """게시글 수정 테스트"""
        updated_post = PostService.update_post(
            post=self.post,
            title="Updated Title",
            content="Updated Content",
            status="draft",
            tags=["tag3"]
        )
        self.assertEqual(updated_post.title, "Updated Title")
        self.assertEqual(updated_post.content, "Updated Content")
        self.assertEqual(updated_post.status, "draft")
        self.assertEqual(list(updated_post.tags.names()), ["tag3"]) 