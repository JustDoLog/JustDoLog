from django.urls import path, include
from . import views
from . import api

urlpatterns = [
    path("trending/", views.TrendingPostsView.as_view(), name="trending_day"),
    path("recent/", views.RecentPostsView.as_view(), name="recent_posts"),
    path("liked/", views.LikedPostsView.as_view(), name="liked_posts"),
    path("recent_read/", views.RecentReadPostsView.as_view(), name="recent_read_posts"),
    path("following/", views.FollowingPostsView.as_view(), name="following_posts"),
    path(
        "bloggers/popular/",
        views.PopularBloggersView.as_view(),
        name="popular_bloggers",
    ),
    path("search/", views.SearchView.as_view(), name="search"),
    path("tags/<str:tag_name>/", views.TaggedPostsView.as_view(), name="tagged_posts"),
]

urlpatterns_api_v1 = [
    path("recent", api.recent_posts, name="api_recent_posts"),
]


urlpatterns += [
    path("api/", include((urlpatterns_api_v1, "api-v1"))),
]
