"""botmarket URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from core import views

urlpatterns = [
    path("<int:pk>/like/<int:bot_pk>", views.LikeView.as_view(), name="/"),
    path("<int:pk>/unlike", views.UnlikeView.as_view(), name="/"),
    path("<int:pk>/rating/<int:bot_pk>", views.RaitingView.as_view(), name="/"),
    path("<int:pk>/comment/<int:bot_pk>", views.CommentView.as_view(), name="/"),
    path("<int:pk>/bot_tg/", views.BotTg.as_view(), name="/"),
    path("<int:pk>/user_tg/", views.UserTg.as_view(), name="/"),
    path("bots_tg/", views.BotList.as_view(), name="/"),
    path("users_tg/", views.UserList.as_view(), name="/"),


]
