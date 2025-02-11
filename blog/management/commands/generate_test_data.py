import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from faker import Faker
from user.models import CustomUser, Follow
from blog.models import Post, PostLike, PostRead
from django.contrib.auth import get_user_model
import os
from django.core.files import File
from datetime import timedelta
import requests
from io import BytesIO
from PIL import Image
import uuid
from pathlib import Path
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import boto3
from botocore.config import Config
import logging

fake = Faker(["ko_KR"])
User = get_user_model()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "테스트용 데이터를 생성합니다."

    def __init__(self, *args, **kwargs):
        self.is_test = kwargs.pop('test_mode', False)  # kwargs에서 test_mode를 꺼내고 제거
        super().__init__(*args, **kwargs)
        self.fake = Faker('ko_KR')
        
        # 테스트 환경이 아닐 때만 MinIO 클라이언트 초기화
        if not self.is_test:
            self._init_minio_client()
        
        # static 폴더의 기본 프로필 이미지 경로
        if settings.DEBUG:
            for static_dir in settings.STATICFILES_DIRS:
                profile_images_dir = os.path.join(static_dir, 'images/default_profile')
                if os.path.exists(profile_images_dir):
                    self.profile_images_dir = profile_images_dir
                    break
        else:
            self.profile_images_dir = os.path.join(settings.STATIC_ROOT, 'images/default_profile')

        # 사용 가능한 프로필 이미지 리스트
        if os.path.exists(self.profile_images_dir):
            self.profile_images = [
                f for f in os.listdir(self.profile_images_dir)
                if f.startswith('profile_') and f.endswith('.jpg')
            ]
        else:
            self.profile_images = []

    def _init_minio_client(self):
        """MinIO 클라이언트 초기화"""
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        try:
            self.s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        except:
            self.s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            logger.info(f"Created bucket: {settings.AWS_STORAGE_BUCKET_NAME}")

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=100, help="생성할 사용자 수")

    def generate_distributed_dates(self):
        """현재 시점 기준으로 포스트 작성일을 분포
        
        Returns:
            timezone.datetime: 생성된 날짜
            
        분포:
            - 일간 (오늘): 30% ± 10%
            - 주간 (1-7일): 30% ± 10%
            - 월간 (8-30일): 25% ± 10%
            - 연간 (31-365일): 15% ± 10%
        """
        now = timezone.now()
        distribution = random.random()
        
        if distribution < 0.30:  # 일간 (30%)
            # 하루 내의 더 자연스러운 분포
            hours = random.triangular(0, 23, 12)  # 정오 근처에 더 많은 포스트
            return now - timedelta(hours=hours)
            
        elif distribution < 0.60:  # 주간 (30%)
            # 최근 날짜에 가중치를 둔 분포
            days = random.triangular(1, 7, 3)  # 주 중반에 더 많은 포스트
            hours = random.uniform(0, 23)
            return now - timedelta(days=days, hours=hours)
            
        elif distribution < 0.85:  # 월간 (25%)
            # 8-30일 사이의 분포
            days = random.triangular(8, 30, 15)  # 월 중반에 더 많은 포스트
            hours = random.uniform(0, 23)
            return now - timedelta(days=days, hours=hours)
            
        else:  # 연간 (15%)
            # 31-365일 사이의 분포
            days = random.triangular(31, 365, 180)  # 연중 중반에 더 많은 포스트
            hours = random.uniform(0, 23)
            return now - timedelta(days=days, hours=hours)

    def calculate_engagement_metrics(self, created_at):
        """작성일에 따른 조회수와 좋아요 수 계산"""
        now = timezone.now()
        days_old = (now - created_at).days
        
        if days_old < 1:  # 오늘 (일간)
            return {
                'views': random.randint(1, 49),
                'likes': random.randint(1, 49)
            }
        elif days_old < 7:  # 이번 주 (주간)
            return {
                'views': random.randint(50, 99),
                'likes': random.randint(50, 99)
            }
        elif days_old < 30:  # 이번 달 (월간)
            return {
                'views': random.randint(100, 299),
                'likes': random.randint(100, 299)
            }
        else:  # 이전 (연간)
            return {
                'views': random.randint(300, 999),
                'likes': random.randint(300, 999)
            }

    def generate_image(self):
        """테스트용 이미지 생성 및 MinIO에 업로드"""
        try:
            # 이미지 생성
            width = random.randint(800, 1200)
            height = random.randint(400, 800)
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
            image = Image.new('RGB', (width, height), color)
            
            # 이미지에 텍스트 추가
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(image)
            text = f"Test Image {width}x{height}"
            draw.text((width/2-100, height/2), text, fill='white')
            
            # BytesIO로 이미지 저장
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            # 파일 경로 생성
            today = timezone.now()
            filename = f"{uuid.uuid4()}.jpg"
            filepath = f"blog/posts/images/{today.year}/{today.month:02d}/{filename}"
            
            # MinIO에 직접 업로드
            logger.info(f"Uploading image to path: {filepath}")
            self.s3_client.upload_fileobj(
                buffer,
                settings.AWS_STORAGE_BUCKET_NAME,
                filepath,
                ExtraArgs={'ContentType': 'image/jpeg'}
            )
            
            # 업로드 확인
            try:
                self.s3_client.head_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=filepath
                )
                logger.info(f"Successfully uploaded image to {filepath}")
            except Exception as e:
                logger.error(f"Failed to verify upload: {str(e)}")
                return None
            
            # 외부 접근용 URL 생성 (localhost 사용)
            public_url = f"http://localhost:9000/{settings.AWS_STORAGE_BUCKET_NAME}/{filepath}"
            logger.info(f"Generated public URL: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"Error generating/uploading image: {str(e)}")
            return None

    def generate_post_content_with_images(self):
        """이미지가 포함된 포스트 컨텐츠 생성"""
        # 테스트 환경에서는 이미지 없이 컨텐츠만 생성
        if self.is_test:
            return f"<p>{self.fake.paragraph()}</p>"
            
        templates = [
            # 템플릿 1: 기술 문서 스타일
            """
            <h2>Introduction</h2>
            <p>{intro}</p>

            <h3>Key Concepts</h3>
            <ul>
                <li>{key_point1}</li>
                <li>{key_point2}</li>
                <li>{key_point3}</li>
            </ul>

            <h3>Detailed Analysis</h3>
            <p>{analysis1}</p>
            <p>{analysis2}</p>

            <h4>Technical Specifications</h4>
            <ol>
                <li>{tech1}</li>
                <li>{tech2}</li>
                <li>{tech3}</li>
            </ol>

            <h3>Implementation</h3>
            <p>{implementation}</p>

            <h2>Conclusion</h2>
            <p>{conclusion}</p>
            """,
            # 템플릿 2: 에세이 스타일
            """
            <h2>Overview</h2>
            <p>{intro}</p>

            <h3>Background</h3>
            <p>{background1}</p>
            <p>{background2}</p>

            <h3>Main Points</h3>
            <ul>
                <li>{point1}</li>
                <li>{point2}</li>
                <li>{point3}</li>
                <li>{point4}</li>
            </ul>

            <h3>Discussion</h3>
            <p>{discussion1}</p>
            <p>{discussion2}</p>

            <h2>Final Thoughts</h2>
            <p>{conclusion}</p>
            """
        ]
        
        template = random.choice(templates)
        
        # 0-3개의 이미지 생성 및 삽입
        num_images = random.randint(0, 3)
        image_sections = []
        for _ in range(num_images):
            image_url = self.generate_image()
            image_sections.append(f'<img src="{image_url}" alt="테스트 이미지">')
        
        # 템플릿의 각 플레이스홀더를 Lorem Ipsum 텍스트로 채움
        placeholders = {
            'intro': self.fake.paragraph(nb_sentences=4),
            'key_point1': self.fake.sentence(),
            'key_point2': self.fake.sentence(),
            'key_point3': self.fake.sentence(),
            'analysis1': self.fake.paragraph(nb_sentences=3),
            'analysis2': self.fake.paragraph(nb_sentences=3),
            'tech1': self.fake.sentence(),
            'tech2': self.fake.sentence(),
            'tech3': self.fake.sentence(),
            'implementation': self.fake.paragraph(nb_sentences=4),
            'conclusion': self.fake.paragraph(nb_sentences=3),
            'background1': self.fake.paragraph(nb_sentences=3),
            'background2': self.fake.paragraph(nb_sentences=3),
            'point1': self.fake.sentence(),
            'point2': self.fake.sentence(),
            'point3': self.fake.sentence(),
            'point4': self.fake.sentence(),
            'discussion1': self.fake.paragraph(nb_sentences=4),
            'discussion2': self.fake.paragraph(nb_sentences=4),
        }
        
        content = template.format(**placeholders)
        
        # 랜덤한 위치에 이미지 삽입
        if image_sections:
            paragraphs = content.split('\n')
            for img in image_sections:
                insert_position = random.randint(1, len(paragraphs)-1)
                paragraphs.insert(insert_position, img)
            content = '\n'.join(paragraphs)
        
        return content

    def generate_tags(self):
        """100개의 태그 생성"""
        tags = []
        # 기술 관련 태그
        tech_tags = ['Python', 'JavaScript', 'React', 'Django', 'Vue.js', 'Docker', 'AWS', 'Git', 
                    'Database', 'API', 'Frontend', 'Backend', 'DevOps', 'Security', 'Testing']
        # 일반적인 태그
        common_tags = ['Tutorial', 'Guide', 'Tips', 'Best Practices', 'Review', 'How-to', 
                      'Learning', 'Career', 'Project', 'Case Study']
        
        # 기본 태그들로 시작
        tags.extend(tech_tags)
        tags.extend(common_tags)
        
        # 나머지는 Faker로 생성
        while len(tags) < 100:
            tag = self.fake.word()
            if tag not in tags:
                tags.append(tag)
        
        return tags

    def handle(self, *args, **options):
        num_users = options["users"]
        self.stdout.write("테스트 데이터 생성을 시작합니다...")

        try:
            # 1. 사용자 생성 (별도 트랜잭션)
            with transaction.atomic():
                users = self.create_users(num_users)
                self.stdout.write(self.style.SUCCESS(f"{len(users)}명의 사용자를 생성했습니다."))

            # 2. 포스트 생성 (배치 처리)
            posts = []
            for i in range(0, len(users), 10):  # 10명의 사용자씩 처리
                user_batch = users[i:i+10]
                with transaction.atomic():
                    batch_posts = self.create_posts(user_batch)
                    posts.extend(batch_posts)
                    self.stdout.write(f"사용자 {i+1}-{i+len(user_batch)}의 포스트 생성 완료")

            # 3. 팔로우 관계 생성 (별도 트랜잭션)
            with transaction.atomic():
                self.generate_follow_relationships(users)
                self.stdout.write("팔로우 관계 생성 완료")

            # 4. 좋아요와 조회 기록 생성 (배치 처리)
            for i in range(0, len(users), 5):  # 5명의 사용자씩 처리
                user_batch = users[i:i+5]
                with transaction.atomic():
                    self.create_engagement_records(user_batch, posts)
                    self.stdout.write(f"사용자 {i+1}-{i+len(user_batch)}의 활동 기록 생성 완료")

            self.stdout.write(self.style.SUCCESS("테스트 데이터 생성이 완료되었습니다!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"오류가 발생했습니다: {str(e)}"))
            raise

    def create_users(self, num_users):
        """사용자 생성 로직"""
        users = []
        for i in range(num_users):
            # 한글 이름 생성
            name = self.fake.name()
            # 이름에서 공백 제거하고 소문자로 변환하여 username 생성
            username = name.replace(' ', '').lower()
            
            # 이메일 생성
            email_domain = random.choice(['gmail.com', 'naver.com', 'kakao.com', 'daum.net'])
            email = f"{username}@{email_domain}"
            
            # 비밀번호는 username + "123"
            password = f"{username}123"

            # 이미 존재하는 사용자는 건너뜀
            if CustomUser.objects.filter(username=username).exists():
                continue

            user = CustomUser.objects.create_user(
                username=username, email=email, password=password
            )
            users.append(user)

            # Blog는 signal에 의해 자동 생성되므로 description만 업데이트
            if hasattr(user, "blog"):
                user.blog.description = self.fake.text(max_nb_chars=200)
                user.blog.save()

            # 추가 프로필 정보 설정
            user.github_url = f"https://github.com/{username}" if random.random() < 0.7 else ""
            user.twitter_url = f"https://twitter.com/{username}" if random.random() < 0.4 else ""
            user.facebook_url = f"https://facebook.com/{username}" if random.random() < 0.3 else ""
            user.homepage_url = f"https://{username}.github.io" if random.random() < 0.2 else ""
            
            user.save()

            # 랜덤한 프로필 이미지 할당
            self.assign_random_profile_image(user)

        return users

    def create_posts(self, users):
        """포스트 생성 로직"""
        posts = []
        for user in users:
            num_posts = random.randint(10, 100)
            
            for _ in range(num_posts):
                created_at = self.generate_distributed_dates()
                metrics = self.calculate_engagement_metrics(created_at)
                
                # 포스트 생성 (views와 likes는 0으로 시작)
                post = Post.objects.create(
                    author=user,
                    blog=user.blog,
                    title=self.fake.sentence(),
                    content=self.generate_post_content_with_images(),
                    views=0,
                    likes=0,
                    status='published'
                )
                
                # created_at, updated_at 설정
                Post.objects.filter(id=post.id).update(
                    created_at=created_at,
                    updated_at=created_at
                )

                # 목표 메트릭 저장
                post.target_views = metrics['views']
                post.target_likes = metrics['likes']
                posts.append(post)

        return posts

    def create_engagement_records(self, users, all_posts):
        """좋아요와 조회 기록 생성 로직"""
        for user in users:
            likes_to_create = []
            reads_to_create = []
            posts_to_update = []
            
            available_posts = [p for p in all_posts if p.author != user]
            
            if available_posts:
                for post in available_posts:
                    # 좋아요 생성 준비
                    if post.likes < post.target_likes:
                        likes_to_create.append(
                            PostLike(user=user, post=post)
                        )
                        post.likes += 1
                        posts_to_update.append(post)
                    
                    # 조회 기록 생성 준비
                    if post.views < post.target_views:
                        reads_to_create.append(
                            PostRead(
                                user=user,
                                post=post,
                                created_at=self.fake.date_time_between(
                                    start_date=post.created_at,
                                    end_date="now",
                                    tzinfo=timezone.get_current_timezone(),
                                )
                            )
                        )
                        post.views += 1
                        if post not in posts_to_update:
                            posts_to_update.append(post)
            
            # 벌크 생성 및 업데이트
            if likes_to_create:
                PostLike.objects.bulk_create(likes_to_create)
            if reads_to_create:
                PostRead.objects.bulk_create(reads_to_create)
            if posts_to_update:
                Post.objects.bulk_update(posts_to_update, ['views', 'likes'])

    def assign_random_profile_image(self, user):
        """사용자에게 랜덤 프로필 이미지 할당"""
        if not self.profile_images:
            return
        
        image_name = random.choice(self.profile_images)
        image_path = os.path.join(self.profile_images_dir, image_name)
        
        with open(image_path, 'rb') as img_file:
            user.profile_image.save(
                image_name,  # 원본 파일명 유지
                File(img_file),
                save=True
            )

    def generate_follow_relationships(self, users):
        """사용자 간 팔로우 관계 생성"""
        # 포스트 수에 따른 사용자 가중치 계산
        user_weights = {}
        for user in users:
            post_count = Post.objects.filter(author=user).count()
            user_weights[user] = post_count + 1  # 최소 가중치 1 보장
        
        # 각 사용자에 대해 팔로우 관계 생성
        for follower in users:
            # 팔로우할 사용자 수 결정 (5-15명)
            num_to_follow = random.randint(5, 15)
            
            # 자신을 제외한 사용자 목록
            potential_followees = [u for u in users if u != follower]
            
            # 가중치 기반으로 팔로우할 사용자 선택
            weights = [user_weights[u] for u in potential_followees]
            followees = random.choices(
                potential_followees,
                weights=weights,
                k=min(num_to_follow, len(potential_followees))
            )
            
            # 팔로우 관계 생성
            for followee in followees:
                Follow.objects.get_or_create(
                    follower=follower,
                    following=followee
                )
