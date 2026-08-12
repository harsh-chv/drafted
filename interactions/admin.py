from django.contrib import admin
from .models import Bookmark, Comment, Like, Follow, Notification


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username', 'post__title']
    raw_id_fields = ['author', 'post']

    def content_preview(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'Comment'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['user', 'post']


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['user', 'post']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['follower', 'following']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'actor', 'action', 'post', 'is_read', 'created_at']
    list_filter = ['action', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'actor__username']
    raw_id_fields = ['recipient', 'actor', 'post']
