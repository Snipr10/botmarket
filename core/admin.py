from django.contrib import admin
from django.contrib.auth.models import User

from core.models import Deal, UserTg, Bot, BotLike, BotRating, BotComment, Ad, VerifyCode, IphoneTop, IphoneSearch, \
    BotViews


class DealAdmin(admin.ModelAdmin):
    list_filter = ('is_active',)
    list_display = ('id', 'user', 'is_active',)


class UserTgAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name')


class BotAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name_en', 'first_name_ru', 'last_name_en', 'last_name_ru')

    # list_display = ('id', 'username', 'first_name_en', 'first_name_ru', 'last_name_en', 'last_name_ru')


admin.site.register(Deal, DealAdmin)
admin.site.register(UserTg, UserTgAdmin)
admin.site.register(Bot, BotAdmin)

admin.site.register(Ad)
admin.site.register(VerifyCode)
admin.site.register(IphoneTop)
admin.site.register(IphoneSearch)
admin.site.register(BotViews)
admin.site.register(User)


