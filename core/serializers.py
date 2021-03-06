import datetime
import json
import re
from json import JSONDecodeError

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
    first_name_en = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    first_name_ru = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    last_name_en = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    last_name_ru = serializers.CharField(max_length=150, required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(max_length=150, required=False)
    is_user = serializers.BooleanField(default=False)
    is_active = serializers.BooleanField(default=True)
    tags = serializers.CharField(max_length=4000, required=False, allow_blank=True, default='[]')
    description_ru = serializers.CharField(max_length=4000, required=False, allow_blank=True, allow_null=True)
    description_en = serializers.CharField(max_length=4000, required=False, allow_blank=True, allow_null=True)
    status = serializers.SerializerMethodField()

    def get_status(self, bot):
        if not bot.is_founded:
            return {"code": 1, "message": "not founded"}
        if bot.ready_to_use:
            return {"code": 4, "message": "bot is working"}
        if not bot.ready_to_use:
            if bot.last_check is None:
                return {"code": 3, "message": "bot is not checked"}
            else:
                return {"code": 2, "message": "bot is not working"}
        return {"code": 1, "message": "not founded"}

    def generate_url(self, bot):
        pk = None
        user_type = "u"
        try:
            user = self.context.get("user")
            if type(self.context.get("user")) is models.User:
                user_type = "i"
            pk = user.pk
        except AttributeError:
            pass
        url = "%s/tg/%s" % (BACKEND_URL, bot.username.replace("@", ""))
        if pk is not None:
            url = '%s?%s=%s' % (url, user_type, pk)
        return url

    def get_url(self, bot):
        return self.generate_url(bot)

    def update(self, instance, validated_data):
        try:
            tags = json.loads(instance.tags.replace("\'", '"'))
        except Exception:
            tags = None
        instance.first_name_en = validated_data.get("first_name_en", instance.first_name_en)
        self.update_tags(tags, instance.first_name_en, validated_data.get("first_name_en", instance.first_name_en))
        instance.first_name_ru = validated_data.get("first_name_ru", instance.first_name_ru)
        self.update_tags(tags, instance.first_name_ru, validated_data.get("first_name_ru", instance.first_name_ru))
        instance.last_name_en = validated_data.get("last_name_en", instance.last_name_en)
        self.update_tags(tags, instance.last_name_en, validated_data.get("last_name_en", instance.last_name_en))
        instance.last_name_ru = validated_data.get("last_name_ru", instance.last_name_ru)
        self.update_tags(tags, instance.last_name_ru, validated_data.get("last_name_ru", instance.last_name_ru))
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
        instance.tags = tags
        self.check_data_content(instance)

        instance.save()
        return instance

    def bot_username_validation(self, username):
        if username.startswith("@"):
            validate_name = username[1:]
        else:
            validate_name = username
        if re.match("^[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)*$", validate_name):
            return username
        raise serializers.ValidationError({"message": "Bad username", "code": 4003})

    def update_tags(self, tags, new, old):
        try:
            tags.remove(old)
        except ValueError:
            pass
        if new is not None and new != "":
            tags.append(new)

    def add_name_to_tags(self, bot, tags):
        if bot.first_name_en is not None:
            self.update_tags(tags, bot.first_name_en, bot.first_name_en)
        if bot.first_name_ru is not None:
            self.update_tags(tags, bot.first_name_ru, bot.first_name_ru)
        if bot.last_name_ru is not None:
            self.update_tags(tags, bot.last_name_ru, bot.last_name_ru)
        if bot.last_name_en is not None:
            self.update_tags(tags, bot.last_name_en, bot.last_name_en)
        self.update_tags(tags, bot.username.replace("@", ""), bot.username.replace("@", ""))
        bot.tags = tags
        bot.save()

    list_age_restriction_18_word = ['poker', 'porn', 'порно', 'покер']
    list_download_type = ['movie', 'film', 'series', 'фильм', 'сериал', 'amazon', 'netflix']

    def check_data_content(self, instance):
        list_user_data = [instance.first_name_en, instance.first_name_ru, instance.last_name_ru, instance.last_name_en,
                          instance.description_ru, instance.description_en]
        for user_data in list_user_data:
            try:
                user_data_lower = user_data.lower()
                for age_restriction_18_word in self.list_age_restriction_18_word:
                    if age_restriction_18_word in user_data_lower:
                        instance.age_restriction_18 = True
                        break
            except Exception:
                pass
        if not instance.is_admin_check_content:
            for user_data in list_user_data:
                try:
                    user_data_lower = user_data.lower()
                    if 'download' in user_data_lower or 'скачать' in user_data_lower:
                        for download_type in self.list_download_type:
                            if download_type in user_data_lower and 'youtube' not in user_data_lower:
                                instance.is_for_display_iphone = False
                                break
                        if 'youtube' in user_data_lower or 'ютуб' in user_data_lower:
                            if 'music' in user_data_lower or 'музык':
                                instance.is_for_display_iphone = False
                                break
                except Exception:
                    pass

    class Meta:
        model = models.Bot
        fields = ("id", "username", "first_name_en", "first_name_ru", "last_name_ru", "last_name_en",
                  "phone", "is_user", "is_active", "status", "is_for_display_iphone", "age_restriction_18",
                  "is_ban", "is_deleted", "is_reply", "ready_to_use", "tags", "description_en", "description_ru",
                  "url",)


class BotTgSerializer(BotsListSerializer):
    description = serializers.SerializerMethodField()

    def create(self, validated_data):
        self.bot_username_validation(validated_data["username"])
        bot = models.Bot.objects.create(**validated_data)
        self.check_data_content(bot)
        user = self.context.get("user")
        bot.user = user
        bot.save()
        try:
            self.add_name_to_tags(bot, json.loads(bot.tags))
        except JSONDecodeError:
            self.add_name_to_tags(bot, [])

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
        fields = ("id", "username", "first_name_en", "first_name_ru", "last_name_ru", "last_name_en", "phone",
                  "is_user", "is_active", "description", "status", "is_for_display_iphone", "age_restriction_18",
                  "is_ban", "is_deleted", "is_reply", "ready_to_use", "tags", "description_en", "description_ru", "url")


class BotTgAdSerializer(BotTgSerializer):
    def get_url(self, bot):
        url = self.generate_url(bot)
        if "?" in url:
            pattern = '%s&a=%s'
        else:
            pattern = '%s?a=%s'
        return pattern % (url, self.context.get("ad"))


class BotsListSerializerIphone(BotsListSerializer):
    def create(self, validated_data):
        user_iphone = self.context["request"].user
        user_tg = models.UserTg.objects.filter(user_phone=user_iphone).first()
        # if user_tg is None:
        #     raise serializers.ValidationError({"message": "please, add user Tg", "code": 4001})
        username = self.bot_username_validation(validated_data["username"])
        if models.Bot.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError({"message": "Bot already exist", "code": 4002})
        instance = super().create(validated_data)
        self.add_name_to_tags(instance, json.loads(instance.tags))
        self.check_data_content(instance)
        if user_tg is None:
            instance.user_iphone = user_iphone
        else:
            instance.user = user_tg
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

    class Meta:
        model = models.Bot
        fields = ("id", "username", "first_name_en", "first_name_ru", "last_name_ru", "last_name_en",
                  "phone", "is_user", "is_active", "status", "is_for_display_iphone", "age_restriction_18",
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
            #     raise serializers.ValidationError({"message": "User with this phone_id already exists", "code": 4004})
        except models.User.DoesNotExist:
            user = models.User.objects.create_user(**validated_data)
        token, _ = Token.objects.get_or_create(user=user)
        return user, token

    class Meta:
        model = models.User
        fields = ("id", "first_name", "last_name", "phone_id", "language", "notification")


class SignInSerializer(serializers.Serializer):
    phone_id = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=150)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        try:
            user = models.User.objects.get(phone_id=validated_data["phone_id"], deleted=False)
        except models.User.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                {"message": "Unable to log in with provided credentials.", "code": 4011})
        if not user.check_password(self.validated_data["password"]) or user.deleted:
            raise exceptions.AuthenticationFailed(
                {"message": "Unable to log in with provided credentials.", "code": 4012})
        elif not user.is_active:
            raise exceptions.AuthenticationFailed({"message": "User registration is not completed", "code": 4013})
        user.last_login = datetime.datetime.utcnow()
        user.save()
        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ("first_name", "last_name", "phone_id", "language", "notification", "registration_id")
