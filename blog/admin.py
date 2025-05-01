from django.contrib import admin
from blog.models import Post, Tag, Comment



@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['text', 'author', 'post', 'published_at']
    list_select_related = ['author', 'post']
    raw_id_fields = ['author', 'post']
    ordering = ['-published_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    raw_id_fields = ['author', 'tags', 'likes']  # особенно полезно для M2M like/tag
    list_display = ['title', 'author', 'published_at']  # кратко и быстро

    list_select_related = ['author']
    search_fields = ['title', 'author__username']
    ordering = ['-published_at']



admin.site.register(Tag)

