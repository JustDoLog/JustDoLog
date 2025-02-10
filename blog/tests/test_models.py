from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from blog.models import Blog, Post, PostLike, PostRead
from taggit.models import Tag
from django.utils import timezone
import datetime

User = get_user_model()

class BlogModelTest(TestCase):
    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.blog = self.user.blog  # signal에 의해 자동 생성됨

    def test_auto_blog_creation(self):
        """새 사용자 생성 시 Blog 자동 생성 테스트"""
        # 새로운 사용자 생성
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )

        # Blog 인스턴스가 자동으로 생성되었는지 확인
        self.assertTrue(hasattr(new_user, 'blog'))
        self.assertIsInstance(new_user.blog, Blog)
        
        # Blog의 owner가 올바르게 설정되었는지 확인
        self.assertEqual(new_user.blog.owner, new_user)
        
        # 기본값 확인
        self.assertEqual(new_user.blog.title, f"Just Do {new_user.username}'s Blog")
        self.assertEqual(new_user.blog.description, "")

    def test_blog_fields(self):
        """Blog 필드 및 str 메소드 테스트"""
        # 필드 값 업데이트
        self.blog.title = "Test Blog"
        self.blog.description = "Test Description"
        self.blog.save()

        # 필드 값 검증
        self.assertEqual(self.blog.title, "Test Blog")
        self.assertEqual(self.blog.description, "Test Description")
        self.assertIsInstance(self.blog.created_at, datetime.datetime)
        self.assertIsInstance(self.blog.updated_at, datetime.datetime)
        
        # str 메소드 검증
        self.assertEqual(str(self.blog), "Test Blog")

        # updated_at이 수정 시 업데이트되는지 확인
        old_updated_at = self.blog.updated_at
        self.blog.title = "Updated Blog"
        self.blog.save()
        self.assertGreater(self.blog.updated_at, old_updated_at)

    def test_get_tags_with_count(self):
        """get_tags_with_count 메소드 테스트"""
        # 게시글 생성 및 태그 추가
        post1 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Post 1",
            content="Content 1",
            status="published"
        )
        post2 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Post 2",
            content="Content 2",
            status="published"
        )
        post3 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Post 3",
            content="Content 3",
            status="draft"  # 비공개 게시글
        )

        # 태그 추가
        post1.tags.add("python", "django")
        post2.tags.add("python", "testing")
        post3.tags.add("python")  # draft 게시글의 태그

        # get_tags_with_count 결과 확인
        tags_with_count = self.blog.get_tags_with_count()
        
        # 태그별 게시글 수 확인 (draft 게시글 제외)
        tag_counts = {tag.name: tag.posts_count for tag in tags_with_count}
        self.assertEqual(tag_counts['python'], 2)  # published 상태의 게시글만 카운트
        self.assertEqual(tag_counts['django'], 1)
        self.assertEqual(tag_counts['testing'], 1)

        # 정렬 순서 확인 (게시글 수 내림차순, 같은 경우 이름 오름차순)
        tag_names = [tag.name for tag in tags_with_count]
        self.assertEqual(tag_names, ['python', 'django', 'testing'])

    def test_blog_owner_cascade_delete(self):
        """사용자 삭제 시 블로그도 함께 삭제되는지 테스트"""
        blog_id = self.blog.id
        self.user.delete()
        
        # 블로그가 삭제되었는지 확인
        self.assertFalse(Blog.objects.filter(id=blog_id).exists())

    def test_blog_related_posts(self):
        """블로그와 게시글 관계 테스트"""
        # 게시글 생성
        post1 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Post 1",
            content="Content 1",
            status="published"
        )
        post2 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Post 2",
            content="Content 2",
            status="draft"
        )

        # related_name을 통한 역참조 확인
        self.assertEqual(self.blog.posts.count(), 2)
        self.assertIn(post1, self.blog.posts.all())
        self.assertIn(post2, self.blog.posts.all())

        # 상태별 게시글 필터링
        published_posts = self.blog.posts.filter(status="published")
        draft_posts = self.blog.posts.filter(status="draft")
        self.assertEqual(published_posts.count(), 1)
        self.assertEqual(draft_posts.count(), 1)

