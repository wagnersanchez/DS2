# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

# Importar os nomes corretos dos modelos como definidos em models/tributos.py
from djangosige.apps.fiscal.models import GrupoFiscal, TributoICMS, TributoICMSSN, TributoICMSUFDest, TributoIPI, TributoPIS, TributoCOFINS

class GrupoFiscalForm(forms.ModelForm):
    class Meta:
        model = GrupoFiscal
        fields = ('descricao', 'regime_trib',)
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'title': 'Insira uma breve descrição do grupo fiscal, EX: ICMS (Simples Nacional) + IPI'}),
            'regime_trib': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'descricao': _('Descrição do Grupo Fiscal'),
            'regime_trib': _('Regime Tributário Predominante'),
        }
        help_texts = { 
            'descricao': _('Nome descritivo para o grupo fiscal. Ex: Produtos Tributados, Serviços Isentos, etc.'),
            'regime_trib': _('Selecione o regime tributário principal associado a este grupo fiscal.')
        }

class ICMSForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        grupo_fiscal_instance = kwargs.pop('grupo_fiscal', None)
        instance_to_edit = None
        if grupo_fiscal_instance:
            try:
                instance_to_edit = TributoICMS.objects.get(grupo_fiscal=grupo_fiscal_instance)
            except TributoICMS.DoesNotExist: pass
            except TributoICMS.MultipleObjectsReturned:
                instance_to_edit = TributoICMS.objects.filter(grupo_fiscal=grupo_fiscal_instance).first()
        if 'instance' not in kwargs and instance_to_edit: kwargs['instance'] = instance_to_edit
        super(ICMSForm, self).__init__(*args, **kwargs)
        if 'cst' in self.fields: self.fields['cst'].required = False 
        for field_name in ['p_icms', 'p_red_bc', 'p_mvast', 'p_red_bcst', 'p_icmsst', 'p_dif', 'p_bc_op']:
            if field_name in self.fields: self.fields[field_name].localize = True

    class Meta:
        model = TributoICMS 
        fields = ('cst', 'mod_bc', 'p_icms', 'p_red_bc', 'mod_bcst', 'p_mvast', 'p_red_bcst', 'p_icmsst', 'mot_des_icms',
                  'p_dif', 'p_bc_op', 'ufst', 'icms_incluido_preco', 'icmsst_incluido_preco', )
        widgets = {
            'cst': forms.Select(attrs={'class': 'form-control'}),
            'mod_bc': forms.Select(attrs={'class': 'form-control'}),
            'p_icms': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_red_bc': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'mod_bcst': forms.Select(attrs={'class': 'form-control'}),
            'p_mvast': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_red_bcst': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_icmsst': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'mot_des_icms': forms.Select(attrs={'class': 'form-control'}),
            'p_dif': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_bc_op': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'ufst': forms.Select(attrs={'class': 'form-control'}), 
            'icms_incluido_preco': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'icmsst_incluido_preco': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'cst': _('CST/CSOSN ICMS'), 
            'mod_bc': _('Modalidade de determinação da BC do ICMS'),
            'p_icms': _('Alíquota ICMS (%)'),
            'p_red_bc': _('% da Redução de BC'),
            'mod_bcst': _('Modalidade de determinação da BC do ICMS ST'),
            'p_mvast': _('% Margem de valor Adicionado do ICMS ST'),
            'p_red_bcst': _('% da Redução de BC do ICMS ST'),
            'p_icmsst': _('Alíquota ICMS ST (%)'),
            'mot_des_icms': _('Motivo da desoneração do ICMS'),
            'p_dif': _('% do diferimento'),
            'p_bc_op': _('% da BC operação própria'),
            'ufst': _('UF para qual é devido o ICMS ST'),
            'icms_incluido_preco': _('ICMS incluso no preço do produto/serviço?'),
            'icmsst_incluido_preco': _('ICMS-ST incluso no preço do produto/serviço?'),
        }

