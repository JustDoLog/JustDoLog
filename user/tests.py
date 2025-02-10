from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch
from .models import Follow
import os
import datetime
from django.urls import reverse

User = get_user_model()

class CustomUserTests(TestCase):
    def setUp(self):
        """테스트 사용자 생성"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def tearDown(self):
        """테스트 후 업로드된 파일 정리"""
        if self.user.profile_image:
            # 실제 파일이 존재하는 경우에만 삭제
            if os.path.isfile(self.user.profile_image.path):
                os.remove(self.user.profile_image.path)

    def test_create_user_with_minimal_data(self):
        """최소 정보로 사용자 생성 테스트"""
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertTrue(self.user.check_password(self.user_data['password']))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_user_str_method(self):
        """사용자 문자열 표현 테스트"""
        self.assertEqual(str(self.user), self.user_data['username'])

    def test_empty_profile_fields(self):
        """프로필 필드 기본값 테스트"""
        self.assertEqual(self.user.github_url, '')
        self.assertEqual(self.user.twitter_url, '')
        self.assertEqual(self.user.facebook_url, '')
        self.assertEqual(self.user.homepage_url, '')
        self.assertIsNone(self.user.profile_image.name)

    def test_profile_image_upload(self):
        """프로필 이미지 업로드 테스트"""
        # 테스트용 이미지 파일 생성
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile(
            'test_image.gif',
            image_content,
            content_type='image/gif'
        )

        # 이미지 업로드
        self.user.profile_image = image
        self.user.save()

        # 이미지가 성공적으로 업로드되었는지 확인
        self.assertTrue(self.user.profile_image)
        self.assertTrue(os.path.exists(self.user.profile_image.path))

    def test_profile_image_delete(self):
        """프로필 이미지 삭제 테스트"""
        # 먼저 이미지 업로드
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile(
            'test_image.gif',
            image_content,
            content_type='image/gif'
        )
        self.user.profile_image = image
        self.user.save()

        # 이미지 파일 경로 저장
        image_path = self.user.profile_image.path

        # 이미지 삭제
        self.user.profile_image.delete()
        self.user.save()

        # 이미지가 실제로 삭제되었는지 확인
        self.assertFalse(os.path.exists(image_path))
        self.assertFalse(self.user.profile_image)

    def test_invalid_image_upload(self):
        """잘못된 형식의 파일 업로드 테스트"""
        # 텍스트 파일을 이미지로 위장
        fake_image = SimpleUploadedFile(
            'test.txt',
            b'this is not an image',
            content_type='text/plain'
        )

        # 이미지가 아닌 파일 업로드 시도
        self.user.profile_image = fake_image
        
        # save() 메서드 호출 시 ValidationError가 발생해야 함
        with self.assertRaises(ValidationError):
            self.user.save()

    def test_follow_user(self):
        """사용자 팔로우 테스트"""
        # 다른 사용자 생성
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # 팔로우 관계 생성
        Follow.objects.create(follower=self.user, following=other_user)

        # 팔로우 확인
        self.assertTrue(self.user.following.filter(following=other_user).exists())
        self.assertTrue(other_user.followers.filter(follower=self.user).exists())

    def test_self_follow_prevention(self):
        """자기 자신을 팔로우할 수 없음을 테스트"""
        # 자기 자신을 팔로우 시도
        with self.assertRaises(ValidationError):
            Follow.objects.create(follower=self.user, following=self.user)

    def test_url_fields_validation(self):
        """URL 필드 유효성 검사 테스트"""
        # 유효한 URL
        self.user.github_url = 'https://github.com/username'
        self.user.twitter_url = 'https://twitter.com/username'
        self.user.facebook_url = 'https://facebook.com/username'
        self.user.homepage_url = 'https://example.com'
        self.user.full_clean()  # ValidationError가 발생하지 않아야 함

        # 잘못된 URL 형식
        self.user.github_url = 'not-a-url'
        with self.assertRaises(ValidationError):
            self.user.full_clean()

    def test_large_image_upload(self):
        """큰 이미지 파일 업로드 테스트"""
        # 5MB를 초과하는 이미지 생성
        large_image_content = b'0' * (5 * 1024 * 1024 + 1)  # 5MB + 1byte
        large_image = SimpleUploadedFile(
            'large_image.jpg',
            large_image_content,
            content_type='image/jpeg'
        )

        # 큰 이미지 업로드 시도
        self.user.profile_image = large_image
        
        # ValidationError가 발생해야 함
        with self.assertRaises(ValidationError):
            self.user.save()

    def test_superuser_creation(self):
        """슈퍼유저 생성 테스트"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_active)

    def test_timestamp_fields(self):
        """타임스탬프 필드 테스트"""
        # 생성 시간 검증
        self.assertIsNotNone(self.user.created_at)
        self.assertIsNotNone(self.user.updated_at)
        
        # 수정 시간 갱신 검증
        original_updated_at = self.user.updated_at
        self.user.email = 'new@example.com'
        self.user.save()
        
        self.assertNotEqual(self.user.updated_at, original_updated_at)

    @patch('uuid.uuid4')
    def test_profile_image_path(self, mock_uuid):
        """프로필 이미지 업로드 경로 테스트"""
        mock_uuid.return_value = 'test-uuid'
        image = SimpleUploadedFile('test.jpg', b'', content_type='image/jpeg')
        
        path = self.user.profile_image.field.upload_to(self.user, 'test.jpg')
        
        self.assertEqual(path, 'user/profiles/images/test-uuid.jpg')

    def test_url_validation(self):
        """URL 필드 유효성 검사 테스트"""
        # 유효한 URL 테스트
        valid_urls = {
            'github_url': 'https://github.com/username',
            'twitter_url': 'https://twitter.com/username',
            'facebook_url': 'https://facebook.com/username',
            'homepage_url': 'https://example.com'
        }
        
        for field, url in valid_urls.items():
            setattr(self.user, field, url)
        self.user.full_clean()  # ValidationError가 발생하지 않아야 함
        
        # 잘못된 프로토콜 테스트
        with self.assertRaises(ValidationError):
            self.user.github_url = 'ftp://github.com/username'
            self.user.full_clean()
            
        # 잘못된 URL 형식 테스트
        with self.assertRaises(ValidationError):
            self.user.github_url = 'not-a-url'
            self.user.full_clean()

