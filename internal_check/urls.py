from django.urls import path
from . import views

urlpatterns = [
    path('similarity_checking/', views.voice_similarity, name='register'),

]