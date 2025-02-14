from django.contrib.auth import get_user_model
from rest_framework import serializers
from blog.models import Post


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["pk", "username", "email"]


class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ["title", "content", "author"]

    @staticmethod
    def get_optimized_queryset():
        return Post.objects.published().order_by("-created_at").select_related("author")
