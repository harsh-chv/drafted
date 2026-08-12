"""
Root URL configuration for WriteSphere.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic.base import RedirectView
from . import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/posts/', api.posts_api, name='api_posts'),
    path('api/posts/<slug:slug>/', api.post_detail_api, name='api_post_detail'),
    path('api/posts/<slug:slug>/comments/', api.post_comments_api, name='api_post_comments'),
    path('api/posts/<slug:slug>/like/', api.post_like_api, name='api_post_like'),
    path('api/bookmarks/', api.bookmarks_api, name='api_bookmarks'),
    path('', include('posts.urls')),
    path('users/', include('users.urls')),
    path('interactions/', include('interactions.urls')),
    path('accounts/', include('allauth.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/images/icon.png', permanent=True)),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
