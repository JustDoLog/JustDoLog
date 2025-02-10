from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Follow
from blog.models import Blog
import json
import os

User = get_user_model()


class UserViewTests(TestCase):
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
        # Blog 객체 생성 (signal로 자동 생성되지만 명시적으로 생성)
        self.user_blog = Blog.objects.get(owner=self.user)
        self.other_blog = Blog.objects.get(owner=self.other_user)
        
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view(self):
        """프로필 뷰 테스트"""
        # 인증된 사용자의 프로필 접근
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/profile.html')
        self.assertEqual(response.context['user'], self.user)

        # 다른 사용자의 프로필 접근
        response = self.client.get(
            reverse('profile') + f'?username={self.other_user.username}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user)  # 로그인한 사용자 정보

    def test_profile_edit_view(self):
        """프로필 수정 뷰 테스트"""
        # GET 요청 테스트
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/profile_edit.html')

        # POST 요청 테스트 - 프로필 정보 업데이트
        image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        image = SimpleUploadedFile(
            'test.gif',
            image_content,
            content_type='image/gif'
        )

        data = {
            'github_url': 'https://github.com/testuser',
            'twitter_url': 'https://twitter.com/testuser',
            'facebook_url': 'https://facebook.com/testuser',
            'homepage_url': 'https://example.com',
            'blog_title': 'Test Blog',
            'blog_description': 'Test Description',
            'profile_image': image
        }

        response = self.client.post(reverse('profile_edit'), data)
        self.assertEqual(response.status_code, 302)  # 리다이렉트 확인
        self.assertRedirects(response, reverse('profile'))
        
        # 업데이트된 사용자 정보 확인
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.github_url, data['github_url'])
        self.assertEqual(updated_user.twitter_url, data['twitter_url'])
        self.assertEqual(updated_user.facebook_url, data['facebook_url'])
        self.assertEqual(updated_user.homepage_url, data['homepage_url'])
        self.assertTrue(updated_user.profile_image)
        
        # 블로그 정보 확인
        self.assertEqual(updated_user.blog.title, data['blog_title'])
        self.assertEqual(updated_user.blog.description, data['blog_description'])

    def test_account_delete_view(self):
        """계정 삭제 뷰 테스트"""
        # GET 요청 테스트
        response = self.client.get(reverse('account_delete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/account_delete.html')

        # POST 요청 테스트 - 계정 삭제
        response = self.client.post(reverse('account_delete'))
        self.assertEqual(response.status_code, 302)  # 리다이렉트 확인
        self.assertRedirects(response, reverse('trending_day'))  # 트렌딩 페이지로 리다이렉트

        # 사용자가 실제로 삭제되었는지 확인
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.user.id)

    def test_follow_user_view(self):
        """팔로우 뷰 테스트"""
        # 팔로우 요청
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username}),
            HTTP_HX_REQUEST='true'  # HTMX 요청 헤더 추가
        )
        self.assertEqual(response.status_code, 200)
        
        # 팔로우 관계 확인
        self.assertTrue(
            Follow.objects.filter(
                follower=self.user,
                following=self.other_user
            ).exists()
        )
        
        # 응답에 '팔로잉' 텍스트가 포함되어 있는지 확인
        self.assertIn('팔로잉', response.content.decode())

        # 언팔로우 요청
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username}),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        
        # 팔로우 관계가 삭제되었는지 확인
        self.assertFalse(
            Follow.objects.filter(
                follower=self.user,
                following=self.other_user
            ).exists()
        )
        
        # 응답에 '팔로우' 텍스트가 포함되어 있는지 확인
        self.assertIn('팔로우', response.content.decode())

    def test_unauthenticated_access(self):
        """인증되지 않은 사용자 접근 테스트"""
        # 로그아웃
        self.client.logout()

        # 프로필 편집 페이지 접근 시도
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 302)  # 리다이렉트
        self.assertTrue(response.url.startswith(reverse('account_login')))

        # 계정 삭제 페이지 접근 시도
        response = self.client.get(reverse('account_delete'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('account_login')))

        # 팔로우 기능 사용 시도
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username}),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 302)

    def test_self_follow_prevention(self):
        """자기 자신 팔로우 방지 테스트"""
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.user.username}),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 400)  # Bad Request

    def test_invalid_profile_edit(self):
        """잘못된 프로필 수정 테스트"""
        # 잘못된 URL 형식으로 프로필 수정 시도
        data = {
            'github_url': 'not-a-url',
            'twitter_url': 'not-a-url',
            'facebook_url': 'not-a-url',
            'homepage_url': 'not-a-url'
        }

        response = self.client.post(reverse('profile_edit'), data)
        self.assertEqual(response.status_code, 302)  # 리다이렉트 (실패해도 리다이렉트됨)

    def test_nonexistent_user_profile(self):
        """존재하지 않는 사용자 프로필 접근 테스트"""
        response = self.client.get(
            reverse('profile') + '?username=nonexistentuser'
        )
        self.assertEqual(response.status_code, 200)  # 404 대신 200 반환 (메인 프로필로 폴백)

    def test_htmx_follow_response(self):
        """HTMX 팔로우 응답 테스트"""
        # 팔로우 요청
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username}),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        
        # 응답 내용에 '팔로잉' 텍스트가 포함되어 있는지 확인
        self.assertIn('팔로잉', response.content.decode())

        # 언팔로우 요청
        response = self.client.post(
            reverse('follow_user', kwargs={'username': self.other_user.username}),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        
        # 응답 내용에 '팔로우' 텍스트가 포함되어 있는지 확인
        self.assertIn('팔로우', response.content.decode())

    def tearDown(self):
        """테스트 후 cleanup"""
        # 업로드된 이미지 파일 정리
        if self.user.profile_image:
            if os.path.isfile(self.user.profile_image.path):
                os.remove(self.user.profile_image.path)
