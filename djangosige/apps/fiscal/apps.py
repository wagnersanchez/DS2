from __future__ import unicode_literals

from django.apps import AppConfig


class FiscalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangosige.apps.fiscal'  # Nome completo obrigatório
    verbose_name = "Fiscal"  # Opcional
