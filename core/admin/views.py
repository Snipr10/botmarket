from core import models

from .forms import DataDisplayForm
from django.views import View
from django.shortcuts import render


class StatisticsView(View):
    """ Statistic of new users """
    template_name = 'admin/statistics.html'

    def get(self, request):
        """Api get"""

        data_fields = {
            'Users phone': (models.User.objects.all().count()),
            'Users tg': (models.UserTg.objects.all().count()),
            'Bots all': (models.Bot.objects.all().count()),
            'Bots ready to use': (models.Bot.objects.filter(ready_to_use=True).count()),
        }
        context = {
            'title': 'Statistics',
            'display_form': DataDisplayForm(data_fields=data_fields),
        }

        return render(request, self.template_name, context)
    