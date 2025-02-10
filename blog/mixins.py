from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from user.models import Follow
from django.db.models import QuerySet

class PaginatedListMixin:
    """페이지네이션 처리를 위한 Mixin"""
    paginate_by = 10

    def paginate_queryset(self, queryset):
        """QuerySet을 페이지네이션 처리"""
        if not isinstance(queryset, (list, QuerySet)):
            return queryset, False, None

        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return page_obj.object_list, True, page_obj

    def get_context_data(self, **kwargs):
        """페이지네이션 관련 컨텍스트 데이터 추가"""
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        object_list, is_paginated, page_obj = self.paginate_queryset(queryset)
        
        context.update({
            'object_list': object_list,
            'is_paginated': is_paginated,
            'page_obj': page_obj,
        })
        return context


class UserContextMixin:
    """사용자 관련 컨텍스트 데이터 처리를 위한 Mixin"""
    
    def get_user_context(self, **kwargs):
        """사용자 관련 컨텍스트 데이터 반환"""
        context = {
            'is_owner': False,
            'has_liked': False,
            'is_following': False
        }
        
        if not self.request.user.is_authenticated:
            return context
            
        # 팔로우 상태 확인
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            if hasattr(obj, 'owner') or hasattr(obj, 'blog'):
                target_user = getattr(obj, 'owner', None) or getattr(obj, 'blog').owner
                if target_user and target_user != self.request.user:
                    context['is_following'] = Follow.objects.filter(
                        follower=self.request.user,
                        following=target_user
                    ).exists()
                if target_user == self.request.user:
                    context['is_owner'] = True
        
        # 좋아요 상태 확인 (Post 객체인 경우)
        if hasattr(self, 'object') and hasattr(self.object, 'liked_by'):
            context['has_liked'] = self.object.liked_by.filter(
                id=self.request.user.id
            ).exists()
        
        return context

    def get_context_data(self, **kwargs):
        """컨텍스트 데이터에 사용자 관련 정보 추가"""
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(**kwargs))
        return context


class HtmxResponseMixin:
    """HTMX 응답 처리를 위한 Mixin"""
    
    def is_htmx_request(self):
        """HTMX 요청인지 확인"""
        return self.request.headers.get('HX-Request') == 'true'
    
    def render_htmx_template(self, template_name, context=None):
        """HTMX 요청에 대한 부분 템플릿 렌더링"""
        from django.template.loader import render_to_string
        context = context or {}
        response = HttpResponse(
            render_to_string(template_name, context, request=self.request)
        )
        response['HX-Request'] = 'true'
        return response
    
    def get_htmx_trigger_headers(self, **kwargs):
        """HTMX 트리거 헤더 생성"""
        headers = {}
        for key, value in kwargs.items():
            headers[f'HX-Trigger-{key}'] = value
        return headers 