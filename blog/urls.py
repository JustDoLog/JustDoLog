from django.urls import path, re_path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("@<str:username>/", RedirectView.as_view(pattern_name="user_blog_main")),
    path(
        "@<str:username>/posts/",
        views.UserBlogMainView.as_view(),
        name="user_blog_main",
    ),
    path(
        "@<str:username>/posts/new/",
        views.UserPostCreateView.as_view(),
        name="user_post_create",
    ),
    path(
        "@<str:username>/posts/new/upload_image",
        views.upload_image,
        name="upload_image",
    ),
    path(
        "@<str:username>/posts/drafts/",
        views.UserPostDraftListView.as_view(),
        name="user_post_draft",
    ),
    re_path(
        r"^@(?P<username>[^/]+)/posts/(?P<slug>[-\w가-힣]+)/$",
        views.UserPostDetailView.as_view(),
        name="user_post_detail",
    ),
    re_path(
        r"^@(?P<username>[^/]+)/posts/(?P<slug>[-\w가-힣]+)/edit/$",
        views.UserPostUpdateView.as_view(),
        name="user_post_update",
    ),
    re_path(
        r"^@(?P<username>[^/]+)/posts/(?P<slug>[-\w가-힣]+)/delete/$",
        views.UserPostDeleteView.as_view(),
        name="user_post_delete",
    ),
    re_path(
        r"^@(?P<username>[^/]+)/posts/(?P<slug>[-\w가-힣]+)/like/$",
        views.toggle_like,
        name="toggle_like",
    ),
]
