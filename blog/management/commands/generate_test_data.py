import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from faker import Faker
from user.models import CustomUser
from blog.models import Blog, Post, PostLike, PostRead

fake = Faker(["ko_KR"])


class Command(BaseCommand):
    help = "테스트용 데이터를 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=100, help="생성할 사용자 수")
        parser.add_argument(
            "--posts", type=int, default=10, help="사용자당 생성할 포스트 수"
        )

    def handle(self, *args, **options):
        num_users = options["users"]
        posts_per_user = options["posts"]

        self.stdout.write("테스트 데이터 생성을 시작합니다...")

        try:
            with transaction.atomic():
                # 사용자 생성
                users = []
                for i in range(num_users):
                    username = f"test_user_{i+1}"
                    email = f"test{i+1}@example.com"

                    # 이미 존재하는 사용자는 건너뜀
                    if CustomUser.objects.filter(username=username).exists():
                        continue

                    user = CustomUser.objects.create_user(
                        username=username, email=email, password="testpass123"
                    )
                    users.append(user)

                    # Blog는 signal에 의해 자동 생성되므로 description만 업데이트
                    if hasattr(user, "blog"):
                        user.blog.description = fake.text(max_nb_chars=200)
                        user.blog.save()

                self.stdout.write(
                    self.style.SUCCESS(f"{len(users)}명의 사용자를 생성했습니다.")
                )

                # 포스트 생성
                posts = []
                for user in users:
                    for _ in range(posts_per_user):
                        post = Post.objects.create(
                            author=user,
                            blog=user.blog,
                            title=fake.sentence(),
                            content="\n\n".join(
                                [
                                    f"# {fake.sentence()}\n\n{fake.paragraph()}\n\n"  # 마크다운 형식의 제목
                                    f"## {fake.sentence()}\n\n{fake.paragraph()}\n\n"  # 하위 제목
                                    f"- {fake.sentence()}\n- {fake.sentence()}\n- {fake.sentence()}\n\n"  # 리스트
                                    f'```python\n# 예시 코드\ndef hello_world():\n    print("Hello, World!")\n```\n\n'  # 코드 블록
                                    f"{fake.paragraph()}"  # 마지막 단락
                                ]
                            ),
                            status="published",
                            created_at=fake.date_time_between(
                                start_date="-1y",
                                end_date="now",
                                tzinfo=timezone.get_current_timezone(),
                            ),
                        )
                        posts.append(post)

                self.stdout.write(
                    self.style.SUCCESS(f"{len(posts)}개의 포스트를 생성했습니다.")
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
                            created_at=fake.date_time_between(
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
