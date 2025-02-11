@shared_task
def update_blog_stats():
    """모든 블로그의 통계 주기적 업데이트"""
    for blog in Blog.objects.all():
        blog.update_stats() 