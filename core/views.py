import asyncio
import concurrent.futures
import json
import secrets
from abc import abstractmethod

import requests

from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import IntegrityError
from django.utils.crypto import get_random_string

# Create your views here.
from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError, ParseError, MethodNotAllowed
from rest_framework.response import Response
from rest_framework import generics, permissions, status

from botmarket.settings import SUPPORT_USER_URL
from core import models, serializers
from rest_framework.generics import get_object_or_404
from django.db.models import Avg, Count, Q, F, FloatField, ExpressionWrapper, IntegerField

from core.elastic.elastic import add_to_elastic, search_elastic, delete_from_elastic


# TG

class UserTgAbstract(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter()
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get_bot(self, bot_username):
        return get_object_or_404(self.queryset_bot, username=bot_username)

    def get_user(self, user_id):
        return get_object_or_404(self.queryset_user, user_id=user_id)


class ResetSubscribeIphoneView(generics.ListAPIView, generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.UserSignUpSerializer
    queryset = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            raise ValidationError({"message": "can not get tg user", "code": 4005})
        serializer = self.get_serializer(instance.user_phone.all(), many=True)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            raise ValidationError({"message": "can not get tg user", "code": 4006})
        instance.user_phone.all().delete()
        return Response("Ok")


class BotTg(UserTgAbstract):
    start = 0
    end = 100

    def get(self, request, *args, **kwargs):
        user = self.get_user(kwargs['pk'])
        try:
            serializer = serializers.BotTgSerializer(self.queryset_bot.filter(username=kwargs['bot_username']),
                                                     many=True, context={"user": user, "language": user.language}
                                                     )
            return Response({"bot": serializer.data})
        except KeyError:
            # serializer = serializers.BotTgSerializer(self.queryset_bot.filter().order_by("username")[
            #                                          int(request.query_params.get("start", self.start)):int(
            #                                              request.query_params.get("end", self.end))],
            #                                          many=True, context={"user": user, "language": user.language}
            #                                          )
            # last 100
            last_bot = self.queryset_bot.all().order_by("-date_created").values('pk')[
                       int(request.query_params.get("start", self.start)):int(
                           request.query_params.get("end", self.end))]

            serializer = serializers.BotTgSerializer(self.queryset_bot.filter(pk__in=last_bot).order_by("username"),
                                                     many=True, context={"user": user, "language": user.language}
                                                     )
            return Response({"bots": serializer.data})

    def post(self, request, *args, **kwargs):
        user = self.get_user(kwargs['pk'])
        if request.data.get("username") is None:
            request.data["username"] = kwargs['bot_username']

        if models.Bot.objects.filter(username__iexact=request.data["username"]).exists():
            return Response({"message": "Bot already exist", "code": 4007}, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializers.BotTgSerializer(data=request.data, partial=True, context={"user": user,
                                                                                           "language": user.language})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError:
            return self.patch(request, *args, **kwargs)
        bot = serializer.data
        return Response({"bot": bot})

    def patch(self, request, *args, **kwargs):
        user = self.get_user(kwargs['pk'])
        bot = self.get_bot(kwargs['bot_username'])
        if bot.user != user:
            return Response({"message": "bot's owner is not this user", "code": 4014}, status=401)
        if request.data.get("username") is None:
            request.data["username"] = kwargs['bot_username']
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(bot, request.data)
        return Response({"bot": serializers.BotTgSerializer(self.get_bot(kwargs['bot_username']), many=False,
                                                            context={
                                                                'request': request,
                                                                "language": user.language
                                                            }).data})


# CHANGE UserTgAbstract
class UserTg(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.UserTgSerializer
    queryset = models.UserTg.objects.filter()

    def get(self, request, *args, **kwargs):
        user = self.queryset.filter(user_id=kwargs['pk'])
        serializer = serializers.UserTgSerializer(user, many=True, context={'request': request})
        return Response({"user": serializer.data})

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"user": serializer.data})
        except IntegrityError as e:
            return self.patch(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        user = get_object_or_404(self.queryset, user_id=kwargs['pk'])
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, request.data)
        user = self.queryset.get(user_id=kwargs['pk'])
        serializer = serializers.UserTgSerializer(user, many=False, context={'request': request})
        return Response({"user": serializer.data})


class SearchAbstract(generics.GenericAPIView):
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def result_data(self, data, display_restrictions):
        tags = json.loads(data["tags"])
        try:
            start = int(data["start"])
            end = int(data["end"])
        except KeyError:
            start = 0
            end = 4
        try:
            language = json.loads(data['language'])
        except Exception:
            language = ["en", "ru"]
        ids, count = search_elastic(tags, start, end - start + 1, display_restrictions, language)
        res = list(self.queryset_bot.filter(id__in=ids))
        sort(res, ids)
        return res, count, tags, start, end


class Search(SearchAbstract):
    permission_classes = [permissions.AllowAny]

    # todo get
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])
        tags = request.data["tags"]
        try:
            start = int(request.data["start"]) - 1
            end = int(request.data["end"]) - 1
        except KeyError:
            start = 0
            end = 4
        try:
            language = json.loads(request.data['language'])
        except Exception:
            language = ["en", "ru"]
        ids, count = search_elastic(tags, start, end - start + 1, False, language)
        res = list(self.queryset_bot.filter(id__in=ids))
        sort(res, ids)
        models.Search.objects.create(tags=tags, start=start, end=end, usertg=user, count=count)
        return Response({'bots': serializers.BotTgSerializer(res,
                                                             context={'user': user, "language": user.language},
                                                             many=True
                                                             ).data, 'founded': count})


