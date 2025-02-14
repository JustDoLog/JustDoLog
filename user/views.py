from django.views.generic import TemplateView, View, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, logout
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.conf import settings
import os
from .models import Follow

User = get_user_model()


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = "account/profile_edit.html"
    fields = []  # 실제 필드는 form_valid에서 처리
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 개발 환경에서는 STATICFILES_DIRS에서 이미지 찾기
        if settings.DEBUG:
            for static_dir in settings.STATICFILES_DIRS:
                profile_images_dir = os.path.join(static_dir, "images/default_profile")
                if os.path.exists(profile_images_dir):
                    break
        else:
            # 프로덕션 환경에서는 STATIC_ROOT 사용
            profile_images_dir = os.path.join(
                settings.STATIC_ROOT, "images/default_profile"
            )

        if os.path.exists(profile_images_dir):
            profile_images = sorted(
                [
                    f
                    for f in os.listdir(profile_images_dir)
                    if f.startswith("profile_") and f.endswith(".jpg")
                ],
                key=lambda x: int(x.split("_")[1].split(".")[0]),
            )
            context["profile_images"] = profile_images
        else:
            context["profile_images"] = []

        return context

    def form_valid(self, form):
        user = form.instance

        # 프로필 이미지 처리
        if "profile_image" in self.request.FILES:
            if user.profile_image:
                user.profile_image.delete()
            user.profile_image = self.request.FILES["profile_image"]

        # 소셜 URL 업데이트
        user.github_url = self.request.POST.get("github_url", "")
        user.twitter_url = self.request.POST.get("twitter_url", "")
        user.facebook_url = self.request.POST.get("facebook_url", "")
        user.homepage_url = self.request.POST.get("homepage_url", "")

        # 블로그 정보 업데이트
        if hasattr(user, "blog"):
            user.blog.title = self.request.POST.get("blog_title", "")
            user.blog.description = self.request.POST.get("blog_description", "")
            user.blog.save()

        messages.success(self.request, "프로필이 성공적으로 업데이트되었습니다.")
        return super().form_valid(form)


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "account/account_delete.html"
    success_url = reverse_lazy("trending_day")

    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "계정이 성공적으로 삭제되었습니다.")
        logout(request)
        return super().delete(request, *args, **kwargs)


class FollowUserView(LoginRequiredMixin, View):
    def post(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)

        # 자기 자신을 팔로우할 수 없음
        if request.user == user_to_follow:
            return HttpResponse(status=400)

        # 이미 팔로우한 경우 언팔로우
        follow, created = Follow.objects.get_or_create(
            follower=request.user, following=user_to_follow
        )

        if not created:  # 이미 팔로우 중이었다면 삭제
            follow.delete()

        # 팔로워 수 조회
        followers_count = user_to_follow.followers.count()

        # HTMX 응답 반환
        button_html = f"""
        <div class="flex-shrink-0" id="follow-button-{username}">
            <button hx-post="{reverse('follow_user', kwargs={'username': username})}"
                    hx-swap="outerHTML"
                    hx-target="#follow-button-{username}"
                    hx-headers='{{"X-CSRFToken": "{request.META.get('CSRF_COOKIE')}"}}' 
                    class="{'bg-gray-900 text-white hover:bg-gray-800' if created else 'text-gray-900 bg-white border border-gray-900 hover:bg-gray-50'} px-6 py-2 text-sm font-medium rounded-full transition-colors">
                {'팔로잉' if created else '팔로우'}
            </button>
        </div>
        <div hx-swap-oob="true" id="followers-count-{username}">
            팔로워 {followers_count}명
        </div>
        """

        return HttpResponse(button_html)
