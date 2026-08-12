from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('explore/', views.explore_view, name='explore'),
    path('post/create/', views.post_create_view, name='create'),
    path('post/<slug:slug>/', views.post_detail_view, name='detail'),
    path('post/<slug:slug>/edit/', views.post_edit_view, name='edit'),
    path('post/<slug:slug>/delete/', views.post_delete_view, name='delete'),
    path('category/<slug:slug>/', views.category_view, name='category'),
]
