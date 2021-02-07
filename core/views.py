from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework import  generics, permissions, status
from core import models, serializers
from rest_framework.generics import get_object_or_404


class BotList(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter(is_active=True)

    def get(self,  request, *args, **kwargs):
        serializer = serializers.BotTgSerializer(self.queryset_bot, many=True, context={'request': request})
        return Response({"bots": serializer.data})


class BotTg(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.BotTgSerializer
    queryset_bot = models.Bot.objects.filter()

    def get(self,  request, *args, **kwargs):
        bot = self.queryset_bot.filter(bot_id=kwargs['pk'])
        serializer = serializers.BotTgSerializer(bot, many=True, context={'request': request})
        return Response({"bot": serializer.data})

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"bot": serializer.data})

    def patch(self, request, *args, **kwargs):
        bot = get_object_or_404(self.queryset_bot, bot_id=kwargs['pk'])

        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(bot, request.data)
        bot = self.queryset_bot.filter(bot_id=kwargs['pk'])
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
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"user": serializer.data})

    def patch(self, request, *args, **kwargs):
        user = get_object_or_404(self.queryset, user_id=kwargs['pk'])
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, request.data)
        user = self.queryset.filter(user_id=kwargs['pk'])
        serializer = serializers.UserTgSerializer(user, many=True, context={'request': request})
        return Response({"user": serializer.data})


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


class UnlikeView(LikeView):
    permission_classes = [permissions.AllowAny]
    queryset_user = models.UserTg.objects.filter(is_active=True, is_ban=False, is_deleted=False)
    queryset_bot = models.Bot.objects.filter(is_active=True, is_ban=False, is_deleted=False)

    def post(self, request, *args, **kwargs):
        user_tg = get_object_or_404(self.queryset_user, user_id=self.kwargs['pk'])
        bot = get_object_or_404(self.queryset_bot, bot_id=self.kwargs['bot_pk'])
        try:
            like = models.BotLike.objects.get(user=user_tg, bot=bot)
            like.delete()
        except models.BotLike.DoesNotExist:
            return Response({"message": "Bot not like"}, status=status.HTTP_400_BAD_REQUEST)
        return Response()


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
