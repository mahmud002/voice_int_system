from django.urls import path
from . import views

urlpatterns = [
    path('similarity_checking/', views.voice_similarity, name='register'),
    path('search_youtube/', views.search_youtube, name='search_youtube'),
    path("delete_temp_files/", views.delete_temp_files, name="delete_temp_files"),
]

#1361260033753