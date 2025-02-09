from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.base import View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from datetime import timedelta
from blog.models import Post, Blog, PostLike, PostRead
from user.models import CustomUser, Follow
from django.conf import settings


class TrendingPostsView(ListView):
    model = Post
    template_name = "discovery/trending_posts.html"
    context_object_name = "posts"
    paginate_by = 9

    # period query parameter: day, week, month, year
    def get_queryset(self):
        period = self.request.GET.get("period", "day")
        now = timezone.now()

        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:  # year
            start_date = now - timedelta(days=365)

        # TODO: 트렌딩 알고리즘 구현 (현재는 임시로 최신순)
        return Post.objects.filter(
            created_at__gte=start_date, status="published"
        ).order_by("-created_at")


class RecentPostsView(ListView):
    model = Post
    template_name = "discovery/recent_posts.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return Post.objects.filter(status="published").order_by("-created_at")


class LikedPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/liked_posts.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return Post.objects.filter(
            postlike__user=self.request.user, status="published"
        ).order_by("-postlike__created_at")


class RecentReadPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/recent_read_posts.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return Post.objects.filter(
            postread__user=self.request.user, status="published"
        ).order_by("-postread__updated_at")


class PopularBloggersView(ListView):
    model = Blog
    template_name = "discovery/popular_bloggers.html"
    context_object_name = "bloggers"
    paginate_by = 9

    def get_queryset(self):
        # TODO: 인기 블로거 알고리즘 구현 (현재는 임시로 포스트 수 기준)
        return Blog.objects.all().order_by("-posts__count")


class SearchView(ListView):
    model = Post
    template_name = "discovery/search.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        if not query:
            return Post.objects.none()

        # 기본 필터: published 상태인 게시글만
        base_queryset = Post.objects.filter(status="published")

        # PostgreSQL을 사용하는 경우 FTS 사용
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
            search_query = SearchQuery(query, config="simple")
            return base_queryset.filter(search_vector=search_query).order_by(
                "-created_at"
            )

        # SQLite3 등 다른 데이터베이스의 경우 icontains 사용
        return base_queryset.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class FollowingPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/following_posts.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        # 현재 사용자가 팔로우하는 사용자들의 ID 목록을 가져옴
        following_users = Follow.objects.filter(
            follower=self.request.user
        ).values_list('following', flat=True)
        
        # 팔로우하는 사용자들의 게시글을 최신순으로 가져옴
        return Post.objects.filter(
            blog__owner__in=following_users,
            status="published"
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 팔로잉 수를 컨텍스트에 추가
        context["following_count"] = Follow.objects.filter(
            follower=self.request.user
        ).count()
        return context
