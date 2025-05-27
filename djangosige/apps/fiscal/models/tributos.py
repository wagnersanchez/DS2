# djangosige/apps/fiscal/models/tributos.py
# -*- coding: utf-8 -*-

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import re

# CHOICES
UF_SIGLA = [
    ('AC', 'AC'), ('AL', 'AL'), ('AP', 'AP'), ('AM', 'AM'), ('BA', 'BA'),
    ('CE', 'CE'), ('DF', 'DF'), ('ES', 'ES'), ('EX', 'EX'), ('GO', 'GO'),
    ('MA', 'MA'), ('MT', 'MT'), ('MS', 'MS'), ('MG', 'MG'), ('PA', 'PA'),
    ('PB', 'PB'), ('PR', 'PR'), ('PE', 'PE'), ('PI', 'PI'), ('RJ', 'RJ'),
    ('RN', 'RN'), ('RS', 'RS'), ('RO', 'RO'), ('RR', 'RR'), ('SC', 'SC'),
    ('SP', 'SP'), ('SE', 'SE'), ('TO', 'TO'),
]

CST_ICMS_ESCOLHAS = (
    ('00', _('00 - Tributada integralmente')),
    ('10', _('10 - Tributada e com cobrança do ICMS por substituição tributária')),
    # ('10p', _('10 - Tributada e com cobrança do ICMS por substituição tributária (com partilha do ICMS)')),
    ('20', _('20 - Com redução de base de cálculo')),
    ('30', _('30 - Isenta ou não tributada e com cobrança do ICMS por substituição tributária')),
    ('40', _('40 - Isenta')),
    ('41', _('41 - Não tributada')),
    # ('41r', _('41 - Não tributada (ICMS ST devido para a UF de destino...)')),
    ('50', _('50 - Suspensão')),
    ('51', _('51 - Diferimento')),
    ('60', _('60 - ICMS cobrado anteriormente por substituição tributária')),
    ('70', _('70 - Com redução de base de cálculo e cobrança do ICMS por substituição tributária')),
    # ('90p', _('90 - Outros (com partilha do ICMS)')),
    ('90', _('90 - Outros')),
)

CST_IPI_ESCOLHAS = (
    ('00', _('00 - Entrada com Recuperação de Crédito')), ('01', _('01 - Entrada Tributável com Alíquota Zero')),
    ('02', _('02 - Entrada Isenta')), ('03', _('03 - Entrada Não-Tributada')),
    ('04', _('04 - Entrada Imune')), ('05', _('05 - Entrada com Suspensão')),
    ('49', _('49 - Outras Entradas')), ('50', _('50 - Saída Tributada')),
    ('51', _('51 - Saída Tributável com Alíquota Zero')), ('52', _('52 - Saída Isenta')),
    ('53', _('53 - Saída Não-Tributada')), ('54', _('54 - Saída Imune')),
    ('55', _('55 - Saída com Suspensão')), ('99', _('99 - Outras Saídas')),
)

CST_PIS_COFINS_ESCOLHAS = (
    ('01', _('01 - Operação Tributável com Alíquota Básica')),
    ('02', _('02 - Operação Tributável com Alíquota Diferenciada')),
    ('03', _('03 - Operação Tributável com Alíquota por Unidade de Medida de Produto')),
    ('04', _('04 - Operação Tributável Monofásica - Revenda a Alíquota Zero')),
    ('05', _('05 - Operação Tributável por Substituição Tributária')),
    ('06', _('06 - Operação Tributável a Alíquota Zero')),
    ('07', _('07 - Operação Isenta da Contribuição')),
    ('08', _('08 - Operação sem Incidência da Contribuição')),
    ('09', _('09 - Operação com Suspensão da Contribuição')),
    ('49', _('49 - Outras Operações de Saída')),
    ('50', _('50 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno')),
    ('51', _('51 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno')),
    ('52', _('52 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita de Exportação')),
    ('53', _('53 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno')),
    ('54', _('54 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas no Mercado Interno e de Exportação')),
    ('55', _('55 - Operação com Direito a Crédito - Vinculada a Receitas Não Tributadas no Mercado Interno e de Exportação')),
    ('56', _('56 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno e de Exportação')),
    ('60', _('60 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Tributada no Mercado Interno')),
    ('61', _('61 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno')),
    ('62', _('62 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação')),
    ('63', _('63 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno')),
    ('64', _('64 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação')),
    ('65', _('65 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação')),
    ('66', _('66 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno e de Exportação')),
    ('67', _('67 - Crédito Presumido - Outras Operações')),
    ('70', _('70 - Operação de Aquisição sem Direito a Crédito')),
    ('71', _('71 - Operação de Aquisição com Isenção')),
    ('72', _('72 - Operação de Aquisição com Suspensão')),
    ('73', _('73 - Operação de Aquisição a Alíquota Zero')),
    ('74', _('74 - Operação de Aquisição sem Incidência da Contribuição')),
    ('75', _('75 - Operação de Aquisição por Substituição Tributária')),
    ('98', _('98 - Outras Operações de Entrada')),
    ('99', _('99 - Outras Operações')),
)

