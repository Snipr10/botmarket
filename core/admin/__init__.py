from django.contrib import admin

from core.models import Deal, UserTg, Bot, User, Ad, VerifyCode, Search, BotViews
from .admin_site import CoreAdmin, site

from django.contrib.auth.admin import Group, GroupAdmin
from rest_framework.authtoken.admin import Token, TokenAdmin

site.register(Group, GroupAdmin)
site.register(Token, TokenAdmin)


class DealAdmin(admin.ModelAdmin):
    list_filter = ('is_active',)
    list_display = ('id', 'user', 'is_active',)


class UserTgAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name')


class UserIPhoneAdmin(admin.ModelAdmin):
    list_display = ('phone_id', 'first_name', 'last_name')

    class Meta:
        verbose_name_plural = "User Iphone"


class BotAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name_en', 'first_name_ru', 'last_name_en', 'last_name_ru')
    search_fields = ['username']


class AdAdmin(admin.ModelAdmin):
    autocomplete_fields = ['bot']


site.register(Deal, DealAdmin)
site.register(UserTg, UserTgAdmin)
site.register(Bot, BotAdmin)
site.register(User, UserIPhoneAdmin)
site.register(Ad, AdAdmin)
site.register(VerifyCode)
site.register(Search)
site.register(BotViews)
