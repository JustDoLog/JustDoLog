from django import template

register = template.Library()


@register.filter
def is_liked_by(post, user):
    if not user.is_authenticated:
        return False
    return post in user.liked_posts.all()