class Top(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def post(self, request, *args, **kwargs):
        months = 1
        start = 0
        end = 10
        language = ["en", "ru"]
        try:
            language = json.loads(request.query_params.get("language"))
        except Exception:
            pass
        try:
            months = int(request.data["months"])
        except KeyError:
            pass
        try:
            months = int(request.data["months"])
            start = int(request.data["start"])
            end = int(request.data["end"])
        except KeyError:
            pass
        user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])

        month_date = date.today() + relativedelta(months=-months)
        ## by like
        # bot_ids = list(BotLike.objects.filter(datetime__gte=month_date, bot__is_active=True, bot__ready_to_use=True)
        #                .values('bot_id').annotate(
        #     num=Count('bot_id')).order_by('-num').values_list('bot_id', flat=True)
        #                )

        res, count = self.top_bots(models.BotViews.objects.filter(datetime__gte=month_date, bot__is_active=True,
                                                                  bot__ready_to_use=True), start, end, language)

        return Response({'bots': serializers.BotTgSerializer(res,
                                                             context={'user': user, "language": user.language},
                                                             many=True
                                                             ).data, 'founded': count})

    def top_bots(self, bot_views, start, end, language):
        # bot_ids = list(bot_views.values('bot_id').annotate(
        #     num=Count('bot_id')).order_by('-num').values_list('bot_id', flat=True))
        if 'ru' in language and 'en' not in language:
            bot_views = bot_views.filter(Q(bot__description_ru__isnull=False) & ~Q(bot__description_ru=''))
        elif 'en' in language and 'ru' not in language:
            bot_views = bot_views.filter(Q(bot__description_en__isnull=False) & ~Q(bot__description_en=''))
        views_user = bot_views.filter(Q(user__isnull=False)).values("bot_id", "user_id").distinct()
        views_phone = bot_views.filter(Q(user_iphone__isnull=False)).values("bot_id", "user_iphone_id").distinct()
        res = {}
        for i in list(views_phone) + list(views_user):
            if res.get(i['bot_id']) is None:
                res[i['bot_id']] = 1
            else:
                res[i['bot_id']] += 1
        bot_ids = sorted(res, key=res.get, reverse=True)
        count = len(bot_ids)
        bot_ids = bot_ids[start:end]
        res = list(self.queryset_bot.filter(id__in=bot_ids))
        sort(res, bot_ids)
        return res, count


