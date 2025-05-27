# djangosige/apps/fiscal/models/tributo_icms.py
# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

# Presume-se que o modelo GrupoFiscal já está definido e importado no __init__.py
# from .grupo_fiscal import GrupoFiscal # Se necessário para type hinting ou lógica específica

# Defina CHOICES para campos como cst, mod_bc, mot_des_icms, ufst aqui ou importe de um arquivo de constantes
# Exemplo (simplificado, você precisará de todos os códigos válidos):
CST_ICMS_CHOICES = [
    ('00', '00 - Tributada integralmente'),
    ('10', '10 - Tributada e com cobrança do ICMS por ST'),
    ('20', '20 - Com redução de base de cálculo'),
    ('30', '30 - Isenta ou não tributada e com cobrança do ICMS por ST'),
    ('40', '40 - Isenta'),
    ('41', '41 - Não tributada'),
    ('50', '50 - Suspensão'),
    ('51', '51 - Diferimento'),
    ('60', '60 - ICMS cobrado anteriormente por ST'),
    ('70', '70 - Com redução de base de cálculo e cobrança do ICMS por ST'),
    ('90', '90 - Outras'),
    # Adicionar CSOSN para Simples Nacional
    ('101', '101 - Tributada pelo Simples Nacional com permissão de crédito'),
    ('102', '102 - Tributada pelo Simples Nacional sem permissão de crédito'),
    # ... etc
]

MOD_BC_ICMS_CHOICES = [
    ('0', '0 - Margem Valor Agregado (%)'),
    ('1', '1 - Pauta (Valor)'),
    ('2', '2 - Preço Tabelado Máx. (valor)'),
    ('3', '3 - Valor da Operação'),
]

MOD_BC_ICMS_ST_CHOICES = [
    ('0', '0 - Preço tabelado ou máximo sugerido'),
    ('1', '1 - Lista Negativa (valor)'),
    ('2', '2 - Lista Positiva (valor)'),
    ('3', '3 - Lista Neutra (valor)'),
    ('4', '4 - Margem Valor Agregado (%)'),
    ('5', '5 - Pauta (valor)'),
    ('6', '6 - Valor da Operação'), # Adicionado conforme NT 2020.005
]

MOT_DES_ICMS_CHOICES = [
    ('1', '1 - Táxi'),
    ('3', '3 - Produtor Agropecuário'),
    ('7', '7 - SUFRAMA'),
    ('9', '9 - Outros'),
    ('12', '12 - Órgão de fomento e desenvolvimento agropecuário'),
    # Adicionar outros motivos
]

UF_CHOICES = [ # Exemplo, idealmente viria de um local mais completo ou de uma lib
    ('SP', 'São Paulo'), ('RJ', 'Rio de Janeiro'), ('MG', 'Minas Gerais'),
    # ... todas as UFs ...
]


