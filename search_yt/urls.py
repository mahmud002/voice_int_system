from django.urls import path
from . import views

urlpatterns = [
    path('channel-search/', views.channel_voice_search, name='channel_search'),
    path('process-channel-comparison/', views.process_channel_comparison, name='process_channel_comparison'),
    path("delete_temp_files/", views.delete_temp_files, name="delete_temp_files"),
]