class Deal(generics.CreateAPIView):
    serializer_class = serializers.DealSerializer
    queryset = models.Deal.objects.filter()


# IPHONE
class SignUpView(generics.CreateAPIView):
    serializer_class = serializers.UserSignUpSerializer
    queryset = models.User.objects.filter()
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = serializer.save()
        return Response({"user": serializers.UserSignUpSerializer(user).data, "token": token.key},
                        status=status.HTTP_200_OK)


# not used
class SignInView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.SignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = serializer.save()
        user = models.User.objects.get(pk=user.pk)
        return Response({"user": serializers.UserSignUpSerializer(user).data, "token": token.key},
                        status=status.HTTP_200_OK)


class SearchIphone(SearchAbstract):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        res, count, tags, start, end = self.result_data(request.query_params, True)
        models.Search.objects.create(tags=tags, start=start, end=end, user=user, count=count)
        # to test
        # res = models.Bot.objects.all()
        return Response({'bots': serializers.BotTgSerializer(res,
                                                             context={'user': user, "language": user.language},
                                                             many=True
                                                             ).data, 'founded': count})


class TopIphone(Top):
    permission_classes = [permissions.IsAuthenticated]
    # queryset_view = models.BotViews.objects.filter(bot__is_active=True, bot__ready_to_use=True, bot__is_ban=False,
    #                                                bot__is_deleted=False)
    queryset_view = models.BotViews.objects.filter(Q(user__isnull=False) | Q(user_iphone__isnull=False),
                                                   bot__is_for_display_iphone=True, bot__age_restriction_18=False,
                                                   )

    def get_queryset(self):
        months = int(self.request.query_params.get('months', 1))
        month_date = date.today() + relativedelta(months=-months)
        queryset_view = self.queryset_view.filter(datetime__gte=month_date)
        return queryset_view

    def get(self, request, *args, **kwargs):
        user = request.user
        start = int(self.request.query_params.get('start', 0))
        end = int(self.request.query_params.get('end', 10))
        months = int(self.request.query_params.get('months', 1))
        language = ["en", "ru"]
        try:
            language = json.loads(request.query_params.get("language"))
        except Exception:
            pass
        res, count = self.top_bots(self.get_queryset(), start, end, language)
        models.IphoneTop.objects.create(months=months, start=start, end=end, user=user, count=count)
        return Response({'bots': serializers.BotTgSerializer(res,
                                                             context={'user': user, "language": user.language},
                                                             many=True
                                                             ).data, 'founded': count})


