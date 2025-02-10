from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth import get_user_model, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from .models import Follow
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.contrib import messages
from django.core.files.storage import default_storage
from django.conf import settings
import boto3
from botocore.client import Config
import uuid

User = get_user_model()

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"

class FollowUserView(LoginRequiredMixin, View):
    def post(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)
        
        # 자기 자신을 팔로우할 수 없음
        if request.user == user_to_follow:
            return HttpResponse(status=400)
        
        # 이미 팔로우한 경우 언팔로우
        follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        
        if not created:  # 이미 팔로우 중이었다면 삭제
            follow.delete()
        
        # 팔로워 수 조회
        followers_count = user_to_follow.followers.count()
        
        # HTMX 응답 반환
        button_html = f'''
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
        '''
        
        return HttpResponse(button_html)

@login_required
@require_POST
def upload_profile_image(request):
    if 'profile_image' in request.FILES:
        file = request.FILES['profile_image']
        
        if not file.content_type.startswith("image/"):
            return HttpResponse("Invalid file type", status=400)
        
        # 기존 이미지 삭제
        if request.user.profile_image:
            request.user.profile_image.delete()
        
        # 새 이미지 저장
        request.user.profile_image = file
        request.user.save()
        
        # 업데이트된 프로필 이미지 섹션 반환
        html = render_to_string('account/partials/profile_image.html', {'user': request.user})
        return HttpResponse(html)
            
    return HttpResponse(status=400)

@login_required
@require_POST
def remove_profile_image(request):
    user = request.user
    if user.profile_image:
        user.profile_image.delete()
        user.profile_image = None
    user.save()
    
    # Return the updated profile image section
    html = render_to_string('account/partials/profile_image.html', {'user': request.user})
    return HttpResponse(html)

@login_required
def toggle_edit_mode(request):
    """프로필 편집 모드 토글을 위한 뷰"""
    is_edit_mode = request.GET.get('edit_mode', 'false') == 'true'
    html = render_to_string('account/partials/profile_form.html', {
        'user': request.user,
        'is_edit_mode': is_edit_mode
    })
    return HttpResponse(html)

@login_required
@require_POST
def update_profile(request):
    user = request.user
    blog_description = request.POST.get('blog_description')
    
    if blog_description is not None:
        user.blog.description = blog_description
        user.blog.save()
    
    # 저장 후 읽기 전용 모드로 변경
    html = render_to_string('account/partials/profile_form.html', {
        'user': request.user,
        'is_edit_mode': False
    })
    return HttpResponse(html)

@login_required
def profile_view(request):
    return render(request, "account/profile.html")

@login_required
def profile_image_upload(request):
    if request.method == "POST" and request.FILES.get("profile_image"):
        request.user.profile_image = request.FILES["profile_image"]
        request.user.save()
        return render(request, "account/partials/profile_image.html")
    return HttpResponse(status=400)

@login_required
def profile_form(request):
    is_edit_mode = request.GET.get("edit") == "true"
    return render(request, "account/partials/profile_form.html", {
        "is_edit_mode": is_edit_mode
    })

@login_required
def profile_update(request):
    if request.method == "POST":
        blog = request.user.blog
        blog.title = request.POST.get("blog_title", "")
        blog.description = request.POST.get("blog_description", "")
        blog.save()
        return render(request, "account/partials/profile_form.html", {
            "is_edit_mode": False
        })
    return HttpResponse(status=400)

@login_required
def account_delete(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "계정이 성공적으로 삭제되었습니다.")
        return redirect("trending_day")
    return render(request, "account/account_delete.html")

@login_required
@require_POST
def toggle_social_edit(request):
    """소셜 정보 수정 모드 토글"""
    return render(request, 'account/partials/social_info.html', {
        'is_edit_mode': True
    })

@login_required
@require_POST
def update_social_info(request):
    """소셜 정보 업데이트"""
    user = request.user
    user.github_url = request.POST.get('github_url', '')
    user.twitter_url = request.POST.get('twitter_url', '')
    user.facebook_url = request.POST.get('facebook_url', '')
    user.homepage_url = request.POST.get('homepage_url', '')
    user.save()

    return render(request, 'account/partials/social_info.html', {
        'is_edit_mode': False
    })

@login_required
def profile_edit(request):
    if request.method == "POST":
        user = request.user
        
        # 프로필 이미지 처리
        if 'profile_image' in request.FILES:
            if user.profile_image:
                user.profile_image.delete()
            user.profile_image = request.FILES['profile_image']
        
        # 소셜 URL 업데이트
        user.github_url = request.POST.get('github_url', '')
        user.twitter_url = request.POST.get('twitter_url', '')
        user.facebook_url = request.POST.get('facebook_url', '')
        user.homepage_url = request.POST.get('homepage_url', '')
        
        # 블로그 정보 업데이트
        if hasattr(user, 'blog'):
            user.blog.title = request.POST.get('blog_title', '')
            user.blog.description = request.POST.get('blog_description', '')
            user.blog.save()
        
        user.save()
        messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
        return redirect('profile')
        
    return render(request, 'account/profile_edit.html')
