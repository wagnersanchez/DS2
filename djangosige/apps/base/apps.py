from __future__ import unicode_literals

from django.apps import AppConfig

class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangosige.apps.base'  # Nome completo do módulo
