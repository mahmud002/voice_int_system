from django.urls import path
from . import views

urlpatterns = [
    path('similarity_checking/', views.check_similarity, name='register'),

]