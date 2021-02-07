import datetime
from typing import List

from django.conf import settings

from rest_framework import exceptions, serializers, status
from rest_framework.exceptions import ParseError
from rest_framework.fields import set_value

from . import models
from .models import BotLike


class BotTgSerializer(serializers.ModelSerializer):
    bot_id = serializers.IntegerField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_user = serializers.BooleanField()
    is_active = serializers.BooleanField()
    is_ban = serializers.BooleanField()
    is_deleted = serializers.BooleanField()
    is_reply = serializers.BooleanField()
    ready_to_use = serializers.BooleanField()
    tags = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    description = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def update(self, bot, validated_data):
        bot.username = validated_data.get("username", bot.username)
        bot.first_name = validated_data.get("first_name", bot.first_name)
        bot.last_name = validated_data.get("last_name", bot.last_name)
        bot.description = validated_data.get("description", bot.description)
        bot.tags = validated_data.get("tags", bot.tags)
        bot.is_user = validated_data.get("is_user", bot.is_user)
        bot.is_active = validated_data.get("is_active", bot.is_active)
        bot.is_ban = validated_data.get("is_ban", bot.is_ban)
        bot.is_deleted = validated_data.get("is_deleted", bot.is_deleted)
        bot.is_reply = validated_data.get("is_reply", bot.is_reply)
        bot.ready_to_use = validated_data.get("ready_to_use", bot.ready_to_use)
        return bot.save()

    class Meta:
        model = models.Bot
        fields = ("bot_id", "username", "first_name", "last_name", "is_user", "is_active",
                  "is_ban", "is_deleted", "is_reply", "ready_to_use", "tags", "description")


class UserTgSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_active = serializers.BooleanField()
    is_ban = serializers.BooleanField()
    is_deleted = serializers.BooleanField()

    def update(self, user, validated_data):
        user.username = validated_data.get("username", user.username)
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.is_active = validated_data.get("is_active", user.is_active)
        user.is_ban = validated_data.get("is_ban", user.is_ban)
        user.is_deleted = validated_data.get("is_deleted", user.is_deleted)
        return user.save()

    class Meta:
        model = models.UserTg
        fields = ("user_id", "username", "first_name", "last_name", "is_active", "is_ban", "is_deleted")


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserTg
        fields = ("user_id", "username", "first_name", "last_name")


def get_user(user):
    return {"user_id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username
            }


class LikesSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, bot_like):
        return get_user(bot_like.user)

    class Meta:
        model = BotLike
        fields = ('id', 'user', 'datetime')


class CommentsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, bot_comment):
        return get_user(bot_comment.user)

    class Meta:
        model = models.BotComment
        fields = ('id', 'user', 'datetime', 'text')