class FollowTests(TestCase):
    def setUp(self):
        """테스트 사용자 생성"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')

    def test_follow_creation(self):
        """팔로우 관계 생성 테스트"""
        follow = Follow.objects.create(follower=self.user1, following=self.user2)
        
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.following, self.user2)
        self.assertEqual(str(follow), "user1 follows user2")

    def test_follow_unique_constraint(self):
        """팔로우 중복 방지 테스트"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        
        with self.assertRaises(ValidationError):
            Follow.objects.create(follower=self.user1, following=self.user2)

    def test_self_follow_prevention(self):
        """자기 자신을 팔로우할 수 없음을 테스트"""
        with self.assertRaises(ValidationError):
            Follow.objects.create(follower=self.user1, following=self.user1)

    def test_follow_timestamp_fields(self):
        """팔로우 타임스탬프 필드 테스트"""
        follow = Follow.objects.create(follower=self.user1, following=self.user2)
        
        self.assertIsNotNone(follow.created_at)
        self.assertIsNotNone(follow.updated_at)
        
        # 수정 시간 갱신 검증 (이 경우 수정할 필드가 없으므로 save() 호출로 테스트)
        original_updated_at = follow.updated_at
        follow.save()
        
        self.assertNotEqual(follow.updated_at, original_updated_at)

    def test_follow_reverse_relations(self):
        """팔로우 역참조 관계 테스트"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        
        # user1이 팔로우하는 사용자 목록에 user2가 있는지
        self.assertTrue(self.user2 in [follow.following for follow in self.user1.following.all()])
        
        # user2의 팔로워 목록에 user1이 있는지
        self.assertTrue(self.user1 in [follow.follower for follow in self.user2.followers.all()])

    def test_clean_method_call(self):
        """clean 메소드 호출 검증"""
        follow = Follow(follower=self.user1, following=self.user1)
        
        # save() 메소드가 clean()을 호출하는지 검증
        with self.assertRaises(ValidationError) as context:
            follow.save()
        
        self.assertIn("자기 자신을 팔로우할 수 없습니다", str(context.exception))

class UserViewTests(TestCase):
    def setUp(self):
        """테스트 사용자 및 클라이언트 설정"""
        self.client = Client()
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

    def test_profile_view_authentication(self):
        """프로필 뷰 인증 테스트"""
        # 비로그인 상태에서 접근
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # 로그인 페이지로 리다이렉트
        
        # 로그인 후 접근
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/profile.html')

    def test_profile_edit_view(self):
        """프로필 수정 뷰 테스트"""
        self.client.login(username='testuser', password='testpass123')
        
        # GET 요청 테스트
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/profile_edit.html')
        
        # POST 요청 테스트 - 프로필 업데이트
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile(
            'test.gif',
            image_content,
            content_type='image/gif'
        )
        update_data = {
            'github_url': 'https://github.com/testuser',
            'twitter_url': 'https://twitter.com/testuser',
            'facebook_url': 'https://facebook.com/testuser',
            'homepage_url': 'https://example.com',
            'blog_title': 'Test Blog',
            'blog_description': 'Test Description',
            'profile_image': image
        }
        
        response = self.client.post(reverse('profile_edit'), update_data)
        self.assertEqual(response.status_code, 302)  # 리다이렉트 확인
        self.assertRedirects(response, reverse('profile'))
        
        # 데이터가 실제로 업데이트되었는지 확인
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_url, update_data['github_url'])
        self.assertEqual(self.user.twitter_url, update_data['twitter_url'])
        self.assertEqual(self.user.facebook_url, update_data['facebook_url'])
        self.assertEqual(self.user.homepage_url, update_data['homepage_url'])
        self.assertEqual(self.user.blog.title, update_data['blog_title'])
        self.assertEqual(self.user.blog.description, update_data['blog_description'])
        self.assertTrue(self.user.profile_image)

    def test_account_delete_view(self):
        """계정 삭제 뷰 테스트"""
        self.client.login(username='testuser', password='testpass123')
        
        # GET 요청 테스트 - 삭제 확인 페이지
        response = self.client.get(reverse('account_delete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/account_delete.html')
        
        # POST 요청 테스트 - 실제 삭제
        response = self.client.post(reverse('account_delete'))
        self.assertEqual(response.status_code, 302)  # 리다이렉트 확인
        self.assertRedirects(response, reverse('trending_day'))
        
        # 사용자가 실제로 삭제되었는지 확인
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_follow_user_view(self):
        """팔로우 기능 테스트"""
        self.client.login(username='testuser', password='testpass123')
        
        # 팔로우 요청
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username}),
            HTTP_HX_REQUEST='true'  # HTMX 요청 시뮬레이션
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Follow.objects.filter(
                follower=self.user,
                following=self.other_user
            ).exists()
        )
        
        # 언팔로우 요청
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username}),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Follow.objects.filter(
                follower=self.user,
                following=self.other_user
            ).exists()
        )

    def test_self_follow_prevention(self):
        """자기 자신 팔로우 방지 테스트"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.user.username}),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_access(self):
        """비인증 사용자 접근 제한 테스트"""
        # 프로필 뷰
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        
        # 프로필 수정 뷰
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 302)
        
        # 계정 삭제 뷰
        response = self.client.get(reverse('account_delete'))
        self.assertEqual(response.status_code, 302)
        
        # 팔로우 뷰
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username})
        )
        self.assertEqual(response.status_code, 302)

    def tearDown(self):
        """테스트 후 cleanup"""
        # 업로드된 이미지 파일 정리
        if self.user.profile_image:
            if os.path.isfile(self.user.profile_image.path):
                os.remove(self.user.profile_image.path)
