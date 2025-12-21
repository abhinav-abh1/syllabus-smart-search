from django.urls import path
from .views import topic_search

urlpatterns = [
    path("", topic_search, name="topic_search"),
]
