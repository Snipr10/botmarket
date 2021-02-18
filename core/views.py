from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework import  generics, permissions, status
from core import models, serializers
from rest_framework.generics import get_object_or_404
from django.db.models import Avg


class BotList(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter(is_active=True)
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get(self,  request, *args, **kwargs):
        # user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])
        return Response({"bots": self.get_serializer(self.queryset_bot, many=True,
                                                             # context={'language': user.language},
                                                            ).data})


class BotTg(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter()
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)


    def get(self,  request, *args, **kwargs):
        user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])
        serializer = serializers.BotTgSerializer(self.queryset_bot.filter(bot_id=kwargs['bot_pk']),
                                                 many=True, context={"user": user}
                                                 )
        return Response({"bot": serializer.data})

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])
        serializer = serializers.BotTgSerializer(data=request.data, partial=True, context={"user": user})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except Exception as e:
            return Response(str(e))
        return Response({"bot": serializer.data})

    def patch(self, request, *args, **kwargs):
        user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=kwargs['bot_pk'])
        if bot.user != user:
            return Response("bot's owner is not this user")
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(bot, request.data)
        bot = self.queryset_bot.filter(bot_id=kwargs['bot_pk'])
        serializer = serializers.BotTgSerializer(bot, many=True, context={'request': request})
        return Response({"bot": serializer.data})


class UserList(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.UserTgSerializer
    queryset_bot = models.UserTg.objects.filter(is_active=True)

    def get(self,  request, *args, **kwargs):
        serializer = serializers.UserTgSerializer(self.queryset_bot, many=True, context={'request': request})
        return Response({"users": serializer.data})


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
        except Exception as e:
            return Response({"error": str(e)})

    def patch(self, request, *args, **kwargs):
        user = get_object_or_404(self.queryset, user_id=kwargs['pk'])
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, request.data)
        user = self.queryset.filter(user_id=kwargs['pk'])
        serializer = serializers.UserTgSerializer(user, many=True, context={'request': request})
        return Response({"user": serializer.data})


class Likes(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.LikesSerializer
    queryset = models.BotLike.objects.filter()
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get(self,  request, *args, **kwargs):
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['pk'])
        query_set = self.queryset.filter(bot=bot)
        serializer = serializers.LikesSerializer(query_set, many=True, context={'request': request})
        return Response({"likes": serializer.data, "count": len(query_set)})


class LikeView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def post(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])

        try:
            models.BotLike.objects.get(user=user_tg, bot=bot)
            return Response("Already like")
        except models.BotLike.DoesNotExist:
            models.BotLike.objects.create(user=user_tg, bot=bot)
            return Response("OK")

    def delete(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
        try:
            like = models.BotLike.objects.get(user=user_tg, bot=bot)
            like.delete()
            return Response("delete")

        except models.BotLike.DoesNotExist:
            return Response("Bot not like")


class Ratings(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = models.BotRating.objects.filter()
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get(self,  request, *args, **kwargs):
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['pk'])
        rating = self.queryset.filter(bot=bot).aggregate(Avg('rating'))['rating__avg']
        return Response({"rating": rating})


class RaitingView(LikeView):
    permission_classes = [permissions.AllowAny]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def post(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
        try:
            models.BotRating.objects.get(user=user_tg, bot=bot)
            return Response("Already rating")
        except models.BotRating.DoesNotExist:
            models.BotRating.objects.create(user=user_tg, bot=bot, rating=int(request.data['rating']))
        return Response("OK")

    def patch(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
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
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
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
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get(self,  request, *args, **kwargs):
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['pk'])
        query_set = self.queryset.filter(bot=bot)
        serializer = serializers.CommentsSerializer(query_set, many=True, context={'request': request})
        return Response({"comments": serializer.data, "count": len(query_set)})


class CommentView(LikeView):
    permission_classes = [permissions.AllowAny]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def post(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
        try:
            models.BotComment.objects.get(user=user_tg, bot=bot)
            return Response("Already comment")
        except models.BotComment.DoesNotExist:
            models.BotComment.objects.create(user=user_tg, bot=bot, text=request.data['text'])
        return Response("OK")

    def patch(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
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
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
        try:
            comment = models.BotComment.objects.get(user=user_tg, bot=bot)
            comment.delete()
            return Response("Delete comment")
        except models.BotComment.DoesNotExist as e:
            return Response("Comment not exist")


class Search(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    # serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def post(self,  request, *args, **kwargs):
        tags = request.data["tags"]
        try:
            start = int(request.data["start"]) - 1
            end = int(request.data["end"]) - 1
        except KeyError:
            start = 0
            end = 4
        user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])
        return Response({"bots":  serializers.BotTgSerializer(self.queryset_bot.filter(tags__in=tags)[start:end],
                                                              many=True,
                                                              context={'language': user.language},
                                                              ).data})


class Top(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    # serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def get(self,  request, *args, **kwargs):
        user = get_object_or_404(self.queryset_user, user_id=kwargs['pk'])

        return Response({"bots": serializers.BotTgSerializer(self.queryset_bot.filter()[:10],
                                                             context={'language': user.language},
                                                             many=True
                                                             ).data})

