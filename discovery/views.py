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
from blog.models import Post, Blog
from user.models import Follow


class TrendingPostsView(ListView):
    model = Post
    template_name = "discovery/trending_posts.html"
    context_object_name = "posts"
    paginate_by = 10

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
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(status="published").order_by("-created_at")


class LikedPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/liked_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(
            postlike__user=self.request.user, status="published"
        ).order_by("-postlike__created_at")


class RecentReadPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "discovery/recent_read_posts.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(
            postread__user=self.request.user, status="published"
        ).order_by("-postread__updated_at")


class PopularBloggersView(ListView):
    template_name = 'discovery/popular_bloggers.html'
    context_object_name = 'bloggers'

    def get_queryset(self):
        # 최근 30일 동안의 활동을 기준으로 인기 블로거 선정
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        queryset = Blog.objects.annotate(
            # 팔로워 수
            followers_count=Count('owner__followers'),
            # 최근 30일 동안 작성한 게시글 수
            recent_posts_count=Count(
                'posts',
                filter=models.Q(posts__created_at__gte=thirty_days_ago)
            ),
            # 최근 30일 동안 받은 좋아요 수
            recent_likes_count=Count(
                'posts__postlike',
                filter=models.Q(posts__postlike__created_at__gte=thirty_days_ago)
            ),
            # 인기도 점수 계산
            popularity_score=ExpressionWrapper(
                # 팔로워 수 * 2 + 최근 게시글 수 * 3 + 최근 좋아요 수
                F('followers_count') * 2 + F('recent_posts_count') * 3 + F('recent_likes_count'),
                output_field=FloatField()
            )
        ).filter(
            # 최소 1개 이상의 게시글이 있는 블로그만 선정
            posts__isnull=False
        ).distinct().order_by('-popularity_score')[:10]

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
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 팔로잉 수를 컨텍스트에 추가
        context["following_count"] = Follow.objects.filter(
            follower=self.request.user
        ).count()
        return context
