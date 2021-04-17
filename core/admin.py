from django.contrib import admin

from core.models import Deal, UserTg, Bot, BotLike, BotRating, BotComment, Ad


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

admin.site.register(BotLike)
admin.site.register(BotRating)
admin.site.register(BotComment)
admin.site.register(Ad)

