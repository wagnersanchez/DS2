# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory

# Importar modelos de compras
from djangosige.apps.compras.models import OrcamentoCompra, PedidoCompra, ItensCompra, Compra
# Importar CondicaoPagamento de onde ele estiver definido (provavelmente vendas?)
# Se não existir, precisará ser criado ou a referência removida/ajustada
try:
    from djangosige.apps.vendas.models import CondicaoPagamento
except ImportError:
    # Se CondicaoPagamento for específico de compras, importe de lá.
    # Se não existir em nenhum lugar, precisará definir ou remover o campo do form.
    CondicaoPagamento = None # Definir como None se não encontrado, mas idealmente importe correto
    print("AVISO: Modelo CondicaoPagamento não encontrado para importação em compras/forms/compras.py")


class CompraForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(CompraForm, self).__init__(*args, **kwargs)
        # Remover inicialização de status aqui se for específico de Orcamento/Pedido
        # self.fields['status'].initial = '0' # Status pode variar entre Orcamento e Pedido

        # Configurar campos decimais restantes
        self.fields['valor_total'].localize = True
        self.fields['valor_total'].initial = '0.00'
        self.fields['desconto'].localize = True
        self.fields['desconto'].initial = '0.0000' # Manter precisão do modelo
        self.fields['despesas'].localize = True
        self.fields['despesas'].initial = '0.00'
        self.fields['seguro'].localize = True
        self.fields['seguro'].initial = '0.00'
        self.fields['frete'].localize = True
        self.fields['frete'].initial = '0.00'

        # Linhas para total_ipi e total_icms REMOVIDAS
        # self.fields['total_ipi'].localize = True
        # self.fields['total_ipi'].initial = '0.00'
        # self.fields['total_icms'].localize = True
        # self.fields['total_icms'].initial = '0.00'

        # Limitar queryset de CondicaoPagamento se importado corretamente
        if CondicaoPagamento:
             self.fields['cond_pagamento'].queryset = CondicaoPagamento.objects.all()
        elif 'cond_pagamento' in self.fields:
             # Desabilitar ou remover se o modelo não foi encontrado
             self.fields['cond_pagamento'].disabled = True


    class Meta:
        # Remover 'total_ipi', 'total_icms' da lista de fields
        fields = ('data_emissao', 'fornecedor', 'mod_frete', 'desconto', 'tipo_desconto', 'frete', 'despesas', 'local_dest',
                  'movimentar_estoque', 'seguro', 'valor_total', 'cond_pagamento', 'observacoes', )

        widgets = {
            'data_emissao': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'fornecedor': forms.Select(attrs={'class': 'form-control'}), # Considerar Select2 ou autocomplete para muitos fornecedores
            'mod_frete': forms.Select(attrs={'class': 'form-control'}),
            'local_dest': forms.Select(attrs={'class': 'form-control'}), # Considerar Select2
            'movimentar_estoque': forms.CheckboxInput(attrs={}), # Remover classe form-control desnecessária para checkbox?
            'valor_total': forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}),
            'tipo_desconto': forms.Select(attrs={'class': 'form-control'}),
            'desconto': forms.TextInput(attrs={'class': 'form-control decimal-mask-four'}),
            'frete': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'despesas': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'seguro': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            # Widgets para total_icms e total_ipi REMOVIDOS
            # 'total_icms': forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}),
            # 'total_ipi': forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}),
            'cond_pagamento': forms.Select(attrs={'class': 'form-control'}), # Considerar Select2
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), # Definir rows
        }
        labels = {
            'data_emissao': _('Data de Emissão'),
            'fornecedor': _('Fornecedor'),
            'mod_frete': _('Modalidade do frete'),
            'local_dest': _('Local de destino (Estoque)'),
            'movimentar_estoque': _('Movimentar estoque ao receber?'),
            # 'vendedor': _('Vendedor'), # Campo não existe no modelo Compra base
            'valor_total': _('Total da Compra (R$)'), # Label mais específico
            'tipo_desconto': _('Tipo de desconto'),
            'desconto': _('Desconto Geral (% ou R$)'), # Label mais específico
            'frete': _('Frete (R$)'),
            'despesas': _('Outras Despesas (R$)'), # Label mais específico
            'seguro': _('Seguro (R$)'),
            # Labels para total_ipi e total_icms REMOVIDAS
            # 'total_ipi': _('Valor total IPI (R$)'),
            # 'total_icms': _('Valor total ICMS (R$)'),
            'cond_pagamento': _('Condição de pagamento'),
            'observacoes': _('Observações'),
        }


