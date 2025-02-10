from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.base import View
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, F, ExpressionWrapper, FloatField
from django.contrib.postgres.search import SearchQuery
from django.conf import settings
from django.db import models
from datetime import timedelta
from blog.models import Post, Blog, PostLike, PostRead
from user.models import Follow


class TrendingPostsView(ListView):
    model = Post
    template_name = "discovery/trending_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        period = self.request.GET.get("period", "day")
        days = {
            "day": 1,
            "week": 7,
            "month": 30,
            "year": 365
        }.get(period, 1)
        
        return Post.objects.trending(days=days)


class RecentPostsView(ListView):
    model = Post
    template_name = "discovery/recent_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.published().order_by("-created_at")


class LikedPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/liked_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        # PostLike 매니저를 사용하여 사용자의 좋아요 목록 조회
        likes = PostLike.objects.get_user_likes(self.request.user)
        return [like.post for like in likes if like.post.status == "published"]


class RecentReadPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/recent_read_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        # PostRead 매니저를 사용하여 사용자의 최근 읽은 글 목록 조회
        reads = PostRead.objects.get_user_reads(self.request.user)
        return [read.post for read in reads if read.post.status == "published"]


class PopularBloggersView(ListView):
    template_name = 'discovery/popular_bloggers.html'
    context_object_name = 'bloggers'

    def get_queryset(self):
        # 새로운 BlogManager의 popular() 메서드 사용
        queryset = Blog.objects.popular()[:10]

        # 로그인한 사용자의 팔로잉 정보를 prefetch
        if self.request.user.is_authenticated:
            queryset = queryset.prefetch_related(
                models.Prefetch(
                    'owner__followers',
                    queryset=Follow.objects.filter(follower=self.request.user),
                    to_attr='is_followed_by_user'
                )
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # 각 블로거의 팔로잉 상태를 context에 추가
            following_dict = {
                follow.following_id: True 
                for follow in Follow.objects.filter(follower=self.request.user)
            }
            context['following_dict'] = following_dict
        return context


class SearchView(ListView):
    model = Post
    template_name = "discovery/search.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        if not query:
            return Post.objects.none()

        # PostgreSQL FTS 사용 여부 확인
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
            search_query = SearchQuery(query, config="simple")
            return Post.objects.published().filter(
                search_vector=search_query
            ).order_by("-created_at")

        return Post.objects.search(query).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class FollowingPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/following_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        # 현재 사용자가 팔로우하는 사용자들의 ID 목록을 가져옴
        following_users = Follow.objects.filter(
            follower=self.request.user
        ).values_list('following', flat=True)
        
        # 팔로우하는 사용자들의 게시글을 최신순으로 가져옴
        return Post.objects.filter(
            blog__owner__in=following_users,
            status="published"
        ).order_by("-updated_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 팔로잉 수를 컨텍스트에 추가
        context["following_count"] = Follow.objects.filter(
            follower=self.request.user
        ).count()
        return context


class TaggedPostsView(ListView):
    model = Post
    template_name = "discovery/tagged_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        tag_name = self.kwargs.get('tag_name')
        return Post.objects.by_tag(tag_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag_name'] = self.kwargs.get('tag_name')
        return context
