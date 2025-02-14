from rest_framework.generics import ListAPIView
from .serializers import PostListSerializer

recent_posts = ListAPIView.as_view(
    queryset=PostListSerializer.get_optimized_queryset(),
    serializer_class=PostListSerializer,
)
