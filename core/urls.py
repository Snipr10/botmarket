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
    path("<int:pk>/like/<str:bot_username>", views.LikeView.as_view(), name="/"),
    path("<int:pk>/rating/<str:bot_username>", views.RaitingView.as_view(), name="/"),
    path("<int:pk>/comment/<str:bot_username>", views.CommentView.as_view(), name="/"),
    path("<int:pk>/bot_tg/<str:bot_username>", views.BotTg.as_view(), name="/"),
    path("<int:pk>/user_tg/", views.UserTg.as_view(), name="/"),
    path("bots_tg/", views.BotList.as_view(), name="/"),
    path("users_tg/", views.UserList.as_view(), name="/"),
    path("<str:bot_username>/likes/", views.Likes.as_view(), name="/"),
    path("<str:bot_username>/comments/", views.Comments.as_view(), name="/"),
    path("<str:bot_username>/ratings/", views.Ratings.as_view(), name="/"),

    path("search/<int:pk>", views.Search.as_view(), name="/"),
    path("top/<int:pk>", views.Top.as_view(), name="/"),

    path("update_elasctic/", views.UpdateElastic.as_view(), name="/")

]
