from django.contrib import admin

from core.models import Deal, UserTg, Bot, User, Ad, VerifyCode, Search, BotViews
# from .admin_site import CoreAdmin, site

admin.site.register(User)


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

    # list_display = ('id', 'username', 'first_name_en', 'first_name_ru', 'last_name_en', 'last_name_ru')


admin.site.register(Deal, DealAdmin)
admin.site.register(UserTg, UserTgAdmin)
admin.site.register(Bot, BotAdmin)
# site.register(User, UserIPhoneAdmin)
admin.site.register(Ad)
admin.site.register(VerifyCode)
admin.site.register(Search)
admin.site.register(BotViews)
