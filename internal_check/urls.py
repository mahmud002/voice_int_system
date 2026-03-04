from django.urls import path
from . import views

urlpatterns = [
    path('similarity_checking/', views.voice_similarity, name='register'),
    path('search_youtube/', views.search_youtube, name='search_youtube'),
]

#1361260033753