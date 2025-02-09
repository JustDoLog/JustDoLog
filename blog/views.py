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

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    file = request.FILES["file"]
    if not file.content_type.startswith("image/"):
        return JsonResponse({"error": "File type not supported"}, status=400)

    # 파일 이름 생성 (UUID + 원본 확장자)
    ext = file.name.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    # 연/월 기반 폴더 구조 (blog/posts/images/YYYY/MM/)
    today = datetime.now()
    filepath = f"blog/posts/images/{today.year}/{today.month:02d}/{filename}"

    try:
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile

        # MinIO에 파일 저장
        filepath = default_storage.save(filepath, ContentFile(file.read()))
        file_url = default_storage.url(filepath)

        return JsonResponse({"location": file_url})
    except Exception as e:
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
