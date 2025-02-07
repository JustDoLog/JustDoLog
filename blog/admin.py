from django.contrib import admin
from .models import Blog, Post


class BlogAdmin(admin.ModelAdmin):
    list_display = ("owner", "title", "description", "created_at")


class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "blog", "title", "created_at")
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