class OrcamentoCompraForm(CompraForm):

    class Meta(CompraForm.Meta):
        model = OrcamentoCompra
        # Adiciona apenas os campos específicos de OrcamentoCompra
        fields = CompraForm.Meta.fields + ('data_vencimento', 'status',)
        # Herda widgets de CompraForm.Meta e adiciona/modifica os específicos
        widgets = CompraForm.Meta.widgets.copy() # Copia para não modificar o original
        widgets.update({
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'status': forms.Select(attrs={'class': 'form-control', 'disabled': True}), # Manter desabilitado
        })
        # Herda labels de CompraForm.Meta e adiciona/modifica os específicos
        labels = CompraForm.Meta.labels.copy()
        labels.update({
            'data_vencimento': _('Data de Vencimento'),
            'status': _('Status'),
        })


class PedidoCompraForm(CompraForm):

    class Meta(CompraForm.Meta):
        model = PedidoCompra
        # Adiciona apenas os campos específicos de PedidoCompra
        fields = CompraForm.Meta.fields + ('data_entrega', 'status', 'orcamento',)
        # Herda widgets e adiciona/modifica
        widgets = CompraForm.Meta.widgets.copy()
        widgets.update({
            'data_entrega': forms.DateInput(attrs={'class': 'form-control datepicker'}),
            'status': forms.Select(attrs={'class': 'form-control', 'disabled': True}),
            'orcamento': forms.Select(attrs={'class': 'form-control', 'disabled': True}), # Geralmente vinculado programaticamente
        })
        # Herda labels e adiciona/modifica
        labels = CompraForm.Meta.labels.copy()
        labels.update({
            'data_entrega': _('Data de Entrega Prevista'), # Label mais claro
            'status': _('Status'),
            'orcamento': _('Orçamento de Origem'), # Label mais claro
        })


