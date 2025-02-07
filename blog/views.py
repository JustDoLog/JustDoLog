from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
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


class UserPostDetailView(PostGetObjectMixin, DetailView):
    model = Post
    template_name = "blog/user_post_detail.html"
    context_object_name = "post"


class UserPostCreateView(LoginRequiredMixin, BlogOwnerRequiredMixin, CreateView):
    model = Post
    template_name = "blog/user_post_create.html"
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
    template_name = "blog/user_post_update.html"
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
