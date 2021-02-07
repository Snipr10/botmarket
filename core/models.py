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
    is_active = models.BooleanField(default=True)
    is_ban = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)


class Bot(models.Model):
    bot_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_user = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_ban = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    ready_to_use = models.BooleanField(default=True)
    tags = models.CharField(max_length=4000)
    # maybe change max_length and create new table for description
    description = models.CharField(max_length=4000)


# todo is Needed?
# class BotView(models.Model):
#     user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
#     bot = models.ForeignKey(Bot, on_delete=models.CASCADE)


class BotLike(models.Model):
    user = models.ForeignKey(UserTg, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    like_datetime = models.DateTimeField(auto_now_add=True)


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
