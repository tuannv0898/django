from django.urls import path

from . import views

urlpatterns = [
    path('', views.ManagerApi.as_view()),
]
