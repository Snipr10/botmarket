from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class CoreConfig(AppConfig):
    name = 'core'


class CoreAdminConfig(AdminConfig):
    default_site = 'core.admin.CoreAdmin'
