from django.views.generic import DetailView, CreateView, UpdateView, DeleteView, ListView
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import uuid
from datetime import datetime
from .models import Blog, Post
from user.models import CustomUser


class BlogOwnerRequiredMixin(UserPassesTestMixin):
    """블로그 소유자 확인 믹스인"""

    def test_func(self):
        blog_owner = get_object_or_404(CustomUser, username=self.kwargs["username"])
        return self.request.user == blog_owner


class PostGetObjectMixin:
    """Post 객체 조회 믹스인"""

    def get_object(self):
        return get_object_or_404(
            Post,
            blog__owner__username=self.kwargs["username"],
            slug=self.kwargs["slug"],
        )


class UserBlogMainView(DetailView):
    model = Blog
    template_name = "blog/user_blog_main.html"
    context_object_name = "blog"

    def get_object(self):
        user = get_object_or_404(CustomUser, username=self.kwargs["username"])
        return get_object_or_404(Blog, owner=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["posts"] = context["blog"].posts.filter(status="published").order_by("-created_at")
        context["is_owner"] = self.request.user == context["blog"].owner
        return context


class UserPostDetailView(PostGetObjectMixin, DetailView):
    model = Post
    template_name = "blog/user_post_detail.html"
    context_object_name = "post"

    def get_object(self):
        post = super().get_object()
        # draft 상태의 글은 작성자만 볼 수 있음
        if post.status == "draft" and post.blog.owner != self.request.user:
            raise Http404("이 글을 볼 수 있는 권한이 없습니다.")
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_owner"] = self.request.user == context["post"].blog.owner
        context["is_following"] = False
        if self.request.user.is_authenticated:
            context["is_following"] = self.request.user.following.filter(following=context["post"].blog.owner).exists()
        return context


class UserPostCreateView(LoginRequiredMixin, BlogOwnerRequiredMixin, CreateView):
    model = Post
    template_name = "blog/user_post_form.html"
    fields = ["title", "content", "status"]

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.blog = self.request.user.blog
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "user_post_detail",
            kwargs={"username": self.request.user.username, "slug": self.object.slug},
        )


class UserPostUpdateView(
    LoginRequiredMixin, BlogOwnerRequiredMixin, PostGetObjectMixin, UpdateView
):
    model = Post
    template_name = "blog/user_post_form.html"
    fields = ["title", "content", "status"]

    def get_success_url(self):
        return reverse(
            "user_post_detail",
            kwargs={"username": self.request.user.username, "slug": self.object.slug},
        )


class UserPostDeleteView(
    LoginRequiredMixin, BlogOwnerRequiredMixin, PostGetObjectMixin, DeleteView
):
    model = Post
    template_name = "blog/user_post_delete.html"

    def get_success_url(self):
        return reverse(
            "user_blog_main", kwargs={"username": self.request.user.username}
        )


@csrf_exempt
@login_required
def upload_image(request, username):
    # 권한 체크: 현재 사용자가 해당 블로그의 소유자인지 확인
    if request.user.username != username:
        return JsonResponse({"error": "Permission denied"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    print("\n==== Image Upload Debug ====")
    print(f"Files in request: {request.FILES}")

    # TinyMCE는 'images' 키를 사용
    if 'images' not in request.FILES and 'file' not in request.FILES:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    # TinyMCE의 'images' 키나 일반적인 'file' 키 중 하나를 사용
    file = request.FILES.get('images') or request.FILES.get('file')
    print(f"File name: {file.name}")
    print(f"File size: {file.size}")
    print(f"Content type: {file.content_type}")

    if not file.content_type.startswith("image/"):
        return JsonResponse({"error": "File type not supported"}, status=400)

    # 파일 이름 생성 (UUID + 원본 확장자)
    ext = file.name.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    # 연/월 기반 폴더 구조
    today = datetime.now()
    filepath = f"blog/posts/images/{today.year}/{today.month:02d}/{filename}"

    try:
        from django.core.files.storage import default_storage
        from django.conf import settings
        import boto3
        from botocore.client import Config

        print("\n==== Storage Configuration ====")
        print(f"Storage backend: {default_storage.__class__.__name__}")
        print(f"MinIO endpoint URL: {settings.AWS_S3_ENDPOINT_URL}")
        print(f"MinIO bucket name: {settings.AWS_STORAGE_BUCKET_NAME}")
        print(f"AWS access key ID: {settings.AWS_ACCESS_KEY_ID}")
        print(f"Target filepath: {filepath}")
        
        # MinIO 클라이언트 초기화
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
            verify=False
        )

        # 버킷 존재 여부 확인
        try:
            print("\n==== Checking Bucket ====")
            s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            print(f"Bucket '{settings.AWS_STORAGE_BUCKET_NAME}' exists and is accessible")
            
            # 버킷 내용물 나열
            print("\n==== Current Bucket Contents ====")
            response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            for obj in response.get('Contents', []):
                print(f"Found object: {obj['Key']}, Size: {obj['Size']} bytes")
        except Exception as e:
            print(f"Error checking bucket: {str(e)}")
            # 버킷이 없으면 생성 시도
            try:
                print(f"Attempting to create bucket '{settings.AWS_STORAGE_BUCKET_NAME}'")
                s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
                print("Bucket created successfully")
            except Exception as create_error:
                print(f"Error creating bucket: {str(create_error)}")
                return JsonResponse({"error": f"Bucket error: {str(create_error)}"}, status=500)
        
        # 파일 저장
        print("\n==== Saving File ====")
        saved_path = default_storage.save(filepath, file)
        print(f"Saved path: {saved_path}")
        
        # 직접 파일 업로드 시도
        try:
            print("\n==== Direct Upload Attempt ====")
            file.seek(0)  # 파일 포인터를 처음으로 되돌림
            s3_client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                saved_path,
                ExtraArgs={'ContentType': file.content_type}
            )
            print("Direct upload successful")
        except Exception as upload_error:
            print(f"Direct upload error: {str(upload_error)}")
        
        # 파일이 실제로 존재하는지 확인
        try:
            print("\n==== Verifying Upload ====")
            print(f"Checking path: {saved_path}")
            obj = s3_client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=saved_path)
            print(f"File exists in MinIO: Yes")
            print(f"File size in MinIO: {obj['ContentLength']} bytes")
            print(f"File content type: {obj['ContentType']}")
            print(f"File metadata: {obj.get('Metadata', {})}")
        except Exception as e:
            print(f"Error verifying file in MinIO: {str(e)}")
            # 파일 목록 다시 확인
            try:
                print("\n==== Updated Bucket Contents ====")
                response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
                for obj in response.get('Contents', []):
                    print(f"Found object: {obj['Key']}, Size: {obj['Size']} bytes")
            except Exception as list_error:
                print(f"Error listing bucket contents: {str(list_error)}")
            return JsonResponse({"error": f"File verification failed: {str(e)}"}, status=500)
        
        # URL 생성 (버킷명 포함)
        file_url = f"http://{settings.AWS_S3_CUSTOM_DOMAIN}/{settings.AWS_STORAGE_BUCKET_NAME}/{saved_path}"
        print(f"\nGenerated URL: {file_url}")
        
        return JsonResponse({
            "location": file_url,
            "success": True
        })
    except Exception as e:
        import traceback
        print(f"\n==== Error Details ====")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
        return JsonResponse({"error": str(e)}, status=500)


class UserPostDraftListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/user_post_draft_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(
            blog__owner=self.request.user,
            status="draft"
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blog"] = Blog.objects.get(owner=self.request.user)
        return context
