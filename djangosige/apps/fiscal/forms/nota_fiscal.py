# djangosige/apps/fiscal/forms.py
# -*- coding: utf-8 -*- 

from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

# Importa o modelo NotaFiscal unificado e outros modelos necessários
from djangosige.apps.fiscal.models import NotaFiscal # Modelo unificado
from djangosige.apps.fiscal.models import NaturezaOperacao # Necessário para NotaFiscalForm
from djangosige.apps.cadastro.models import Empresa, Cliente, MinhaEmpresa # Necessário para NotaFiscalForm

# Definição local das constantes, já que a importação original falhou.
TP_AMB_ESCOLHAS = (
    ('1', _('Produção')),
    ('2', _('Homologação')),
)

MOD_NFE_ESCOLHAS = (
    ('55', _('NF-e')),
    ('65', _('NFC-e')),
)

# As constantes MD_... e TP_MANIFESTO_OPCOES abaixo não são mais necessárias
# se o ManifestacaoDestinatarioForm definir TIPOS_MANIFESTACAO internamente.
# No entanto, como estavam no seu arquivo, vou mantê-las comentadas para referência,
# mas o ManifestacaoDestinatarioForm atualizado abaixo usa sua própria definição.
# try:
#     from pysignfe.nfe.manifestacao_destinatario import MD_CONFIRMACAO_OPERACAO, MD_DESCONHECIMENTO_OPERACAO, MD_OPERACAO_NAO_REALIZADA, MD_CIENCIA_OPERACAO
# except ImportError:
#     MD_CONFIRMACAO_OPERACAO = u'210200'
#     MD_DESCONHECIMENTO_OPERACAO = u'210220'
#     MD_OPERACAO_NAO_REALIZADA = u'210240'
#     MD_CIENCIA_OPERACAO = u'210210'

# TP_MANIFESTO_OPCOES = (
#     (MD_CONFIRMACAO_OPERACAO, u'Confirmação da Operação'),
#     (MD_DESCONHECIMENTO_OPERACAO, u'Desconhecimento da Operação'),
#     (MD_OPERACAO_NAO_REALIZADA, u'Operação Não Realizada'),
#     (MD_CIENCIA_OPERACAO, u'Ciência da Emissão (ou Ciência da Operação)'),
# )


