from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from .models import Follow
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

User = get_user_model()

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"

class FollowUserView(LoginRequiredMixin, View):
    def post(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)
        
        # 자기 자신을 팔로우할 수 없음
        if request.user == user_to_follow:
            return HttpResponseRedirect(reverse('user_blog_main', kwargs={'username': username}))
        
        # 이미 팔로우한 경우 무시
        Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        
        return HttpResponseRedirect(reverse('user_blog_main', kwargs={'username': username}))

class UnfollowUserView(LoginRequiredMixin, View):
    def post(self, request, username):
        user_to_unfollow = get_object_or_404(User, username=username)
        
        # 팔로우 관계가 있으면 삭제
        Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
        
        return HttpResponseRedirect(reverse('user_blog_main', kwargs={'username': username}))

@login_required
@require_POST
def upload_profile_image(request):
    if 'profile_image' in request.FILES:
        request.user.profile_image = request.FILES['profile_image']
        request.user.save()
        
        # Return the updated profile image section
        html = render_to_string('account/partials/profile_image.html', {'user': request.user})
        return HttpResponse(html)
    return HttpResponse(status=400)

@login_required
@require_POST
def remove_profile_image(request):
    if request.user.profile_image:
        request.user.profile_image.delete()
        request.user.profile_image = None
        request.user.save()
        
        # Return the updated profile image section
        html = render_to_string('account/partials/profile_image.html', {'user': request.user})
        return HttpResponse(html)
    return HttpResponse(status=400)

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