class TributoICMS(models.Model):
    """
    Modelo para armazenar as configurações de ICMS,
    geralmente associado a um GrupoFiscal.
    """
    grupo_fiscal = models.OneToOneField( # Ou ForeignKey se um grupo pode ter várias configs de ICMS (raro)
        'fiscal.GrupoFiscal',
        verbose_name=_('Grupo Fiscal'),
        on_delete=models.CASCADE,
        related_name='config_icms' # ou apenas 'icms' se for OneToOne
    )

    # Campos que o ICMSForm espera:
    cst = models.CharField(
        _('CST/CSOSN ICMS'), 
        max_length=3, 
        choices=CST_ICMS_CHOICES, 
        null=True, blank=True
    )
    mod_bc = models.CharField(
        _('Modalidade de determinação da BC do ICMS'), 
        max_length=1, 
        choices=MOD_BC_ICMS_CHOICES, 
        null=True, blank=True
    )
    p_icms = models.DecimalField(
        _('Alíquota ICMS (%)'), 
        max_digits=7, decimal_places=4, # Ex: 18.0000%
        default=Decimal('0.0000'), 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    p_red_bc = models.DecimalField(
        _('% da Redução de BC'), 
        max_digits=7, decimal_places=4, 
        default=Decimal('0.0000'), 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    mod_bcst = models.CharField(
        _('Modalidade de determinação da BC do ICMS ST'), 
        max_length=1, 
        choices=MOD_BC_ICMS_ST_CHOICES, 
        null=True, blank=True
    )
    p_mvast = models.DecimalField(
        _('% Margem de valor Adicionado do ICMS ST'), 
        max_digits=7, decimal_places=4, 
        default=Decimal('0.0000'), 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    p_red_bcst = models.DecimalField(
        _('% da Redução de BC do ICMS ST'), 
        max_digits=7, decimal_places=4, 
        default=Decimal('0.0000'), 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    p_icmsst = models.DecimalField(
        _('Alíquota ICMS ST (%)'), 
        max_digits=7, decimal_places=4, 
        default=Decimal('0.0000'), 
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    mot_des_icms = models.CharField(
        _('Motivo da desoneração do ICMS'), 
        max_length=2, # Códigos numéricos
        choices=MOT_DES_ICMS_CHOICES, 
        null=True, blank=True
    )
    p_dif = models.DecimalField(
        _('% do diferimento'), 
        max_digits=7, decimal_places=4, 
        default=Decimal('0.0000'), 
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    p_bc_op = models.DecimalField(
        _('% da BC operação própria'), 
        max_digits=7, decimal_places=4, 
        default=Decimal('0.0000'), 
        validators=[MinValueValidator(Decimal('0.00'))] # Usado em ICMS Partilha
    )
    ufst = models.CharField( # Deveria ser uma ForeignKey para um modelo de UF ou usar choices
        _('UF para qual é devido o ICMS ST'), 
        max_length=2, 
        choices=UF_CHOICES, # Use choices mais completos
        null=True, blank=True
    )
    icms_incluido_preco = models.BooleanField(
        _('ICMS incluso no preço do produto/serviço?'), 
        default=False
    )
    icmsst_incluido_preco = models.BooleanField(
        _('ICMS-ST incluso no preço do produto/serviço?'), 
        default=False
    )

    # Campos que podem ser necessários para Simples Nacional (CSOSN)
    # Se você não for usar o ICMSSNForm separado, adicione-os aqui
    # csosn = models.CharField(_('CSOSN'), max_length=3, choices=CST_ICMS_CHOICES (filtrado para CSOSN), null=True, blank=True)
    # p_cred_sn = models.DecimalField(_('Alíquota aplicável de cálculo do crédito SN (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'))
    
    # Campos para ICMS UF Destino (Partilha)
    # Se não for usar ICMSUFDestForm separado, adicione-os aqui
    # p_fcp_dest = models.DecimalField(_('% FCP Destino'), max_digits=7, decimal_places=4, default=Decimal('0.0000'))
    # p_icms_dest = models.DecimalField(_('Alíquota interna UF Destino (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'))
    # p_icms_inter = models.DecimalField(_('Alíquota Interestadual (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000')) # Pode ter choices fixos (4, 7, 12)
    # p_icms_inter_part = models.DecimalField(_('% Partilha ICMS Destino'), max_digits=7, decimal_places=4, default=Decimal('0.0000')) # Ex: 100.0000 para 100%

    # Campos de valor (geralmente calculados no item da nota, mas podem ter defaults aqui)
    valor_bc = models.DecimalField(_('Valor Base de Cálculo ICMS'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_icms = models.DecimalField(_('Valor ICMS'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_bc_st = models.DecimalField(_('Valor Base de Cálculo ICMS ST'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_st = models.DecimalField(_('Valor ICMS ST'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_icms_desonerado = models.DecimalField(_('Valor ICMS Desonerado'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_fcp = models.DecimalField(_('Valor FCP'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_fcp_st = models.DecimalField(_('Valor FCP ST'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_fcp_st_retido = models.DecimalField(_('Valor FCP ST Retido'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)


    class Meta:
        verbose_name = _("Configuração de ICMS")
        verbose_name_plural = _("Configurações de ICMS")
        # Se um GrupoFiscal só pode ter uma config de ICMS, unique=True no OneToOneField já garante.
        # unique_together = ('grupo_fiscal', 'cst') # Se um grupo puder ter várias configs por CST

    def __str__(self):
        return f"ICMS para {self.grupo_fiscal.descricao} - CST/CSOSN: {self.cst or self.csosn or 'N/A'}"

    # O método to_edoc() para este modelo precisará ser refatorado para nfelib,
    # construindo o objeto Tnfe.InfNfe.Det.Imposto.Icms e seus grupos internos (ICMS00, ICMS10, etc.)
    def to_edoc(self):
        icms_nfelib_container = Tnfe.InfNfe.Det.Imposto.Icms()
        cst_csosn = self.cst # ou self.csosn se você unificar

        # Lógica para preencher o grupo correto dentro de icms_nfelib_container
        # Exemplo para ICMS00:
        if cst_csosn == '00':
            icms00 = Tnfe.InfNfe.Det.Imposto.Icms.Icms00()
            icms00.orig = Torig(self.origem_produto_fk.codigo_nfelib) # Supondo que você tem um campo origem no produto ou aqui
            icms00.CST = Icms00Cst(cst_csosn)
            icms00.modBC = Icms00ModBc(self.mod_bc)
            icms00.vBC = f"{self.valor_bc_calculado_no_item:.2f}" # Valor da BC do item
            icms00.pICMS = f"{self.p_icms:.4f}" 
            icms00.vICMS = f"{self.valor_icms_calculado_no_item:.2f}" # Valor do ICMS do item
            # Adicionar vFCP, pFCP se aplicável
            icms_nfelib_container.ICMS00 = icms00
        # Adicione elif para outros CSTs/CSOSN...
        
        return icms_nfelib_container