class ItensCompraForm(forms.ModelForm):
    # Campos calculados apenas para exibição (não salvos diretamente no modelo ItensCompra)
    # A lógica de cálculo deve vir dos métodos do modelo
    total_sem_desconto = forms.CharField(label='Subtotal Bruto', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}))
    total_impostos = forms.CharField(label='Impostos (Item)', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}))
    total_com_impostos = forms.CharField(label='Total c/ Impostos (Item)', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}))

    # Campos removidos que não pareciam ser usados diretamente ou eram confusos
    # calculo_imposto = forms.CharField(...)
    # p_red_bc = forms.DecimalField(...)
    # tipo_ipi = forms.ChoiceField(...)
    # vfixo_ipi = forms.DecimalField(...)

    def __init__(self, *args, **kwargs):
        super(ItensCompraForm, self).__init__(*args, **kwargs)
        # Configurar campos para usar localize (formatação local) se necessário
        # A máscara nos widgets já pode cuidar disso no front-end
        number_fields = ['quantidade', 'valor_unit', 'desconto', 'subtotal', 'vicms', 'vipi', 'p_icms', 'p_ipi']
        for field_name in number_fields:
            if field_name in self.fields:
                self.fields[field_name].localize = True
                # Definir initial='0.00' pode ser feito no modelo com default=Decimal('0.00')

        # Preencher campos calculados readonly se houver instância (ao carregar form de edição)
        if self.instance and self.instance.pk:
            # Usar os métodos format_* do modelo que corrigimos
            self.initial['total_sem_desconto'] = self.instance.format_vprod() # vprod é o total sem desconto
            self.initial['total_impostos'] = self.instance.format_total_impostos()
            self.initial['total_com_impostos'] = self.instance.format_total_com_imposto()


    class Meta:
        model = ItensCompra
        # Incluir campos do modelo que devem ser editáveis no formset
        # Remover campos calculados como 'subtotal' se for sempre calculado no save do modelo
        # Remover campos de imposto que são calculados automaticamente (a menos que queira override manual)
        fields = ('produto', 'quantidade', 'valor_unit', 'tipo_desconto', 'desconto',
                  'vicms', 'vipi', 'p_icms', 'p_ipi', # Permitir edição de impostos? Avaliar.
                  # 'subtotal', # Removido, será calculado no save do modelo
                  'inf_ad_prod',
                  # 'icms_incluido_preco', # Manter se o usuário precisar configurar isso por item
                  # 'ipi_incluido_preco', # Manter se o usuário precisar configurar isso por item
                  # 'incluir_bc_icms', # Manter se o usuário precisar configurar isso por item
                  # 'auto_calcular_impostos', # Manter se o usuário precisar configurar isso por item
                 )

        widgets = {
            'produto': forms.Select(attrs={'class': 'form-control select-produto'}), # Usar Select2 ou similar para busca
            'quantidade': forms.TextInput(attrs={'class': 'form-control decimal-mask-four'}), # Permitir 4 casas?
            'valor_unit': forms.TextInput(attrs={'class': 'form-control decimal-mask-four'}), # Permitir 4 casas?
            'tipo_desconto': forms.Select(attrs={'class': 'form-control'}),
            'desconto': forms.TextInput(attrs={'class': 'form-control decimal-mask-four'}), # Permitir 4 casas?
            # Remover widget de subtotal se o campo foi removido de 'fields'
            # 'subtotal': forms.TextInput(attrs={'class': 'form-control decimal-mask', 'readonly': True}),

            # Manter widgets de impostos se eles estiverem em 'fields' e forem editáveis
            'vicms': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'vipi': forms.TextInput(attrs={'class': 'form-control decimal-mask'}),
            'p_icms': forms.TextInput(attrs={'class': 'form-control decimal-mask-four'}), # Percentual
            'p_ipi': forms.TextInput(attrs={'class': 'form-control decimal-mask-four'}), # Percentual

            # Manter widgets das opções booleanas se estiverem em 'fields'
            # 'ipi_incluido_preco': forms.CheckboxInput(attrs={}),
            # 'icms_incluido_preco': forms.CheckboxInput(attrs={}),
            # 'incluir_bc_icms': forms.CheckboxInput(attrs={}),
            # 'auto_calcular_impostos': forms.CheckboxInput(attrs={}),

            'inf_ad_prod': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'produto': _('Produto'),
            'quantidade': _('Quantidade'),
            'valor_unit': _('Vl. Unit. R$'), # Indicar moeda
            # 'subtotal': _('Subtotal R$'), # Remover se campo foi removido
            'tipo_desconto': _('Tipo Desc.'),
            'desconto': _('Desc. (% ou R$)'),
            'vicms': _('Valor ICMS R$'),
            'vipi': _('Valor IPI R$'),
            'p_icms': _('Alíq. ICMS %'),
            'p_ipi': _('Alíq. IPI %'),
            'inf_ad_prod': _('Inf. Adicional'),
        }

    # Remover validação que limpava tudo se produto fosse None,
    # pois o formset pode ter linhas extras vazias. A validação
    # de campos obrigatórios deve cuidar disso.
    # def is_valid(self):
    #     valid = super(ItensCompraForm, self).is_valid()
    #     if self.cleaned_data.get('produto', None) is None:
    #         # Verificar se é uma linha marcada para exclusão ou totalmente vazia
    #         if not self.cleaned_data.get('DELETE', False) and any(self.cleaned_data.values()):
    #              # Se não for para deletar e tiver algum dado, mas sem produto, é inválido
    #              # A validação padrão de 'produto' (se for obrigatório) deve pegar isso.
    #              pass # Deixar validação padrão agir
    #         else:
    #              # Linha vazia ou marcada para deletar, limpar erros não relacionados a ela
    #              if 'produto' in self._errors: del self._errors['produto']
    #              # Não limpar self.cleaned_data totalmente
    #              pass
    #     return valid


ItensCompraFormSet = inlineformset_factory(
    Compra, # Modelo pai
    ItensCompra, # Modelo dos itens
    form=ItensCompraForm, # Formulário customizado para os itens
    extra=1, # Quantidade de formulários extras em branco
    can_delete=True, # Permitir marcar para deletar
    # min_num=1, # Exigir pelo menos um item?
    # validate_min=True,
)

# Definição do PagamentoFormSet (mantida como estava, assumindo que Pagamento tem FK para Compra)
# Verificar se Pagamento precisa de um form customizado (PagamentoForm)
from djangosige.apps.compras.models import Pagamento # Importar Pagamento

class PagamentoForm(forms.ModelForm): # Criar um form básico se não existir
     class Meta:
         model = Pagamento
         fields = '__all__' # Ou liste os campos necessários

PagamentoFormSet = inlineformset_factory(Compra, Pagamento, form=PagamentoForm, extra=1, can_delete=True)