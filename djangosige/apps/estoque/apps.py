from __future__ import unicode_literals

from django.apps import AppConfig


class EstoqueConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangosige.apps.estoque'  # Nome completo obrigatório
    verbose_name = "Controle de Estoque"
