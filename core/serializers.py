import datetime
from rest_framework import exceptions, generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework import serializers, status

from botmarket.settings import BACKEND_URL
from . import models
from .elastic.elastic import delete_from_elastic, add_to_elastic_bot_model
from .models import BotLike, Deal


class BotsListSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    username = serializers.CharField(max_length=150, required=False)
    first_name_en = serializers.CharField(max_length=150, required=False)
    first_name_ru = serializers.CharField(max_length=150, required=False)
    last_name_en = serializers.CharField(max_length=150, required=False)
    last_name_ru = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=150, required=False)
    is_user = serializers.BooleanField(default=False)
    is_active = serializers.BooleanField(default=True)
    tags = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    description_ru = serializers.CharField(max_length=4000, required=False)
    description_en = serializers.CharField(max_length=4000, required=False)

    def get_url(self, bot):
        pk = None
        try:
            pk = self.context.get("user").pk
        except AttributeError:
            pass
        url = "%s/tg/%s" % (BACKEND_URL, bot.username.replace("@", ""))
        if pk is not None:
            url = '%s?u=%s' % (url, pk)
        return url

    def update(self, bot, validated_data):
        bot.first_name_en = validated_data.get("first_name_en", bot.first_name_en)
        bot.first_name_ru = validated_data.get("first_name_ru", bot.first_name_ru)
        bot.last_name_en = validated_data.get("last_name_en", bot.last_name_en)
        bot.last_name_ru = validated_data.get("last_name_ru", bot.last_name_ru)
        bot.phone = validated_data.get("phone", bot.phone)
        bot.description_ru = validated_data.get("description_ru", bot.description_ru)
        bot.description_en = validated_data.get("description_en", bot.description_en)
        bot.tags = validated_data.get("tags", bot.tags)
        bot.is_user = validated_data.get("is_user", bot.is_user)
        bot.is_active = validated_data.get("is_active", bot.is_active)

        return bot.save()

    class Meta:
        model = models.Bot
        fields = ("id", "username", "first_name_en", "first_name_ru", "last_name_ru", "last_name_en",
                  "phone", "is_user", "is_active",
                  "is_ban", "is_deleted", "is_reply", "ready_to_use", "tags", "description_en", "description_ru", "url")


class BotTgSerializer(BotsListSerializer):
    description = serializers.SerializerMethodField()

    def create(self, validated_data):
        bot = models.Bot.objects.create(**validated_data)
        user = self.context.get("user")
        bot.user = user
        bot.save()
        return bot

    def get_description(self, bot):
        try:
            language = self.context.get("language")
            if language == "ru":
                return bot.description_ru
        except AttributeError:
            pass
        return bot.description_en

    class Meta:
        model = models.Bot
        fields = ("id", "username", "first_name_en", "first_name_ru", "last_name_ru", "last_name_en",
                  "phone", "is_user", "is_active", "description",
                  "is_ban", "is_deleted", "is_reply", "ready_to_use", "tags", "description_en", "description_ru", "url")


class BotsListSerializerIphone(BotsListSerializer):
    url = serializers.SerializerMethodField()
    username = serializers.CharField(max_length=150, required=True)
    first_name_en = serializers.CharField(max_length=150, required=False)
    first_name_ru = serializers.CharField(max_length=150, required=False)
    last_name_en = serializers.CharField(max_length=150, required=False)
    last_name_ru = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=150, required=False)
    is_user = serializers.BooleanField(default=False)
    is_active = serializers.BooleanField(default=True)
    tags = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    description_ru = serializers.CharField(max_length=4000, required=False)
    description_en = serializers.CharField(max_length=4000, required=False)

    def create(self, validated_data):
        user_iphone = self.context["request"].user
        username = validated_data["username"]
        if models.Bot.objects.filter(username=username).exists():
            raise serializers.ValidationError("Bot already exist")
        instance = super().create(validated_data)
        instance.user_iphone = user_iphone
        instance.save()
        return instance

    def get_url(self, bot):
        pk = None
        try:
            pk = self.context.get("user").pk
        except AttributeError:
            pass
        url = "%s/tg/%s" % (BACKEND_URL, bot.username.replace("@", ""))
        if pk is not None:
            url = '%s?u=%s' % (url, pk)
        return url

    def update(self, instance, validated_data):
        instance.first_name_en = validated_data.get("first_name_en", instance.first_name_en)
        instance.first_name_ru = validated_data.get("first_name_ru", instance.first_name_ru)
        instance.last_name_en = validated_data.get("last_name_en", instance.last_name_en)
        instance.last_name_ru = validated_data.get("last_name_ru", instance.last_name_ru)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.description_ru = validated_data.get("description_ru", instance.description_ru)
        instance.description_en = validated_data.get("description_en", instance.description_en)
        instance.tags = validated_data.get("tags", instance.tags)
        instance.is_user = validated_data.get("is_user", instance.is_user)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        if instance.is_active and instance.is_deleted:
            instance.is_deleted = False
        if not instance.is_active:
            delete_from_elastic(instance.id)
        if instance.is_active:
            add_to_elastic_bot_model(instance)
        instance.save()
        return instance

    class Meta:
        model = models.Bot
        fields = ("id", "username", "first_name_en", "first_name_ru", "last_name_ru", "last_name_en",
                  "phone", "is_user", "is_active",
                  "is_ban", "is_deleted", "is_reply", "ready_to_use", "tags", "description_en", "description_ru", "url")


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


# IPHONE

class UserSignUpSerializer(serializers.ModelSerializer):
    phone_id = serializers.CharField(max_length=150)

    def create(self, validated_data):
        phone_id = validated_data["phone_id"]
        try:
            user = models.User.objects.get(phone_id=phone_id)
            # if user.is_active:
            #     raise serializers.ValidationError({"message": "User with this phone_id already exists"},
            #                                       status.HTTP_400_BAD_REQUEST)
        except models.User.DoesNotExist:
            user = models.User.objects.create_user(**validated_data)
        token, _ = Token.objects.get_or_create(user=user)
        return user, token

    class Meta:
        model = models.User
        fields = ("first_name", "last_name", "phone_id")


class SignInSerializer(serializers.Serializer):
    phone_id = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=150)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        try:
            user = models.User.objects.get(phone_id=validated_data["phone_id"], deleted=False)
        except models.User.DoesNotExist:
            raise exceptions.AuthenticationFailed({"message": "Unable to log in with provided credentials."})
        if not user.check_password(self.validated_data["password"]) or user.deleted:
            raise exceptions.AuthenticationFailed({"message": "Unable to log in with provided credentials."})
        elif not user.is_active:
            raise exceptions.AuthenticationFailed({"message": "User registration is not completed"})
        user.last_login = datetime.datetime.utcnow()
        user.save()
        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ("first_name", "last_name", "phone_id", "language")


class IphoneSearchSerializer(serializers.Serializer):
    tags = serializers.CharField(max_length=150)
    start = serializers.IntegerField(default=0)
    end = serializers.IntegerField(default=4)
    user = serializers.PrimaryKeyRelatedField(queryset=models.User.objects.all(), write_only=True)

    class Meta:
        model = models.IphoneSearch
        fields = ("tags", "start", "end", "user")
