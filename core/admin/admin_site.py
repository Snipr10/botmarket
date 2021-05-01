from django.contrib import admin
from django.urls import path

from .views import StatisticsView


class CoreAdmin(admin.AdminSite):
    index_template = 'admin/core_index.html'

    def get_app_list(self, request):
        """
        Return {} of apps
        :param request: Request
        :return: {}
        """
        app_list = [
            {
                "name": "Controls",
                "models": [
                    {
                        "name": "Borrower",
                        "admin_url": "/admin/core/borroweruser/"
                    },
                    {
                        "name": "Loans",
                        "admin_url": "/admin/core/loan/"
                    },
                    {
                        "name": "Payments",
                        "admin_url": "/admin/payment/"
                    },
                    {
                        "name": "InvestLoan",
                        "admin_url": "/admin/invest_loan/"
                    }
                ],

            }
        ]
        app_list += super().get_app_list(request)

        return app_list

    def get_urls(self):
        """
        Return admin api
        :return: []
        """
        urls = super().get_urls()
        # custom_urls = [
        #     path('statistics/', self.admin_view(StatisticsView.as_view()), name='statistics'),
        #
        # ]
        return urls


site = CoreAdmin(name='coreadmin')
