from django.urls import path, re_path
from . import views
from .feeds import LatestPostsFeed
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


app_name = 'blog'

urlpatterns = [
    # post views
    path('', views.post_list, name='post_list'),
    path('tag/<slug:tag_slug>/', views.post_list, name='post_list_by_tag'),
    # path('', views.PostListView.as_view(), name='post_list'),
    path('detail/<str:post>/', views.post_detail, name='post_detail'),
    
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', views.post_search, name='post_search'),
    path('update/', views.update_users, name='update_users')
]

urlpatterns += staticfiles_urlpatterns()
