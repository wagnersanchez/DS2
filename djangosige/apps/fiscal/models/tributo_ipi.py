# djangosige/apps/fiscal/models/tributo_ipi.py
# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.core.validators import MinValueValidator

# Defina CHOICES para campos como cst_ipi, tipo_calculo_ipi aqui ou importe
# Exemplo (você precisará dos códigos válidos da NFe):
CST_IPI_CHOICES = [
    ('00', '00 - Entrada com recuperação de crédito'),
    ('01', '01 - Entrada tributada com alíquota zero'),
    ('02', '02 - Entrada isenta'),
    ('03', '03 - Entrada não-tributada'),
    ('04', '04 - Entrada imune'),
    ('05', '05 - Entrada com suspensão'),
    ('49', '49 - Outras entradas'),
    ('50', '50 - Saída tributada'),
    ('51', '51 - Saída tributada com alíquota zero'),
    ('52', '52 - Saída isenta'),
    ('53', '53 - Saída não-tributada'),
    ('54', '54 - Saída imune'),
    ('55', '55 - Saída com suspensão'),
    ('99', '99 - Outras saídas'),
]

TIPO_CALCULO_IPI_CHOICES = [
    ('1', 'Percentual (Alíquota %)'),
    ('2', 'Valor por Unidade Tributável (R$)'),
]

