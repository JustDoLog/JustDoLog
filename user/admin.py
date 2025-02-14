from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Follow


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "username",
        "email",
        "is_staff",
        "created_at",
        "updated_at",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "추가 정보",
            {
                "fields": (
                    "profile_image",
                    "github_url",
                    "twitter_url",
                    "facebook_url",
                    "homepage_url",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "추가 정보",
            {
                "fields": (
                    "profile_image",
                    "github_url",
                    "twitter_url",
                    "facebook_url",
                    "homepage_url",
                )
            },
        ),
    )


class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following")


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Follow, FollowAdmin)