class PostModelTest(TestCase):
    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.blog = self.user.blog

    def test_post_slug_creation(self):
        """신규 포스트 생성 시 slug 자동 생성 테스트"""
        # 기본 포스트 생성
        post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Sample Title",
            content="Sample Content"
        )
        self.assertEqual(post.slug, "sample-title")

        # 동일한 제목으로 새 포스트 생성
        post2 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Sample Title",
            content="Another Content"
        )
        self.assertEqual(post2.slug, "sample-title-1")

        # 한 번 더 동일한 제목으로 생성
        post3 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Sample Title",
            content="Yet Another Content"
        )
        self.assertEqual(post3.slug, "sample-title-2")

        # 한글 제목 테스트
        post4 = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="테스트 제목",
            content="테스트 내용"
        )
        self.assertEqual(post4.slug, "테스트-제목")

    def test_post_slug_update(self):
        """포스트 수정 시 slug 업데이트 테스트"""
        # 포스트 생성
        post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Original Title",
            content="Original Content"
        )
        original_slug = post.slug

        # title 외의 필드 수정 시 slug 유지
        post.content = "Updated Content"
        post.save()
        self.assertEqual(post.slug, original_slug)

        # title 수정 시 slug 변경
        post.title = "Updated Title"
        post.save()
        self.assertEqual(post.slug, "updated-title")

        # 이미 존재하는 slug로 변경 시도
        another_post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Another Title",
            content="Another Content"
        )
        another_post.title = "Updated Title"
        another_post.save()
        self.assertEqual(another_post.slug, "updated-title-1")

    def test_thumbnail_extraction(self):
        """HTML content에서 썸네일 추출 테스트"""
        # 이미지가 있는 content로 포스트 생성
        post_with_image = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Post with Image",
            content='<p>Some text</p><img src="https://example.com/image.jpg"><p>More text</p>'
        )
        self.assertEqual(post_with_image.thumbnail, "https://example.com/image.jpg")

        # 이미지가 없는 content로 포스트 생성
        post_without_image = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Post without Image",
            content='<p>Just text content</p>'
        )
        self.assertIsNone(post_without_image.thumbnail)

        # content 업데이트로 이미지 추가
        post_without_image.content = '<img src="https://example.com/new-image.jpg"><p>Updated content</p>'
        post_without_image.save()
        self.assertEqual(post_without_image.thumbnail, "https://example.com/new-image.jpg")

        # content 업데이트로 이미지 제거
        post_with_image.content = '<p>No more images</p>'
        post_with_image.save()
        self.assertIsNone(post_with_image.thumbnail)

    def test_post_basic_fields(self):
        """Post 기본 필드 및 관계 테스트"""
        # 기본 포스트 생성
        post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Test Post",
            content="Test Content"
        )

        # 기본값 검증
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.blog, self.blog)
        self.assertEqual(post.status, "draft")  # 기본 상태
        self.assertEqual(post.likes, 0)
        self.assertEqual(post.views, 0)
        self.assertIsInstance(post.created_at, datetime.datetime)
        self.assertIsInstance(post.updated_at, datetime.datetime)
        self.assertIsNone(post.search_vector)  # 기본적으로 null

        # str 메소드 검증
        self.assertEqual(str(post), "Test Post")

        # updated_at 자동 업데이트 검증
        old_updated_at = post.updated_at
        post.content = "Updated content"
        post.save()
        self.assertGreater(post.updated_at, old_updated_at)

    def test_post_status_transitions(self):
        """Post 상태 변경 테스트"""
        post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Test Post",
            content="Test Content"
        )

        # draft -> published
        post.status = "published"
        post.save()
        self.assertEqual(post.status, "published")

        # published -> draft
        post.status = "draft"
        post.save()
        self.assertEqual(post.status, "draft")

        # 잘못된 상태값 설정 시도
        with self.assertRaises(ValueError):
            post.status = "invalid_status"
            post.save()

    def test_post_cascade_delete(self):
        """연관 객체 삭제 시 Post 삭제 테스트"""
        post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="Test Post",
            content="Test Content"
        )
        post_id = post.id

        # 사용자 삭제 시 포스트도 삭제
        self.user.delete()
        self.assertFalse(Post.objects.filter(id=post_id).exists())

        # 다른 사용자의 포스트 생성
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        other_post = Post.objects.create(
            author=other_user,
            blog=other_user.blog,
            title="Other Post",
            content="Other Content"
        )
        other_post_id = other_post.id

        # 블로그 삭제 시 포스트도 삭제
        other_user.blog.delete()
        self.assertFalse(Post.objects.filter(id=other_post_id).exists())

