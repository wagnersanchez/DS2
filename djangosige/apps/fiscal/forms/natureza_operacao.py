# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

# Importa o modelo NaturezaOperacao.
# Certifique-se de que o caminho do import está correto conforme a estrutura do seu projeto.
# Se o __init__.py em fiscal/models/ estiver configurado para exportar NaturezaOperacao,
# from djangosige.apps.fiscal.models import NaturezaOperacao também funcionaria.
from djangosige.apps.fiscal.models.natureza_operacao import NaturezaOperacao 


class NaturezaOperacaoForm(forms.ModelForm):
    """
    Formulário para criar e editar instâncias de NaturezaOperacao.
    """

    class Meta:
        model = NaturezaOperacao
        # Define os campos do modelo que serão incluídos no formulário.
        # Estes campos devem existir no modelo NaturezaOperacao.
        fields = (
            'codigo', 
            'descricao', 
            'tipo_operacao', # Campo corrigido de 'tp_operacao'
            'regime_especial',
            'incentivo_fiscal',
            'ativo',
        )
        # Define widgets customizados para cada campo, se necessário.
        widgets = {
            'codigo': forms.TextInput(
                attrs={
                    'class': 'form-control', 
                    'maxlength': '10',
                    'placeholder': 'Ex: 5102',
                }
            ),
            'descricao': forms.TextInput(
                attrs={
                    'class': 'form-control', 
                    'maxlength': '100',
                    'placeholder': 'Ex: Venda de mercadoria adquirida',
                }
            ),
            'tipo_operacao': forms.Select( # Usa o TIPO_OPERACAO_CHOICES do modelo
                attrs={
                    'class': 'form-control',
                }
            ),
            'regime_especial': forms.CheckboxInput(
                attrs={
                    # Adicione classes CSS de frontend se estiver usando (ex: Bootstrap)
                    # 'class': 'form-check-input', 
                }
            ),
            'incentivo_fiscal': forms.CheckboxInput(
                attrs={
                    # 'class': 'form-check-input',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    # 'class': 'form-check-input',
                }
            ),
        }
        # Define labels customizados para os campos do formulário.
        labels = {
            'codigo': _('Código da Natureza'),
            'descricao': _('Descrição da Natureza da Operação'),
            'tipo_operacao': _('Tipo de Operação (E/S)'),
            'regime_especial': _('Possui Regime Especial de Tributação?'),
            'incentivo_fiscal': _('Operação com Incentivo Fiscal?'),
            'ativo': _('Ativo? (Disponível para uso)'),
        }
        # Define textos de ajuda para os campos, se necessário.
        help_texts = {
            'codigo': _('Código numérico ou alfanumérico que identifica a natureza da operação. Ex: 5102, 1102.'),
            'descricao': _('Descrição detalhada da natureza da operação. Ex: Venda de mercadoria adquirida ou recebida de terceiros.'),
            'tipo_operacao': _('Define se a operação é de Entrada de mercadorias/serviços no estoque/empresa ou Saída.'),
            'regime_especial': _('Marque se esta natureza de operação está vinculada a algum regime especial de tributação.'),
            'incentivo_fiscal': _('Marque se esta operação se beneficia de algum incentivo fiscal.'),
            'ativo': _('Desmarque para inativar esta natureza de operação, impedindo seu uso em novas notas fiscais.'),
        }

    def __init__(self, *args, **kwargs):
        super(NaturezaOperacaoForm, self).__init__(*args, **kwargs)
        # Você pode adicionar personalizações ao formulário aqui, se necessário.
        # Por exemplo, definir um campo como obrigatório ou alterar seu widget dinamicamente.
        # self.fields['codigo'].required = True
