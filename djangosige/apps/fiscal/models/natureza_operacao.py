# djangosige/apps/fiscal/models/natureza_operacao.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class NaturezaOperacao(models.Model):
    TIPO_OPERACAO_CHOICES = [
        ('E', 'Entrada'),
        ('S', 'Saída'),
    ]
    
    codigo = models.CharField(
        _('Código'), 
        max_length=10, 
        unique=True, 
        null=True, 
        blank=True # Permite que o código seja opcional inicialmente
    )
    # CORRIGIDO: Adicionado default='' para o campo descrição
    descricao = models.CharField(
        _('Descrição'), 
        max_length=100,
        default='' # Garante que novas instâncias e migrações tenham um valor
    )
    
    tipo_operacao = models.CharField(
        _('Tipo de Operação'),
        max_length=1,
        choices=TIPO_OPERACAO_CHOICES,
        null=True, 
        blank=True,
    )
    regime_especial = models.BooleanField(_('Regime Especial'), default=False)
    incentivo_fiscal = models.BooleanField(_('Incentivo Fiscal'), default=False)
    ativo = models.BooleanField(_('Ativo'), default=True)
    
    class Meta:
        verbose_name = "Natureza de Operação"
        verbose_name_plural = "Naturezas de Operação"
        ordering = ['descricao']
    
    def __str__(self):
        return f"{self.codigo or 'S/C'} - {self.descricao}"
    
    # Este método to_edoc() era para a estrutura anterior com erpbrasil.edoc.
    # Ao usar nfelib diretamente no modelo NotaFiscal, o campo `descricao`
    # será acessado diretamente (self.natureza_operacao.descricao).
    # Considere remover ou adaptar este método se ele não for mais usado.
    def to_edoc(self):
        return self.descricao

    @property
    def tipo_operacao_nfelib(self):
        """
        Retorna o valor para o campo tpNF da NFe ('0' para Entrada, '1' para Saída).
        """
        if self.tipo_operacao == 'E':
            return '0' # Entrada
        elif self.tipo_operacao == 'S':
            return '1' # Saída
        return None # Ou um valor padrão se tipo_operacao for None
