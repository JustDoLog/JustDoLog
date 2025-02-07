from django.dispatch import receiver
from django.db.models.signals import post_save
from user.models import CustomUser
from .models import Blog


@receiver(post_save, sender=CustomUser)
def create_user_blog(sender, instance, created, **kwargs):
    if created:
        Blog.objects.create(owner=instance, title=f"Just Do {instance.username}'s Blog")
