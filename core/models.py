import requests
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.
from botmarket.settings import SUPPORT_URL, SUPPORT_USER_URL
from core.elastic.elastic import delete_from_elastic


class UserManager(BaseUserManager):
    use_in_migrations = True


class UserTg(models.Model):
    user_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_ban = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    language = models.CharField(max_length=150, default="ru")

    # def __str__(self):
    #     return {"user_id": self.user_id,
    #            "first_name": self.first_name,
    #            "last_name": self.last_name,
    #            "username": self.username
    #            }
    def __str__(self):
        return str(self.user_id)


class Bot(models.Model):
    username = models.CharField(max_length=150, unique=True, blank=True)
    first_name_en = models.CharField(max_length=150, null=True, blank=True)
    first_name_ru = models.CharField(max_length=150, null=True, blank=True)
    last_name_en = models.CharField(max_length=150, null=True, blank=True)
    last_name_ru = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=150, null=True, blank=True)
    is_user = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_ban = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    ready_to_use = models.BooleanField(default=False)
    last_check = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=4000)
    # maybe change max_length and create new table for description
    description_ru = models.CharField(max_length=4000, null=True, blank=True)
    description_en = models.CharField(max_length=4000, null=True, blank=True)
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE, null=True, blank=True)
    all_warnings = models.IntegerField(default=0)
    # if bot active warnings = 0
    warnings = models.IntegerField(default=0)
    is_founded = models.BooleanField(default=True)
    is_being_checked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk is not None and (not self.is_active or not self.ready_to_use):
            try:
                delete_from_elastic(self.pk)
            except Exception as e:
                print(e)
                raise Exception(e)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            post_data = {
                "user_id": self.user.pk,
                "text": "Не могу отправить сообщение боту" + str(self.username)
            }
            response = requests.post(SUPPORT_USER_URL, json=post_data)
            if response.status_code != 200:
                print(response.text)
        except Exception as e:
            print(e)
        try:
            delete_from_elastic(self.pk)
        except Exception as e:
            print(e)
            raise Exception(e)
        super().delete(*args, **kwargs)

    def __str__(self):
        return str(self.username)


# todo is Needed?
# class BotView(models.Model):
#     user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
#     bot = models.ForeignKey(Bot, on_delete=models.CASCADE)


class BotLike(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user.username)


class BotRating(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user.username)


class BotComment(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=4000, blank=True)


class Deal(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    message_id = models.IntegerField()
    description = models.CharField(max_length=4000)
    is_active = models.BooleanField(default=True)
    answer = models.CharField(max_length=4000, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is not None and not self.is_active and self.answer is not None:
            try:
                post_data = {
                    "user_id": self.user.pk,
                    "message_id": self.message_id,
                    "text": self.answer
                }

                response = requests.post(SUPPORT_URL, json=post_data)
                if response.status_code != 200:
                    raise Exception(response.text)
            except Exception as e:
                print(e)
                raise Exception(e)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.pk)


class BotApi(models.Model):
    api_id = models.CharField(max_length=256)
    api_hash = models.CharField(max_length=256)

    def __str__(self):
        return str(self.api_id)


class Sessions(models.Model):
    session = models.FileField(upload_to='', null=True, blank=True)
    name = models.CharField(max_length=256)
    is_active = models.IntegerField(default=1, db_index=True)
    is_parsing = models.BooleanField(default=False)
    start_parsing = models.DateTimeField(null=True, blank=True)
    last_parsing = models.DateTimeField(null=True, blank=True)
    banned_until = models.DateTimeField(null=True, blank=True)
    # proxy_id = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    bot_api = models.ForeignKey(BotApi, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)