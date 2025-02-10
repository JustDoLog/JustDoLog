from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from user import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="trending_day", permanent=False)),
    path("admin/", admin.site.urls),
    path("accounts/", include("user.urls")),
    path("accounts/", include("allauth.urls")),
    path("tinymce/", include("tinymce.urls")),
    path("", include("blog.urls")),
    path("discovery/", include("discovery.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
