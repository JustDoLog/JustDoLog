from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


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
                    "nickname",
                    "bio",
                    "github",
                    "twitter",
                    "facebook",
                    "homepage",
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
                    "nickname",
                    "bio",
                    "github",
                    "twitter",
                    "facebook",
                    "homepage",
                )
            },
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
