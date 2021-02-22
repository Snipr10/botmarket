import datetime
from typing import List

from django.conf import settings

from rest_framework import exceptions, serializers, status
from rest_framework.exceptions import ParseError
from rest_framework.fields import set_value

from . import models
from .models import BotLike, Deal


class BotTgSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150, required=True)
    first_name_en = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name_ru = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name_en = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name_ru = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_user = serializers.BooleanField()
    is_active = serializers.BooleanField()
    is_ban = serializers.BooleanField()
    is_deleted = serializers.BooleanField()
    is_reply = serializers.BooleanField()
    ready_to_use = serializers.BooleanField()
    tags = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    description_ru = serializers.CharField(max_length=150, required=False, allow_blank=True)
    description_en = serializers.CharField(max_length=150, required=False, allow_blank=True)
    description = serializers.SerializerMethodField()

    def create(self, validated_data):
        bot = models.Bot.objects.create(**validated_data)
        user = self.context.get("user")
        bot.user = user
        bot.save()
        return bot

    def update(self, bot, validated_data):
        # bot.username = validated_data.get("username", bot.username)
        bot.first_name_en = validated_data.get("first_name_en", bot.first_name_en)
        bot.first_name_ru = validated_data.get("first_name_ru", bot.first_name_ru)
        bot.last_name_en = validated_data.get("last_name_en", bot.last_name_en)
        bot.last_name_ru = validated_data.get("last_name_ru", bot.last_name_ru)
        bot.phone = validated_data.get("phone", bot.phone)
        bot.description_rus = validated_data.get("description_ru", bot.description_rus)
        bot.description_eng = validated_data.get("description_en", bot.description_eng)
        bot.tags = validated_data.get("tags", bot.tags)
        bot.is_user = validated_data.get("is_user", bot.is_user)
        bot.is_deleted = validated_data.get("is_deleted", bot.is_deleted)
        bot.ready_to_use = validated_data.get("ready_to_use", bot.ready_to_use)

        # bot.is_active = validated_data.get("is_active", bot.is_active)
        # bot.is_ban = validated_data.get("is_ban", bot.is_ban)
        # bot.is_reply = validated_data.get("is_reply", bot.is_reply)

        return bot.save()

    def get_description(self, bot):
        language = self.context.get("language")
        if language == "ru":
            return bot.description_ru
        return bot.description_en

    class Meta:
        model = models.Bot
        fields = ("id", "username", "first_name_en", "first_name_ru", "last_name_ru", "last_name_en",
                  "phone", "is_user", "is_active", "description",
                  "is_ban", "is_deleted", "is_reply", "ready_to_use", "tags", "description_en", "description_ru")


class UserTgSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=150, required=False, allow_blank=True)
    is_active = serializers.BooleanField()
    is_ban = serializers.BooleanField()
    is_deleted = serializers.BooleanField()
    language = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def update(self, user, validated_data):
        user.username = validated_data.get("username", user.username)
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        user.phone = validated_data.get("phone", user.phone)
        user.language = validated_data.get("language", user.language)
        user.is_active = validated_data.get("is_active", user.is_active)
        user.is_ban = validated_data.get("is_ban", user.is_ban)
        user.is_deleted = validated_data.get("is_deleted", user.is_deleted)
        return user.save()

    class Meta:
        model = models.UserTg
        fields = ("user_id", "username", "first_name", "last_name", "phone", "is_active", "is_ban", "is_deleted",
                  "language")


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserTg
        fields = ("user_id", "username", "first_name", "last_name", "phone")


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


class DealSerializer(serializers.ModelSerializer):

    class Meta:
        model = Deal
        fields = '__all__'

