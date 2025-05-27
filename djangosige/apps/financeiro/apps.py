from __future__ import unicode_literals

from django.apps import AppConfig


class FinanceiroConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangosige.apps.financeiro'  # Nome completo obrigatório
    verbose_name = "Financeiro"  # Opcional
