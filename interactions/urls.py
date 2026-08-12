from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    path('like/<int:post_id>/', views.like_toggle_view, name='like_toggle'),
    path('comment/<int:post_id>/add/', views.comment_add_view, name='comment_add'),
    path('comment/<int:comment_id>/edit/', views.comment_edit_view, name='comment_edit'),
    path('comment/<int:comment_id>/delete/', views.comment_delete_view, name='comment_delete'),
    path('comment/<int:comment_id>/like/', views.comment_like_toggle_view, name='comment_like_toggle'),
    path('follow/<str:username>/', views.follow_toggle_view, name='follow_toggle'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('note/add/', views.note_add_view, name='note_add'),
]
