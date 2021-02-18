from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# Create your models here.

class UserManager(BaseUserManager):
    use_in_migrations = True


class UserTg(models.Model):
    user_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    username = models.CharField(max_length=150)
    phone = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_ban = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    language = models.CharField(max_length=150, default="ru")

    def __str__(self):
        return {"user_id": self.user_id,
               "first_name": self.first_name,
               "last_name": self.last_name,
               "username": self.username
               }


class Bot(models.Model):
    username = models.CharField(max_length=150, unique=True)
    first_name_en = models.CharField(max_length=150, null=True)
    first_name_ru = models.CharField(max_length=150, null=True)
    last_name_en = models.CharField(max_length=150, null=True)
    last_name_ru = models.CharField(max_length=150, null=True)
    phone = models.CharField(max_length=150)
    is_user = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_ban = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    ready_to_use = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=4000)
    # maybe change max_length and create new table for description
    description_ru = models.CharField(max_length=4000, null=True, blank=True)
    description_en = models.CharField(max_length=4000, null=True, blank=True)
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE, null=True, blank=True)


# todo is Needed?
# class BotView(models.Model):
#     user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
#     bot = models.ForeignKey(Bot, on_delete=models.CASCADE)


class BotLike(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)


class BotRating(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    datetime = models.DateTimeField(auto_now_add=True)


class BotComment(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=1000, blank=True)
