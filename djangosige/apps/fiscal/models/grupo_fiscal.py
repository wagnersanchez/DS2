# djangosige/apps/fiscal/models/grupo_fiscal.py
# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import gettext_lazy as _

class GrupoFiscal(models.Model):
    """
    Modelo para cadastrar Grupos Fiscais.
    Um grupo fiscal define um conjunto de regras tributárias que podem ser aplicadas
    a um grupo de produtos.
    """
    descricao = models.CharField(
        _('Descrição do Grupo Fiscal'),
        max_length=100,
        unique=True, # Garante que cada descrição de grupo fiscal seja única
        help_text=_('Ex: Tributados Integralmente, Isentos, Substituição Tributária, etc.')
    )
    
    REGIME_TRIB_CHOICES = [
        ('0', 'Simples Nacional'),
        ('1', 'Simples Nacional - excesso de sublimite de receita bruta'),
        ('2', 'Regime Normal'),
        # Adicione outros regimes conforme necessário
    ]
    regime_trib = models.CharField(
        _('Regime Tributário'),
        max_length=1, # Ou o tamanho apropriado para seus códigos
        choices=REGIME_TRIB_CHOICES,
        null=True, # Permite que o campo seja nulo no banco de dados
        blank=True, # Permite que o campo seja opcional em formulários e no admin
        help_text=_('Selecione o regime tributário principal para este grupo fiscal.')
    )
    
    class Meta:
        verbose_name = _("Grupo Fiscal")
        verbose_name_plural = _("Grupos Fiscais")
        ordering = ['descricao']

    def __str__(self):
        return self.descricao