class UserView(generics.ListAPIView, generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.UserDataSerializer
    queryset = models.User.objects.filter(deleted=False)

    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class BotView(generics.CreateAPIView, generics.UpdateAPIView, generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.BotsListSerializerIphone
    queryset = models.Bot.objects.filter()

    def get_user_tg(self):
        user_tg = models.UserTg.objects.filter(user_phone=self.request.user).first()
        # if user_tg is None:
        #     raise ValidationError({"message": "Please, add tg user", "code": 4008})
        return user_tg

    def get_queryset(self):
        user_tg = self.get_user_tg()
        if user_tg is None:
            return self.queryset.filter(user_iphone=self.request.user)
        return self.queryset.filter(Q(user=self.get_user_tg()) | Q(user_iphone=self.request.user))

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class BotsView(BotView, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Bot.objects.filter(is_for_display_iphone=True, age_restriction_18=False)

    start = 0
    end = 100

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('username')[
                   int(request.query_params.get("start", self.start)):int(request.query_params.get("end", self.end))]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserTgAndIphone(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def check_user(self, user):
        if self.queryset_user.filter(user_phone=user).exists():
            raise ValidationError({"message": "your phone already add", "code": 4009})


class CreateCodeForAddPhoneToTg(UserTgAndIphone):

    def post(self, request, *args, **kwargs):
        user = request.user
        self.check_user(user)
        user_id = int(request.data["id"])
        # user_tg = self.queryset_user.get_object_or_404(user_id=user_id)
        user_tg = self.queryset_user.filter(user_id=user_id).first()
        if user_tg is None:
            raise ValidationError({"message": "user_tg not exist", "code": 40010})

        code = generate_code()
        try:
            post_data = {
                "user_id": user_tg.pk,
                "text": "Code <code>%s</code>" % code
            }
            response = requests.post(SUPPORT_USER_URL, json=post_data)
            if response.status_code != 200:
                raise ParseError({"message": "We can't send the code, check what our bot can write to you",
                                  "code": 40011})

        except Exception:
            raise ParseError({"message": "We can't send the code, please try again later",
                              "code": 40012})
        models.VerifyCode.objects.create(user_phone=user, user_tg=user_tg, code=code)
        # sent code
        return Response({code})


class PhoneToTg(UserTgAndIphone):
    def post(self, request, *args, **kwargs):
        code = request.data["code"]
        user = request.user
        if code == "AppleTestCd":
            user_tg = models.UserTg.objects.get(user_id=1472296121)
            user_tg.user_phone.add(user)
            return Response({"OK"})
        verify_code = models.VerifyCode.objects.filter(is_active=True, code=code).first()
        self.check_user(user)
        user_tg = verify_code.user_tg
        user_tg.user_phone.add(user)
        stop_generate_code(verify_code)
        return Response({"OK"})


class TgAccount(generics.DestroyAPIView, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    serializer_class = serializers.UserTgSerializer

    def get_queryset(self):
        return self.queryset.filter(user_phone=self.request.user)

    def perform_destroy(self, instance):
        instance.user_phone.remove(self.request.user)


from django.db.models import Func


class DiffDays(Func):
    function = 'DATE_PART'
    template = "%(function)s('day', %(expressions)s)"


class CastDate(Func):
    function = 'date_trunc'
    template = "%(function)s('day', %(expressions)s)"


class AdAbstract(generics.RetrieveAPIView):
    queryset = models.Ad.objects.filter(is_active=True)

    def get_object(self):
        return self.queryset.annotate(days=ExpressionWrapper(DiffDays(
            CastDate(secrets.choice([date.today(), F('datetime')]) - F('datetime'))) + 1,
                                                             output_field=IntegerField())).annotate(
            stats_ad=ExpressionWrapper(
                F('spent') / (1.0 * F('bought')) - F('days') / 30.0, output_field=FloatField())).order_by(
            'stats_ad').first()

    @abstractmethod
    def get_user(self, request, kwargs):
        ...

    def get(self, request, *args, **kwargs):
        ad = self.get_object()
        user = self.get_user(request, kwargs)
        while True:
            if ad is None:
                return Response({"message": "Ad not founded", "code": 4041}, status=404)
            elif ad.bot.is_active:
                if ad.category == 0:
                    ad.spent += 1
                    if ad.spent >= ad.bought:
                        ad.is_active = False
                    ad.save(update_fields=["is_active", "spent"])
                    return Response({"bot": serializers.BotTgSerializer(ad.bot,
                                                                        context={"user": user,
                                                                                 "language": user.language},
                                                                        ).data})
                else:
                    return Response({"bot": serializers.BotTgAdSerializer(ad.bot,
                                                                          context={'user': user,
                                                                                   "language": user.language,
                                                                                   "ad": ad.id},
                                                                          ).data})

            else:
                ad.is_active = False
                ad.save(update_fields=["is_active"])
                ad = self.get_object()


class Ad(AdAbstract):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Ad.objects.filter(is_active=True, bot__is_for_display_iphone=True)

    def get_user(self, request, kwargs):
        return request.user


class AdTg(AdAbstract):
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get_user(self, request, kwargs):
        return get_object_or_404(self.queryset_user, user_id=kwargs['pk'])


class AddBotsToTg(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_tg = models.UserTg.objects.filter(user_phone=self.request.user).first()
        if user_tg is None:
            raise ValidationError({"message": "Please, add tg user", "code": 4008})
        try:
            models.Bot.objects.filter(user=None, user_iphone=self.request.user).update(user=user_tg, user_iphone=None)
            return Response("OK")
        except Exception:
            raise ParseError({"message": "Try again later", "code": 40013})


def generate_code():
    unique_id = get_random_string(length=8)
    if models.VerifyCode.objects.filter(is_active=True, code=unique_id).exists():
        return generate_code()
    return unique_id


def stop_generate_code(verify_code):
    verify_code.is_active = False
    verify_code.save()


# URLs
class TgMe(generics.CreateAPIView):
    def get(self, request, *args, **kwargs):
        username = self.kwargs['bot_username']
        pk_u = request.GET.get("u")
        pk_i = request.GET.get("i")
        pk_a = request.GET.get("a")

        executor = concurrent.futures.ThreadPoolExecutor(2)
        executor.submit(save_views, username, pk_u, pk_i, pk_a)
        return redirect('https://t.me/%s' % username.replace('@', ''))


def save_views(username, pk_u, pk_i, pk_a):
    bot = None
    try:
        bot = models.Bot.objects.get(username=username)
    except Exception:
        pass

    if bot is None:
        try:
            bot = models.Bot.objects.get(username='@' + username)
        except Exception:
            pass
    if bot is not None:
        try:
            if pk_u is not None:
                user = models.UserTg.objects.get(pk=int(pk_u))
                models.BotViews.objects.create(bot=bot, user=user)
            elif pk_i is not None:
                user = models.User.objects.get(pk=int(pk_i))
                models.BotViews.objects.create(bot=bot, user_iphone=user)
            else:
                models.BotViews.objects.create(bot=bot)
        except Exception:
            models.BotViews.objects.create(bot=bot)
            pass
        try:
            if pk_a is not None:
                ad = models.Ad.objects.get(id=int(pk_a))
                ad.spent += 1
                if ad.spent >= ad.bought:
                    ad.is_active = False
                ad.save(update_fields=["is_active", "spent"])
        except Exception:
            pass


def sort(res, ids):
    res.sort(key=lambda t: ids.index(t.id))


# NOT NEEDED NOW
class BotList(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter(is_active=True)
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get(self, request, *args, **kwargs):
        return Response({"bots": self.get_serializer(self.queryset_bot, many=True,
                                                     ).data})


class UserList(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.UserTgSerializer
    queryset_bot = models.UserTg.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        serializer = serializers.UserTgSerializer(self.queryset_bot, many=True, context={'request': request})
        return Response({"users": serializer.data})


class Likes(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.LikesSerializer
    queryset = models.BotLike.objects.filter()
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)

    def get(self, request, *args, **kwargs):
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        query_set = self.queryset.filter(bot=bot)
        serializer = serializers.LikesSerializer(query_set, many=True, context={'request': request})
        return Response({"likes": serializer.data, "count": len(query_set)})


class LikeView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)

    def post(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            models.BotLike.objects.get(user=user_tg, bot=bot)
            return Response("Already like")
        except models.BotLike.DoesNotExist:
            models.BotLike.objects.create(user=user_tg, bot=bot)
            return Response("OK")

    def delete(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            like = models.BotLike.objects.get(user=user_tg, bot=bot)
            like.delete()
            return Response("delete")
        except models.BotLike.DoesNotExist:
            return Response("Bot not like")


class Ratings(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = models.BotRating.objects.filter()
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)

    def get(self, request, *args, **kwargs):
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        rating = self.queryset.filter(bot=bot).aggregate(Avg('rating'))['rating__avg']
        return Response({"rating": rating})


class RaitingView(LikeView):
    permission_classes = [permissions.AllowAny]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)

    def post(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            models.BotRating.objects.get(user=user_tg, bot=bot)
            return Response("Already rating")
        except models.BotRating.DoesNotExist:
            models.BotRating.objects.create(user=user_tg, bot=bot, rating=int(request.data['rating']))
        return Response("OK")

    def patch(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            rating = models.BotRating.objects.get(user=user_tg, bot=bot)
            rating.rating = int(request.data['rating'])
            rating.save(update_fields=["rating"])
            return Response("Change rating")
        except models.BotRating.DoesNotExist:
            models.objects.BotRating.create(user=user_tg, bot=bot, rating=request.data['rating'])
            return Response("Raiting create")

    def delete(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            rating = models.BotRating.objects.get(user=user_tg, bot=bot)
            rating.delete()
            return Response("Delete rating")
        except models.BotRating.DoesNotExist:
            return Response("Raiting not exist")


class Comments(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.CommentsSerializer
    queryset = models.BotComment.objects.filter()
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)

    def get(self, request, *args, **kwargs):
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        query_set = self.queryset.filter(bot=bot)
        serializer = serializers.CommentsSerializer(query_set, many=True, context={'request': request})
        return Response({"comments": serializer.data, "count": len(query_set)})


class CommentView(LikeView):
    permission_classes = [permissions.AllowAny]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True)

    def post(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            models.BotComment.objects.get(user=user_tg, bot=bot)
            return Response("Already comment")
        except models.BotComment.DoesNotExist:
            models.BotComment.objects.create(user=user_tg, bot=bot, text=request.data['text'])
        return Response("OK")

    def patch(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            rating = models.BotComment.objects.get(user=user_tg, bot=bot)
            rating.rating = request.data['rating']
            rating.save(["rating"])
            return Response("Change comment")
        except models.BotComment.DoesNotExist:
            models.BotComment.objects.create(user=user_tg, bot=bot, text=request.data['text'])
            return Response("Comment create")

    def delete(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, username=self.kwargs['bot_username'])
        try:
            comment = models.BotComment.objects.get(user=user_tg, bot=bot)
            comment.delete()
            return Response("Delete comment")
        except models.BotComment.DoesNotExist as e:
            return Response("Comment not exist")


# FOR TEST
class UpdateElastic(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        for bot in models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False, ready_to_use=True):
            add_to_elastic(bot.id, bot.tags, "{ru} {en}".format(ru=bot.description_ru,
                                                                en=bot.description_en))
        for bot in models.Bot.objects.filter(ready_to_use=False):
            try:
                delete_from_elastic(bot.id)
            except Exception:
                pass
        for bot in models.Bot.objects.filter(is_active=False):
            try:
                delete_from_elastic(bot.id)
            except Exception:
                pass
        return Response("Ok")


class ReadyToUse(generics.GenericAPIView):

    def get(self, request, *args, **kwargs):

        from core.push.ios import CLIENT_ISO_PUSH
        # from gobiko.apns.payload import PayloadAlert, Payload

        CLIENT_ISO_PUSH.send_message('f0c328b3a8dc8cc8e9c5a4b023d5ccd361f151217f420aaf3f92fc44fcf63a4d', 'тест',
                                     loc_key='This is a %@',
           loc_args=['Test'])

        code = generate_code()
        try:
            post_data = {
                "user_id": 457180576,
                "text": "Code <code>%s</code>" % code
            }
            response = requests.post(SUPPORT_USER_URL, json=post_data)
        except Exception:
            pass

        validate_name = "usaway_world_dates_bot"
        import re
        re.match("^[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*$", validate_name)
        # for bot in models.Bot.objects.filter():
        #     bot.ready_to_use = True
        #     bot.save()
        #     try:
        #         add_to_elastic(bot.id, bot.tags, "{ru} {en}".format(ru=bot.description_ru,
        #                                                             en=bot.description_en))
        #     except Exception:
        #         pass
        return Response("Ok")