class TributoICMSSNForm(forms.ModelForm): # Nome da classe está CORRETO
    def __init__(self, *args, **kwargs):
        grupo_fiscal_instance = kwargs.pop('grupo_fiscal', None)
        instance_to_edit = None
        if grupo_fiscal_instance:
            try:
                instance_to_edit = TributoICMSSN.objects.get(grupo_fiscal=grupo_fiscal_instance) 
            except TributoICMSSN.DoesNotExist: pass
            except TributoICMSSN.MultipleObjectsReturned:
                instance_to_edit = TributoICMSSN.objects.filter(grupo_fiscal=grupo_fiscal_instance).first()
        if 'instance' not in kwargs and instance_to_edit: kwargs['instance'] = instance_to_edit
        super(TributoICMSSNForm, self).__init__(*args, **kwargs) 
        if 'csosn' in self.fields: self.fields['csosn'].required = False
        for field_name in ['p_cred_sn', 'p_icms', 'p_red_bc', 'p_mvast', 'p_red_bcst', 'p_icmsst']:
            if field_name in self.fields: self.fields[field_name].localize = True

    class Meta:
        model = TributoICMSSN # Modelo CORRETO
        fields = ('csosn', 'p_cred_sn', 'mod_bc', 'p_icms', 'p_red_bc', 
                  'mod_bcst', 'p_mvast', 'p_red_bcst', 'p_icmsst',
                  'icmssn_incluido_preco', 'icmssnst_incluido_preco',)
        widgets = {
            'csosn': forms.Select(attrs={'class': 'form-control'}),
            'p_cred_sn': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'mod_bc': forms.Select(attrs={'class': 'form-control'}),
            'p_icms': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_red_bc': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'mod_bcst': forms.Select(attrs={'class': 'form-control'}),
            'p_mvast': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_red_bcst': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_icmsst': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'icmssn_incluido_preco': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'icmssnst_incluido_preco': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'csosn': _('CSOSN'),
            'p_cred_sn': _('Alíquota aplicável de cálculo do crédito (%)'),
            'mod_bc': _('Modalidade de determinação da BC do ICMS (SN)'),
            'p_icms': _('Alíquota ICMS (SN) (%)'),
            'p_red_bc': _('% da Redução de BC (SN)'),
            'mod_bcst': _('Modalidade de determinação da BC do ICMS ST (SN)'),
            'p_mvast': _('% Margem de valor Adicionado do ICMS ST (SN)'),
            'p_red_bcst': _('% da Redução de BC do ICMS ST (SN)'),
            'p_icmsst': _('Alíquota ICMS ST (SN) (%)'),
            'icmssn_incluido_preco': _('ICMS SN incluso no preço?'),
            'icmssnst_incluido_preco': _('ICMS-ST SN incluso no preço?'),
        }

class TributoICMSUFDestForm(forms.ModelForm): # Nome da classe CORRETO
    def __init__(self, *args, **kwargs):
        grupo_fiscal_instance = kwargs.pop('grupo_fiscal', None)
        instance_to_edit = None
        if grupo_fiscal_instance:
            try:
                instance_to_edit = TributoICMSUFDest.objects.get(grupo_fiscal=grupo_fiscal_instance)
            except TributoICMSUFDest.DoesNotExist: pass
            except TributoICMSUFDest.MultipleObjectsReturned:
                instance_to_edit = TributoICMSUFDest.objects.filter(grupo_fiscal=grupo_fiscal_instance).first()
        if 'instance' not in kwargs and instance_to_edit: kwargs['instance'] = instance_to_edit
        super(TributoICMSUFDestForm, self).__init__(*args, **kwargs) 
        for field_name in ['p_fcp_dest', 'p_icms_dest', 'p_icms_inter', 'p_icms_inter_part']:
            if field_name in self.fields: self.fields[field_name].localize = True

    class Meta:
        model = TributoICMSUFDest # Modelo CORRETO
        fields = ('p_fcp_dest', 'p_icms_dest', 'p_icms_inter', 'p_icms_inter_part', )
        widgets = {
            'p_fcp_dest': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_icms_dest': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'p_icms_inter': forms.Select(attrs={'class': 'form-control'}), 
            'p_icms_inter_part': forms.Select(attrs={'class': 'form-control'}), 
        }
        labels = {
            'p_fcp_dest': _('% do ICMS relativo ao FCP de destino'),
            'p_icms_dest': _('Alíquota interna da UF de destino (%)'),
            'p_icms_inter': _('Alíquota interestadual das UF envolvidas'),
            'p_icms_inter_part': _('% provisório de partilha do ICMS Interestadual'),
        }

class IPIForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        grupo_fiscal_instance = kwargs.pop('grupo_fiscal', None)
        instance_to_edit = None
        if grupo_fiscal_instance:
            try:
                instance_to_edit = TributoIPI.objects.get(grupo_fiscal=grupo_fiscal_instance) 
            except TributoIPI.DoesNotExist: pass
            except TributoIPI.MultipleObjectsReturned:
                instance_to_edit = TributoIPI.objects.filter(grupo_fiscal=grupo_fiscal_instance).first()
        if 'instance' not in kwargs and instance_to_edit: kwargs['instance'] = instance_to_edit
        super(IPIForm, self).__init__(*args, **kwargs)
        for field_name in ['p_ipi', 'valor_fixo_ipi']: 
            if field_name in self.fields: self.fields[field_name].localize = True

    class Meta:
        model = TributoIPI 
        fields = ('cst', 'cl_enq', 'c_enq', 'cnpj_prod', 'tipo_ipi', 'p_ipi',
                  'valor_fixo_ipi', 'ipi_incluido_preco', 'incluir_bc_icms', 'incluir_bc_icmsst',)
        widgets = {
            'cst': forms.Select(attrs={'class': 'form-control'}),
            'cl_enq': forms.TextInput(attrs={'class': 'form-control'}),
            'c_enq': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj_prod': forms.TextInput(attrs={'class': 'form-control'}),
            'p_ipi': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'tipo_ipi': forms.Select(attrs={'class': 'form-control'}),
            'valor_fixo_ipi': forms.TextInput(attrs={'class': 'form-control decimal-mask'}), 
            'ipi_incluido_preco': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'incluir_bc_icms': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'incluir_bc_icmsst': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'cst': _('CST IPI'),
            'cl_enq': _('Classe de enquadramento para Cigarros e Bebidas'),
            'c_enq': _('Código de Enquadramento Legal do IPI'),
            'cnpj_prod': _('CNPJ do produtor da mercadoria'),
            'p_ipi': _('Alíquota do IPI (%)'),
            'tipo_ipi': _('Tipo de cálculo do IPI'),
            'valor_fixo_ipi': _('Valor do IPI por unidade tributável (R$)'),
            'ipi_incluido_preco': _('IPI incluso no preço?'),
            'incluir_bc_icms': _('Incluir IPI na BC do ICMS?'),
            'incluir_bc_icmsst': _('Incluir IPI na BC do ICMS-ST?'),
        }

class PISForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        grupo_fiscal_instance = kwargs.pop('grupo_fiscal', None)
        instance_to_edit = None
        if grupo_fiscal_instance:
            try:
                instance_to_edit = TributoPIS.objects.get(grupo_fiscal=grupo_fiscal_instance) 
            except TributoPIS.DoesNotExist: pass
            except TributoPIS.MultipleObjectsReturned:
                instance_to_edit = TributoPIS.objects.filter(grupo_fiscal=grupo_fiscal_instance).first()
        if 'instance' not in kwargs and instance_to_edit: kwargs['instance'] = instance_to_edit
        super(PISForm, self).__init__(*args, **kwargs)
        for field_name in ['p_pis', 'valiq_pis']:
            if field_name in self.fields: self.fields[field_name].localize = True

    class Meta:
        model = TributoPIS 
        fields = ('cst', 'p_pis', 'valiq_pis',)
        widgets = {
            'cst': forms.Select(attrs={'class': 'form-control'}),
            'p_pis': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'valiq_pis': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
        }
        labels = {
            'cst': _('CST PIS'),
            'p_pis': _('Alíquota do PIS (em %)'),
            'valiq_pis': _('Valor Alíquota do PIS por unidade (em R$)'),
        }

class COFINSForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        grupo_fiscal_instance = kwargs.pop('grupo_fiscal', None)
        instance_to_edit = None
        if grupo_fiscal_instance:
            try:
                instance_to_edit = TributoCOFINS.objects.get(grupo_fiscal=grupo_fiscal_instance) 
            except TributoCOFINS.DoesNotExist: pass
            except TributoCOFINS.MultipleObjectsReturned:
                instance_to_edit = TributoCOFINS.objects.filter(grupo_fiscal=grupo_fiscal_instance).first()
        if 'instance' not in kwargs and instance_to_edit: kwargs['instance'] = instance_to_edit
        super(COFINSForm, self).__init__(*args, **kwargs)
        for field_name in ['p_cofins', 'valiq_cofins']:
            if field_name in self.fields: self.fields[field_name].localize = True

    class Meta:
        model = TributoCOFINS 
        fields = ('cst', 'p_cofins', 'valiq_cofins',)
        widgets = {
            'cst': forms.Select(attrs={'class': 'form-control'}),
            'p_cofins': forms.TextInput(attrs={'class': 'form-control percentual-mask'}),
            'valiq_cofins': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
        }
        labels = {
            'cst': _('CST COFINS'),
            'p_cofins': _('Alíquota do COFINS (em %)'),
            'valiq_cofins': _('Valor Alíquota do COFINS por unidade (em R$)'),
        }