class NotaFiscalFormBase(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'data_emissao' in self.fields:
            self.fields['data_emissao'].input_formats = ('%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M')
            self.fields['data_emissao'].widget.format = '%d/%m/%Y %H:%M'
            self.fields['data_emissao'].localize = True

        if 'emitente' in self.fields and self.instance and self.instance.pk:
            self.fields['emitente'].disabled = True

    class Meta:
        model = NotaFiscal
        fields = (
            'natureza_operacao', 'destinatario', 'serie', 'numero', 
            'informacoes_adicionais_fisco', 'informacoes_complementares',
            'valor_frete', 'valor_seguro', 'valor_desconto', 'valor_outros',
        )
        widgets = {
            'natureza_operacao': forms.Select(attrs={'class': 'form-control'}),
            'destinatario': forms.Select(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'informacoes_adicionais_fisco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'informacoes_complementares': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor_frete': forms.NumberInput(attrs={'class': 'form-control decimal-mask'}),
            'valor_seguro': forms.NumberInput(attrs={'class': 'form-control decimal-mask'}),
            'valor_desconto': forms.NumberInput(attrs={'class': 'form-control decimal-mask'}),
            'valor_outros': forms.NumberInput(attrs={'class': 'form-control decimal-mask'}),
        }
        labels = {
            'natureza_operacao': _('Natureza da Operação'),
            'destinatario': _('Destinatário (Cliente/Fornecedor)'),
            'serie': _('Série'),
            'numero': _('Número da Nota'),
            'informacoes_adicionais_fisco': _('Informações Adicionais de Interesse do Fisco'),
            'informacoes_complementares': _('Informações Complementares de interesse do Contribuinte'),
        }

class NotaFiscalOperacaoForm(NotaFiscalFormBase):
    pass

class EmissaoNotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal 
        fields = ('data_emissao',) 
        widgets = {
            'data_emissao': forms.DateTimeInput(
                attrs={'class': 'form-control datetimepicker', 'required': True}, 
                format='%d/%m/%Y %H:%M:%S'
            ),
        }
        labels = {
            'data_emissao': _('Confirmar Data e Hora de Emissão'),
        }

class CancelamentoNotaFiscalForm(forms.Form): 
    justificativa_cancelamento = forms.CharField(
        label=_('Justificativa do Cancelamento (mínimo 15 caracteres)'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        min_length=15,
        required=True
    )

class ConsultarCadastroForm(forms.Form):
    empresa_para_certificado = forms.ModelChoiceField( 
        queryset=MinhaEmpresa.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        label='Empresa (para usar o certificado)', 
        required=True,
        empty_label="Selecione a empresa para o certificado"
    )
    uf_consulta = forms.CharField(
        label=_('UF do Contribuinte a Consultar (Sigla)'),
        max_length=2,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: SP'})
    )
    documento_consulta = forms.CharField(
        label=_('CNPJ, CPF ou IE do Contribuinte'),
        max_length=14, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números'})
    )

class InutilizarNotasForm(forms.Form):
    ambiente = forms.ChoiceField(
        choices=TP_AMB_ESCOLHAS, 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        label='Ambiente', 
        initial='2', 
        required=True
    )
    empresa_para_certificado = forms.ModelChoiceField( 
        queryset=MinhaEmpresa.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        label='Empresa Emitente (para usar o certificado)', 
        required=True,
        empty_label="Selecione a empresa emitente"
    )
    modelo = forms.ChoiceField(
        choices=MOD_NFE_ESCOLHAS, 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        label='Modelo Documento', 
        initial='55',
        required=True
    )
    serie = forms.CharField(
        max_length=3, 
        widget=forms.TextInput(attrs={'class': 'form-control'}), 
        label='Série', 
        required=True
    )
    numero_inicial = forms.IntegerField( 
        widget=forms.NumberInput(attrs={'class': 'form-control'}), 
        label='Número inicial da faixa', 
        required=True
    )
    numero_final = forms.IntegerField( 
        widget=forms.NumberInput(attrs={'class': 'form-control'}), 
        label='Número final da faixa', 
        required=True
    )
    justificativa = forms.CharField(
        max_length=255, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows':3}), 
        label='Justificativa (mínimo 15 caracteres)', 
        min_length=15,
        required=True
    )

class ConsultarNotaForm(forms.Form):
    ambiente = forms.ChoiceField(
        choices=TP_AMB_ESCOLHAS, 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        label='Ambiente da NF-e', 
        initial='2', 
        required=True
    )
    chave_consulta = forms.CharField(
        max_length=44, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '44 dígitos da chave de acesso'}), 
        label='Chave de Acesso da NF-e', 
        required=True
    )
    empresa_para_certificado = forms.ModelChoiceField(
        queryset=MinhaEmpresa.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Empresa (para certificado da consulta)',
        help_text="Empresa cujo certificado será usado para a consulta.",
        required=True,
        empty_label="Selecione a empresa para o certificado"
    )

class BaixarNotaForm(forms.Form): 
    ambiente = forms.ChoiceField(
        choices=TP_AMB_ESCOLHAS, 
        widget=forms.Select(attrs={'class': 'form-control'}), 
        label='Ambiente', 
        initial='2', 
        required=True
    )
    chave_download = forms.CharField(
        max_length=44, 
        widget=forms.TextInput(attrs={'class': 'form-control'}), 
        label='Chave de Acesso da NF-e para Download', 
        required=True
    )
    empresa_manifestante = forms.ModelChoiceField( 
        queryset=MinhaEmpresa.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Empresa/CNPJ Manifestante (para certificado)',
        required=True,
        empty_label="Selecione a empresa manifestante"
    )

class ManifestacaoDestinatarioForm(forms.Form):
    TIPOS_MANIFESTACAO = [
        ('210200', 'Confirmação da Operação'),
        ('210210', 'Ciência da Emissão'),
        ('210220', 'Desconhecimento da Operação'),
        ('210240', 'Operação não Realizada'),
    ]
    
    chave_nfe = forms.CharField(
        label='Chave de Acesso da NF-e', 
        max_length=44,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite os 44 dígitos da chave de acesso'})
    )
    tipo_manifestacao = forms.ChoiceField(
        label='Tipo de Manifestação', 
        choices=TIPOS_MANIFESTACAO,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    justificativa = forms.CharField(
        label='Justificativa', 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Obrigatória para "Desconhecimento" ou "Operação não Realizada" (mínimo 15 caracteres)'}),
        required=False 
    )
    empresa_manifestante = forms.ModelChoiceField(
        queryset=MinhaEmpresa.objects.all(), 
        label="Empresa (Destinatário da NF-e)",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Selecione a empresa que está manifestando",
        help_text="A empresa selecionada aqui é o destinatário da NF-e que está realizando a manifestação."
    )

    def clean(self): # Esta é a definição correta do clean
        cleaned_data = super().clean()
        tipo_manifestacao = cleaned_data.get("tipo_manifestacao")
        justificativa = cleaned_data.get("justificativa", "")

        # Os códigos de evento para Desconhecimento e Operação Não Realizada são strings
        if tipo_manifestacao in ['210220', '210240']: 
            if not justificativa or len(justificativa.strip()) < 15:
                self.add_error('justificativa', 'A justificativa é obrigatória e deve ter no mínimo 15 caracteres para este tipo de manifestação.')
        return cleaned_data
    
    # A SEGUNDA DEFINIÇÃO DE clean FOI REMOVIDA DAQUI, POIS ESTAVA DUPLICADA E USAVA CONSTANTES INDEFINIDAS

# --- Formulários comentados pois os modelos AutXML e ConfiguracaoNotaFiscal não foram definidos/refatorados ---
# class AutXMLForm(forms.ModelForm):
#     class Meta:
#         model = AutXML 
#         fields = ('cpf_cnpj',)
#         labels = {
#             'cpf_cnpj': _('CPF/CNPJ (Apenas digitos)'),
#         }
#         widgets = {
#             'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control'}),
#         }

# AutXMLFormSet = inlineformset_factory(
#     NotaFiscal, 
#     AutXML, 
#     form=AutXMLForm, 
#     extra=1, 
#     can_delete=True
# )

# class ConfiguracaoNotaFiscalForm(forms.ModelForm):
#     class Meta:
#         model = ConfiguracaoNotaFiscal 
#         fields = ('serie_atual', 'ambiente', 'imp_danfe', 'arquivo_certificado_a1',
#                   'senha_certificado', 'inserir_logo_danfe', 'orientacao_logo_danfe', 'csc', 'cidtoken',)
# # ) # Parêntese final comentado
