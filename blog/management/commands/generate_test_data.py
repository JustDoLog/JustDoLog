import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from faker import Faker
from user.models import CustomUser
from blog.models import Post, PostLike, PostRead
from django.contrib.auth import get_user_model
import os
from django.core.files import File

fake = Faker(["ko_KR"])
User = get_user_model()


class Command(BaseCommand):
    help = "테스트용 데이터를 생성합니다."

    def __init__(self):
        super().__init__()
        self.fake = Faker('ko_KR')  # 한국어 로케일 설정
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

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=100, help="생성할 사용자 수")

    def generate_post_content(self):
        """HTML 형식의 블로그 포스트 컨텐츠 생성"""
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

        return template.format(**placeholders)

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
            with transaction.atomic():
                # 사용자 생성
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

                self.stdout.write(
                    self.style.SUCCESS(f"{len(users)}명의 사용자를 생성했습니다.")
                )

                # 태그 리스트 생성 (실제 태그 객체는 생성하지 않음)
                tags = self.generate_tags()
                self.stdout.write(
                    self.style.SUCCESS(f"{len(tags)}개의 태그를 준비했습니다.")
                )

                # 포스트 생성
                posts = []
                for user in users:
                    num_posts = random.randint(10, 100)
                    
                    for _ in range(num_posts):
                        created_at = self.fake.date_time_between(
                            start_date="-1y",
                            end_date="now",
                            tzinfo=timezone.get_current_timezone(),
                        )
                        
                        post = Post.objects.create(
                            author=user,
                            blog=user.blog,
                            title=self.fake.sentence(),
                            content=self.generate_post_content(),
                            created_at=created_at,
                            updated_at=created_at,
                            views=random.randint(0, 1000),
                            likes=0,
                            status='published'
                        )

                        # 랜덤하게 0-5개의 태그 추가
                        num_tags = random.randint(0, 5)
                        if num_tags > 0:
                            selected_tags = random.sample(tags, num_tags)
                            post.tags.add(*selected_tags)  # django-taggit의 방식으로 태그 추가

                        posts.append(post)

                    self.stdout.write(
                        f"사용자 {user.username}의 {num_posts}개 포스트를 생성했습니다."
                    )

                self.stdout.write(
                    self.style.SUCCESS(f"총 {len(posts)}개의 포스트를 생성했습니다.")
                )

                # 좋아요와 조회 기록 생성
                for user in users:
                    # 각 사용자가 랜덤하게 10~30개의 포스트에 좋아요
                    available_posts = [
                        p for p in posts if p.author != user
                    ]  # 자신의 글은 제외
                    if available_posts:  # 좋아요할 포스트가 있는 경우에만
                        num_likes = min(random.randint(10, 30), len(available_posts))
                        posts_to_like = random.sample(available_posts, num_likes)
                        for post in posts_to_like:
                            PostLike.objects.create(user=user, post=post)
                            post.likes += 1
                            post.save()

                    # 각 사용자가 랜덤하게 20~50개의 포스트를 읽음
                    num_reads = min(random.randint(20, 50), len(posts))
                    posts_to_read = random.sample(posts, num_reads)
                    for post in posts_to_read:
                        PostRead.objects.create(
                            user=user,
                            post=post,
                            created_at=self.fake.date_time_between(
                                start_date=post.created_at,
                                end_date="now",
                                tzinfo=timezone.get_current_timezone(),
                            ),
                        )
                        post.views += 1
                        post.save()

                self.stdout.write(
                    self.style.SUCCESS("좋아요와 조회 기록을 생성했습니다.")
                )
                self.stdout.write(
                    self.style.SUCCESS("테스트 데이터 생성이 완료되었습니다!")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"오류가 발생했습니다: {str(e)}"))
            raise

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
