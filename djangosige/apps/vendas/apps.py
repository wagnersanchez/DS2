from __future__ import unicode_literals

from django.apps import AppConfig


class VendasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangosige.apps.vendas'  # Nome completo do módulo
    verbose_name = "Vendas"  # Opcional