CSOSN_ESCOLHAS = (
    ('101', _('101 - Tributada pelo Simples Nacional com permissão de crédito')),
    ('102', _('102 - Tributada pelo Simples Nacional sem permissão de crédito')),
    ('103', _('103 - Isenção do ICMS no Simples Nacional para faixa de receita bruta')),
    ('201', _('201 - Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por Substituição Tributária')),
    ('202', _('202 - Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por Substituição Tributária')),
    ('203', _('203 - Isenção do ICMS no Simples Nacional para faixa de receita bruta e com cobrança do ICMS por Substituição Tributária')),
    ('300', _('300 - Imune')),
    ('400', _('400 - Não tributada pelo Simples Nacional')),
    ('500', _('500 - ICMS cobrado anteriormente por substituição tributária (substituído) ou por antecipação')),
    ('900', _('900 - Outros')),
)

MOD_BCST_ESCOLHAS = (
    ('0', _('0 - Preço tabelado ou máximo sugerido')), 
    ('1', _('1 - Lista Negativa (valor)')),
    ('2', _('2 - Lista Positiva (valor)')), 
    ('3', _('3 - Lista Neutra (valor)')),
    ('4', _('4 - Margem Valor Agregado (%)')), 
    ('5', _('5 - Pauta (valor)')),
    ('6', _('6 - Valor da Operação')),
)

MOD_BC_ESCOLHAS = (
    ('0', _('0 - Margem Valor Agregado (%)')), 
    ('1', _('1 - Pauta (Valor)')),
    ('2', _('2 - Preço Tabelado Máx. (valor)')), 
    ('3', _('3 - Valor da operação')),
)

MOT_DES_ICMS_ESCOLHAS = ( 
    ('1', _('1 - Táxi')), 
    ('3', _('3 - Produtor Agropecuário')),
    ('4', _('4 - Frotista/Locadora')), 
    ('5', _('5 - Diplomático/Consular')),
    ('6', _('6 - Utilitários e Motocicletas da Amazônia Ocidental e Áreas de Livre Comércio')),
    ('7', _('7 - SUFRAMA')), 
    ('8', _('8 - Venda a Órgão Público')),
    ('9', _('9 - Outros')), 
    ('10', _('10 - Deficiente Condutor')),
    ('11', _('11 - Deficiente Não Condutor')), 
    ('12', _('12 - Órgão de fomento e desenvolvimento agropecuário')),
    ('16', _('16 - Olimpíadas Rio 2016')),
)

P_ICMS_INTER_ESCOLHAS = (
    (Decimal('4.00'), '4%'),
    (Decimal('7.00'), '7%'),
    (Decimal('12.00'), '12%'),
)

P_ICMS_INTER_PART_ESCOLHAS = (
    (Decimal('40.00'), '40% (2016)'), 
    (Decimal('60.00'), '60% (2017)'),
    (Decimal('80.00'), '80% (2018)'), 
    (Decimal('100.00'), '100% (a partir de 2019)'),
)

TIPO_IPI_ESCOLHAS = ( # Constante definida aqui
    ('0', _('Não sujeito ao IPI')),
    ('1', _('Valor por Unidade')), 
    ('2', _('Alíquota Percentual')),   
)

