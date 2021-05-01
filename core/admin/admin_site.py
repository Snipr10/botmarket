from django.contrib import admin
from django.urls import path, reverse

from .views import StatisticsView


class CoreAdmin(admin.AdminSite):
    index_template = 'admin/core_index.html'

    def get_app_list(self, request):
        """
        Return {} of apps
        :param request: Request
        :return: {}
        """

        return super().get_app_list(request)

    def get_urls(self):
        """
        Return admin api
        :return: []
        """
        urls = super().get_urls()
        custom_urls = [
            path('statistics/', self.admin_view(StatisticsView.as_view()), name='statistics'),

        ]
        return urls + custom_urls

    def get_extra_pages(self) -> dict:
        """Returns a dictionary of additional sections and pages to display on index page:
        extra_pages = {
            'Section name': {
                'Page name': page_url,
            },
        }
        """
        extra_pages = {
            'Statistics': {
                'All statistic': reverse('admin:statistics'),
            },

        }
        return extra_pages

    def index(self, request, extra_context=None):
        context = extra_context if extra_context is not None else {}
        context.update({
            'extra_pages': self.get_extra_pages(),
        })
        return super().index(request, extra_context=context)


site = CoreAdmin(name='coreadmin')
