from django.urls import path
from . import views

urlpatterns = [
    path("trending/", views.TrendingPostsView.as_view(), name="trending_day"),
    path("recent/", views.RecentPostsView.as_view(), name="recent_posts"),
    path("liked/", views.LikedPostsView.as_view(), name="liked_posts"),
    path("recent_read/", views.RecentReadPostsView.as_view(), name="recent_read_posts"),
    path(
        "bloggers/popular/",
        views.PopularBloggersView.as_view(),
        name="popular_bloggers",
    ),
    path("search/", views.SearchView.as_view(), name="search"),
]
