from django.urls import path

from .views import ManagerApi

urlpatterns = [
    path('', ManagerApi.as_view()),
]
