from core import models

from .forms import DataDisplayForm
from django.shortcuts import render
from django.views import View


class StatisticsView(View):
    """ Statistic of new users """
    template_name = 'admin/static_info.html'

    def get(self, request):
        """Api get"""

        data_fields = {
            'User Iphone': (models.User.objects.all()
                            .count()),
            'User tg': (models.UserTg.objects
                        .all()
                        .count()),

            'Bot': (
                models.Bot.objects.all().count()),
            'Bot ready to use': (
                models.Bot.objects.filter(ready_to_use=True).count()),

        }
        context = {
            'title': 'Statistics',
            'display_form': DataDisplayForm(data_fields=data_fields),
        }

        return render(request, self.template_name, context)