class PostLikeModelTest(TestCase):
    def setUp(self):
        """테스트 데이터 설정"""
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
            author=self.user,
            blog=self.blog,
            title="Test Post",
            content="Test Content"
        )

    def test_post_like_creation(self):
        """정상적인 좋아요 생성 테스트"""
        # 좋아요 생성
        like = PostLike.objects.create(user=self.user, post=self.post)
        
        # 기본 필드 검증
        self.assertEqual(like.user, self.user)
        self.assertEqual(like.post, self.post)
        self.assertIsInstance(like.created_at, datetime.datetime)

        # str 메소드 검증 (필요한 경우)
        expected_str = f"{self.user.username} likes {self.post.title}"
        self.assertEqual(str(like), expected_str)

    def test_post_like_ordering(self):
        """좋아요 정렬 순서 테스트"""
        # 시간 차이를 두고 여러 좋아요 생성
        like1 = PostLike.objects.create(user=self.user, post=self.post)
        like2 = PostLike.objects.create(user=self.other_user, post=self.post)

        # 정렬 순서 확인 (최신순)
        likes = PostLike.objects.all()
        self.assertEqual(likes[0], like2)
        self.assertEqual(likes[1], like1)

    def test_duplicate_post_like_prevention(self):
        """중복 좋아요 방지 테스트"""
        # 첫 번째 좋아요 생성
        PostLike.objects.create(user=self.user, post=self.post)

        # 동일한 user-post 조합으로 두 번째 좋아요 시도
        with self.assertRaises(IntegrityError):
            PostLike.objects.create(user=self.user, post=self.post)

    def test_post_like_cascade_delete(self):
        """연관 객체 삭제 시 좋아요 삭제 테스트"""
        like = PostLike.objects.create(user=self.user, post=self.post)
        like_id = like.id

        # 포스트 삭제 시 좋아요도 삭제
        self.post.delete()
        self.assertFalse(PostLike.objects.filter(id=like_id).exists())

        # 새 포스트와 좋아요 생성
        new_post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="New Post",
            content="New Content"
        )
        new_like = PostLike.objects.create(user=self.user, post=new_post)
        new_like_id = new_like.id

        # 사용자 삭제 시 좋아요도 삭제
        self.user.delete()
        self.assertFalse(PostLike.objects.filter(id=new_like_id).exists())


class PostReadModelTest(TestCase):
    def setUp(self):
        """테스트 데이터 설정"""
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
            author=self.user,
            blog=self.blog,
            title="Test Post",
            content="Test Content"
        )

    def test_post_read_creation(self):
        """정상적인 읽음 기록 생성 테스트"""
        read = PostRead.objects.create(user=self.user, post=self.post)

        self.assertEqual(read.user, self.user)
        self.assertEqual(read.post, self.post)
        expected_str = f"{self.user.username} read {self.post.title}"
        self.assertEqual(str(read), expected_str)
        
        # created_at과 updated_at이 거의 동일한 시점에 생성되었는지 확인
        time_difference = abs(read.updated_at.timestamp() - read.created_at.timestamp())
        self.assertLess(time_difference, 1)  # 1초 미만의 차이

    def test_post_read_ordering(self):
        """읽음 기록 정렬 순서 테스트"""
        # 시간 차이를 두고 여러 읽음 기록 생성
        read1 = PostRead.objects.create(user=self.user, post=self.post)
        read2 = PostRead.objects.create(user=self.other_user, post=self.post)

        # 정렬 순서 확인 (최신 updated_at 순)
        reads = PostRead.objects.all()
        self.assertEqual(reads[0], read2)
        self.assertEqual(reads[1], read1)

    def test_duplicate_post_read_prevention(self):
        """중복 읽음 기록 방지 테스트"""
        # 첫 번째 읽음 기록 생성
        PostRead.objects.create(user=self.user, post=self.post)

        # 동일한 user-post 조합으로 두 번째 읽음 기록 시도
        with self.assertRaises(IntegrityError):
            PostRead.objects.create(user=self.user, post=self.post)

    def test_post_read_update(self):
        """읽음 기록 업데이트 테스트"""
        # 읽음 기록 생성
        read = PostRead.objects.create(user=self.user, post=self.post)
        original_updated_at = read.updated_at

        # 시간이 지난 후 업데이트
        read.save()  # 단순 저장만으로도 updated_at이 갱신되어야 함
        
        # updated_at 갱신 확인
        read.refresh_from_db()
        self.assertGreater(read.updated_at, original_updated_at)
        self.assertNotEqual(read.updated_at, read.created_at)

    def test_post_read_cascade_delete(self):
        """연관 객체 삭제 시 읽음 기록 삭제 테스트"""
        read = PostRead.objects.create(user=self.user, post=self.post)
        read_id = read.id

        # 포스트 삭제 시 읽음 기록도 삭제
        self.post.delete()
        self.assertFalse(PostRead.objects.filter(id=read_id).exists())

        # 새 포스트와 읽음 기록 생성
        new_post = Post.objects.create(
            author=self.user,
            blog=self.blog,
            title="New Post",
            content="New Content"
        )
        new_read = PostRead.objects.create(user=self.user, post=new_post)
        new_read_id = new_read.id

        # 사용자 삭제 시 읽음 기록도 삭제
        self.user.delete()
        self.assertFalse(PostRead.objects.filter(id=new_read_id).exists())
