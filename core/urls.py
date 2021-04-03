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
from core import views
from django.urls import include, path


def trigger_error(request):
    division_by_zero = 1 / 0


iphone = [
    path("signup/", views.SignUpView.as_view(), name="sign-up"),
    path("signin/", views.SignInView.as_view(), name="sign-in"),
    path("user/", views.UserView.as_view(), name="user"),
    path("tipidor/", views.Tipidor.as_view(), name="tipidor"),
    path("search/", views.SearchIphone.as_view(), name="search"),
    path("top/", views.TopIphone.as_view(), name="search"),
    path("bot/", views.BotView.as_view(), name="all my bots"),
    path("bot/<int:pk>/", views.BotView.as_view(), name="my bot"),
    path("generate_code/", views.CreateCodeForAddPhoneToTg.as_view(), name="code"),
    path("phone_and_tg/", views.PhoneToTg.as_view(), name="add phone to bot"),
    path("tg_account/", views.TgAccount.as_view(), name="PhoneToBot"),
    path("tg_account/<int:pk>/", views.TgAccount.as_view(), name="PhoneToBot")
]

tg = [
    path("<int:pk>/bot_tg/<str:bot_username>/", views.BotTg.as_view(), name="/"),
    path("<int:pk>/user_tg/", views.UserTg.as_view(), name="/"),
    path("search/<int:pk>/", views.Search.as_view(), name="/"),
    path("top/<int:pk>/", views.Top.as_view(), name="/"),
    path("deal/", views.Deal.as_view(), name="/"),
    # path("<int:pk>/my_device/", views.MyDeviceView.as_view(), name="/"),
    # path("<int:pk>/my_device/<int:phone_id>/", views.MyDeviceView.as_view(), name="/"),
]


urlpatterns = [
    path('sentry-debug/', trigger_error),
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
    path("update_elasctic/", views.UpdateElastic.as_view(), name="/"),
    path("deal", views.Deal.as_view(), name="/"),

    # iphone
    path("iphone/", include(iphone)),
    # tg
    path("tg/", include(iphone)),
]