class TributoICMS(models.Model):
    item_nota_fiscal = models.OneToOneField(
        'fiscal.ItemNotaFiscal',
        verbose_name=_('Item da Nota Fiscal'),
        on_delete=models.CASCADE,
        related_name='icms', 
        null=True, blank=True 
    )
    grupo_fiscal = models.ForeignKey(
        'fiscal.GrupoFiscal', 
        verbose_name=_('Grupo Fiscal de Origem (Opcional)'),
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='configs_icms',
        help_text=_("Grupo fiscal usado para preencher valores padrão para este tributo.")
    )
    cst = models.CharField(_('CST ICMS (Regime Normal)'), max_length=3, choices=CST_ICMS_ESCOLHAS, null=True, blank=True, help_text=_('Código de Situação Tributária do ICMS.'))
    csosn = models.CharField(_('CSOSN (Simples Nacional)'), max_length=3, choices=CSOSN_ESCOLHAS, null=True, blank=True, help_text=_('Código de Situação da Operação no Simples Nacional.'))
    origem_mercadoria = models.CharField(_('Origem da Mercadoria'), max_length=1, default='0', help_text=_("0-Nacional, 1-Estrangeira Direta, 2-Estrangeira Interna, etc.")) 
    
    mod_bc = models.CharField(_('Modalidade BC ICMS'), max_length=1, choices=MOD_BC_ESCOLHAS, null=True, blank=True)
    p_icms = models.DecimalField(_('Alíquota ICMS (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    p_red_bc = models.DecimalField(_('Redução Base Cálculo ICMS (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    
    mod_bcst = models.CharField(_('Modalidade BC ICMS ST'), max_length=1, choices=MOD_BCST_ESCOLHAS, null=True, blank=True)
    p_mvast = models.DecimalField(_('MVA ICMS ST (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    p_red_bcst = models.DecimalField(_('Redução Base Cálculo ICMS ST (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    p_icmsst = models.DecimalField(_('Alíquota ICMS ST (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    
    mot_des_icms = models.CharField(_('Motivo Desoneração ICMS'), max_length=2, choices=MOT_DES_ICMS_ESCOLHAS, null=True, blank=True) 
    p_dif = models.DecimalField(_('Percentual Diferimento ICMS (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    p_bc_op = models.DecimalField(_('Percentual BC Operação Própria (ICMS Partilha) (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    ufst = models.CharField(_('UF Destino ICMS ST'), max_length=2, choices=UF_SIGLA, null=True, blank=True, help_text=_('UF para qual é devido o ICMS ST'))
    
    icms_incluido_preco = models.BooleanField(_('ICMS Incluso no Preço?'), default=False)
    icmsst_incluido_preco = models.BooleanField(_('ICMS ST Incluso no Preço?'), default=False)
    
    p_cred_sn = models.DecimalField(_('Alíquota Crédito Simples Nacional (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))]) 
    
    valor_bc = models.DecimalField(_('Valor Base de Cálculo ICMS (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_icms = models.DecimalField(_('Valor ICMS (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_bc_st = models.DecimalField(_('Valor Base de Cálculo ICMS ST (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_st = models.DecimalField(_('Valor ICMS ST (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_icms_desonerado = models.DecimalField(_('Valor ICMS Desonerado (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_fcp = models.DecimalField(_('Valor FCP (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_fcp_st = models.DecimalField(_('Valor FCP ST (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_fcp_st_retido = models.DecimalField(_('Valor FCP ST Retido Anteriormente (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_credito_icms_sn = models.DecimalField(_('Valor Crédito ICMS SN (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Tributo ICMS (Item)")
        verbose_name_plural = _("Tributos ICMS (Itens)")

    def __str__(self):
        item_info = f"Item {self.item_nota_fiscal.ordem}" if self.item_nota_fiscal else "Config Padrão"
        return f"ICMS {item_info} para {self.grupo_fiscal} - CST/CSOSN: {self.cst or self.csosn}"


class TributoICMSUFDest(models.Model):
    item_nota_fiscal = models.OneToOneField( 
        'fiscal.ItemNotaFiscal',
        verbose_name=_('Item da Nota Fiscal'),
        on_delete=models.CASCADE,
        related_name='icms_uf_dest',
        null=True, blank=True
    )
    grupo_fiscal = models.ForeignKey(
        'fiscal.GrupoFiscal', 
        verbose_name=_('Grupo Fiscal de Origem (Opcional)'),
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='configs_icms_ufdest'
    )
    p_fcp_dest = models.DecimalField(_('% FCP Destino'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    p_icms_dest = models.DecimalField(_('Alíquota ICMS Destino (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    p_icms_inter = models.DecimalField(_('Alíquota Interestadual (%)'), max_digits=7, decimal_places=4, choices=P_ICMS_INTER_ESCOLHAS, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    p_icms_inter_part = models.DecimalField(_('% Partilha ICMS Interestadual'), max_digits=7, decimal_places=4, choices=P_ICMS_INTER_PART_ESCOLHAS, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    valor_bc_uf_dest = models.DecimalField(_('Valor BC UF Destino (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_fcp_uf_dest = models.DecimalField(_('Valor FCP UF Destino (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_icms_uf_dest = models.DecimalField(_('Valor ICMS UF Destino (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_icms_uf_remet = models.DecimalField(_('Valor ICMS UF Remetente (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Tributo ICMS UF Destino (Item)")
        verbose_name_plural = _("Tributos ICMS UF Destino (Itens)")

    def __str__(self):
        item_info = f"Item {self.item_nota_fiscal.ordem}" if self.item_nota_fiscal else "Config Padrão"
        return f"ICMS UF Destino {item_info} para {self.grupo_fiscal}"

class TributoICMSSN(models.Model): 
    item_nota_fiscal = models.OneToOneField( 
        'fiscal.ItemNotaFiscal',
        verbose_name=_('Item da Nota Fiscal'),
        on_delete=models.CASCADE,
        related_name='icms_sn',
        null=True, blank=True
    )
    grupo_fiscal = models.ForeignKey(
        'fiscal.GrupoFiscal', 
        verbose_name=_('Grupo Fiscal de Origem (Opcional)'),
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='configs_icms_sn'
    )
    csosn = models.CharField(_('CSOSN'), max_length=3, choices=CSOSN_ESCOLHAS, help_text='Código de Situação da Operação – Simples Nacional')
    p_cred_sn = models.DecimalField(_('Alíquota Crédito Simples Nacional (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))])
    mod_bc = models.CharField(_('Modalidade BC (SN)'), max_length=1, choices=MOD_BC_ESCOLHAS, null=True, blank=True)
    p_icms = models.DecimalField(_('Alíquota ICMS (SN) (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    p_red_bc = models.DecimalField(_('Redução Base Cálculo (SN) (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    icmssn_incluido_preco = models.BooleanField(_('ICMS SN Incluso no Preço?'), default=False)
    icmssnst_incluido_preco = models.BooleanField(_('ICMS ST SN Incluso no Preço?'), default=False)
    mod_bcst = models.CharField(_('Modalidade BC ST (SN)'), max_length=1, choices=MOD_BCST_ESCOLHAS, null=True, blank=True)
    p_mvast = models.DecimalField(_('MVA ST (SN) (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    p_red_bcst = models.DecimalField(_('Redução Base Cálculo ST (SN) (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    p_icmsst = models.DecimalField(_('Alíquota ICMS ST (SN) (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    valor_credito_icms_sn = models.DecimalField(_('Valor Crédito ICMS SN (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_bc_st_sn = models.DecimalField(_('Valor BC ST SN (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00')) 
    valor_icms_st_sn = models.DecimalField(_('Valor ICMS ST SN (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Tributo ICMS Simples Nacional (Item)")
        verbose_name_plural = _("Tributos ICMS Simples Nacional (Itens)")

    def __str__(self):
        item_info = f"Item {self.item_nota_fiscal.ordem}" if self.item_nota_fiscal else "Config Padrão"
        return f"ICMS SN {item_info} para {self.grupo_fiscal} - CSOSN: {self.csosn}"

class TributoIPI(models.Model):
    item_nota_fiscal = models.OneToOneField( 
        'fiscal.ItemNotaFiscal',
        verbose_name=_('Item da Nota Fiscal'),
        on_delete=models.CASCADE,
        related_name='ipi',
        null=True, blank=True
    )
    grupo_fiscal = models.ForeignKey(
        'fiscal.GrupoFiscal', 
        verbose_name=_('Grupo Fiscal de Origem (Opcional)'),
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='configs_ipi'
    )
    cst = models.CharField(_('CST IPI'), max_length=2, choices=CST_IPI_ESCOLHAS, null=True, blank=True)
    cl_enq = models.CharField(_('Classe Enquadramento IPI'), max_length=5, null=True, blank=True)
    c_enq = models.CharField(_('Código Enquadramento IPI'), max_length=3, null=True, blank=True, default='999')
    cnpj_prod = models.CharField(_('CNPJ Produtor IPI'), max_length=14, null=True, blank=True)
    tipo_ipi = models.CharField(_('Tipo Cálculo IPI'), max_length=1, choices=TIPO_IPI_ESCOLHAS, default='2')
    p_ipi = models.DecimalField(_('Alíquota IPI (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    valor_fixo_ipi = models.DecimalField( 
        _('Valor IPI por Unidade Tributável (R$)'),
        max_digits=15, decimal_places=4, 
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))], 
        null=True, blank=True
    ) 
    ipi_incluido_preco = models.BooleanField(_('IPI Incluso no Preço?'), default=False)
    incluir_bc_icms = models.BooleanField(_('IPI na BC ICMS?'), default=False)
    incluir_bc_icmsst = models.BooleanField(_('IPI na BC ICMS ST?'), default=False)
    valor_bc = models.DecimalField(_('Valor Base de Cálculo IPI (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_ipi = models.DecimalField(_('Valor IPI (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Tributo IPI (Item)")
        verbose_name_plural = _("Tributos IPI (Itens)")

    def get_cnpj_prod_apenas_digitos(self):
        if self.cnpj_prod:
            return re.sub(r'[^0-9]', '', self.cnpj_prod)
        return None
    
    def __str__(self):
        item_info = f"Item {self.item_nota_fiscal.ordem}" if self.item_nota_fiscal else "Config Padrão"
        return f"IPI {item_info} para {self.grupo_fiscal} - CST: {self.cst}"

class TributoPIS(models.Model):
    item_nota_fiscal = models.OneToOneField( 
        'fiscal.ItemNotaFiscal',
        verbose_name=_('Item da Nota Fiscal'),
        on_delete=models.CASCADE,
        related_name='pis',
        null=True, blank=True
    )
    grupo_fiscal = models.ForeignKey(
        'fiscal.GrupoFiscal', 
        verbose_name=_('Grupo Fiscal de Origem (Opcional)'),
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='configs_pis'
    )
    cst = models.CharField(_('CST PIS'), max_length=2, choices=CST_PIS_COFINS_ESCOLHAS, null=True, blank=True)
    p_pis = models.DecimalField(_('Alíquota PIS (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    valiq_pis = models.DecimalField( 
        _('Valor Alíquota PIS por Unidade (R$)'),
        max_digits=15, decimal_places=4, 
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))], 
        null=True, blank=True
    )
    valor_bc = models.DecimalField(_('Valor Base de Cálculo PIS (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_pis = models.DecimalField(_('Valor PIS (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Tributo PIS (Item)")
        verbose_name_plural = _("Tributos PIS (Itens)")

    def __str__(self):
        item_info = f"Item {self.item_nota_fiscal.ordem}" if self.item_nota_fiscal else "Config Padrão"
        return f"PIS {item_info} para {self.grupo_fiscal} - CST: {self.cst}"

class TributoCOFINS(models.Model):
    item_nota_fiscal = models.OneToOneField( 
        'fiscal.ItemNotaFiscal',
        verbose_name=_('Item da Nota Fiscal'),
        on_delete=models.CASCADE,
        related_name='cofins',
        null=True, blank=True
    )
    grupo_fiscal = models.ForeignKey(
        'fiscal.GrupoFiscal', 
        verbose_name=_('Grupo Fiscal de Origem (Opcional)'),
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='configs_cofins'
    )
    cst = models.CharField(_('CST COFINS'), max_length=2, choices=CST_PIS_COFINS_ESCOLHAS, null=True, blank=True)
    p_cofins = models.DecimalField(_('Alíquota COFINS (%)'), max_digits=7, decimal_places=4, default=Decimal('0.0000'), validators=[MinValueValidator(Decimal('0.00'))], null=True, blank=True)
    valiq_cofins = models.DecimalField( 
        _('Valor Alíquota COFINS por Unidade (R$)'),
        max_digits=15, decimal_places=4, 
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))], 
        null=True, blank=True
    )
    valor_bc = models.DecimalField(_('Valor Base de Cálculo COFINS (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_cofins = models.DecimalField(_('Valor COFINS (Item)'), max_digits=15, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Tributo COFINS (Item)")
        verbose_name_plural = _("Tributos COFINS (Itens)")

    def __str__(self):
        item_info = f"Item {self.item_nota_fiscal.ordem}" if self.item_nota_fiscal else "Config Padrão"
        return f"COFINS {item_info} para {self.grupo_fiscal} - CST: {self.cst}"