class TributoIPI(models.Model):
    """
    Modelo para armazenar as configurações de IPI,
    geralmente associado a um GrupoFiscal.
    """
    grupo_fiscal = models.OneToOneField(
        'fiscal.GrupoFiscal',
        verbose_name=_('Grupo Fiscal'),
        on_delete=models.CASCADE,
        related_name='config_ipi' # ou apenas 'ipi'
    )

    # Campos que o IPIForm espera:
    cst = models.CharField(
        _('CST IPI'),
        max_length=2,
        choices=CST_IPI_CHOICES,
        null=True, blank=True
    )
    cl_enq = models.CharField(
        _('Classe de Enquadramento do IPI para Cigarros e Bebidas'),
        max_length=5, # Conforme especificação da NFe (ex: "999")
        null=True, blank=True,
        help_text=_("Opcional. Usado para cigarros e bebidas.")
    )
    c_enq = models.CharField(
        _('Código de Enquadramento Legal do IPI'),
        max_length=3, # Geralmente "999" para não-enquadrado ou códigos específicos
        default='999',
        help_text=_("Padrão '999' para não-enquadrado.")
    )
    cnpj_prod = models.CharField(
        _('CNPJ do Produtor da Mercadoria'),
        max_length=14, # Apenas números
        null=True, blank=True,
        help_text=_("CNPJ do produtor, se diferente do emitente (para IPI). Apenas números.")
    )
    
    # Para controlar o tipo de cálculo do IPI
    tipo_calculo_ipi = models.CharField(
        _('Tipo de Cálculo do IPI'),
        max_length=1,
        choices=TIPO_CALCULO_IPI_CHOICES,
        default='1', # Padrão para percentual
        help_text=_("Define se o IPI é calculado por alíquota percentual ou valor fixo por unidade.")
    )
    p_ipi = models.DecimalField( # Alíquota percentual
        _('Alíquota do IPI (%)'),
        max_digits=7, decimal_places=4, # Ex: 5.0000%
        null=True, blank=True, # Nulo se o cálculo for por valor fixo
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    valor_unidade_tributavel_ipi = models.DecimalField( # Valor fixo por unidade (vUnid do IPI)
        _('Valor do IPI por Unidade Tributável (R$)'), # Corresponde ao 'valor_fixo' do form
        max_digits=15, decimal_places=4, # Ex: 1.2345 R$ por unidade
        null=True, blank=True, # Nulo se o cálculo for por percentual
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Flags booleanas
    ipi_incluido_preco = models.BooleanField(
        _('Valor do IPI compõe o valor total da NF-e?'),
        default=True # Geralmente o IPI soma no total da nota
    )
    incluir_bc_icms = models.BooleanField(
        _('Incluir valor do IPI na Base de Cálculo do ICMS?'),
        default=False
    )
    incluir_bc_icmsst = models.BooleanField(
        _('Incluir valor do IPI na Base de Cálculo do ICMS-ST?'),
        default=False
    )

    # Campos de valor (geralmente calculados no item da nota, mas podem ter defaults aqui)
    # Se estes forem apenas para configuração e os valores reais são por item, podem ser omitidos
    # ou mantidos como 'editable=False' se forem apenas para referência/cálculo inicial.
    valor_bc = models.DecimalField(_('Valor Base de Cálculo IPI'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_ipi = models.DecimalField(_('Valor IPI'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)
    valor_ipi_devolvido = models.DecimalField(_('Valor IPI Devolvido'), max_digits=15, decimal_places=2, default=Decimal('0.00'), editable=False)


    class Meta:
        verbose_name = _("Configuração de IPI")
        verbose_name_plural = _("Configurações de IPI")

    def __str__(self):
        return f"IPI para {self.grupo_fiscal.descricao} - CST: {self.cst or 'N/A'}"

    # O método to_edoc() para este modelo precisará ser refatorado para nfelib,
    # construindo o objeto Tipi e seus grupos internos (IPITrib, IPINT).
    def to_edoc(self):
        # Importar aqui para evitar import circular no nível do módulo, se necessário
        from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import Tipi, IpitribCst, IpintCst

        ipi_nfelib = Tipi()
        if self.cl_enq: # Classe de enquadramento (opcional)
            ipi_nfelib.clEnq = self.cl_enq
        if self.cnpj_prod: # CNPJ do produtor (opcional)
            ipi_nfelib.CNPJProd = self.cnpj_prod
        if self.c_enq: # Código de enquadramento (obrigatório no XSD)
            ipi_nfelib.cEnq = self.c_enq
        else:
            ipi_nfelib.cEnq = "999" # Padrão se não informado

        cst_ipi = self.cst
        if cst_ipi in ['00', '49', '50', '99']: # CSTs para IPITrib (Saída Tributada ou Entrada com Recuperação)
            ipitrib = Tipi.Ipitrib()
            ipitrib.CST = IpitribCst(cst_ipi)
            
            # A NFe espera vBC e pIPI OU qUnid e vUnid para IPITrib
            if self.tipo_calculo_ipi == '1' and self.p_ipi is not None: # Percentual
                # vBC e vIPI seriam calculados no item da nota e passados para cá ou para o objeto do item
                # Aqui estamos definindo a configuração, não o valor calculado da nota.
                # ipitrib.vBC = f"{self.valor_bc_base_para_calculo_do_item:.2f}" # BC do IPI do item
                ipitrib.pIPI = f"{self.p_ipi:.4f}"
                # ipitrib.vIPI = f"{self.valor_ipi_calculado_do_item:.2f}" # Valor do IPI do item
            elif self.tipo_calculo_ipi == '2' and self.valor_unidade_tributavel_ipi is not None: # Valor por unidade
                # qUnid seria a quantidade do item na unidade tributável
                # ipitrib.qUnid = f"{quantidade_do_item_na_unidade_tributavel:.4f}"
                ipitrib.vUnid = f"{self.valor_unidade_tributavel_ipi:.4f}"
                # ipitrib.vIPI = f"{self.valor_ipi_calculado_do_item:.2f}"
            
            # vIPI é obrigatório em IPITrib, mas seu cálculo depende da BC/qUnid do item.
            # Este modelo armazena a configuração. O valor final do IPI é calculado por item.
            # Para o to_edoc do item, você usaria estas alíquotas para calcular vIPI.
            # Se este to_edoc for chamado no contexto de um item específico, você teria acesso aos valores.
            # Por ora, vamos omitir vIPI aqui, pois ele é calculado.
            # Se a validação XSD exigir, pode ser necessário um valor placeholder ou cálculo.

            ipi_nfelib.IPITrib = ipitrib
        elif cst_ipi in ['01', '02', '03', '04', '05', '51', '52', '53', '54', '55']: # CSTs para IPINT (Não Tributado)
            ipint = Tipi.Ipint()
            ipint.CST = IpintCst(cst_ipi)
            ipi_nfelib.IPINT = ipint
        # else: Tratar erro ou CST não esperado / não preencher IPI

        return ipi_nfelib
