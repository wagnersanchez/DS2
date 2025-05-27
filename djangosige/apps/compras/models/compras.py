# -*- coding: utf-8 -*-

from django.db import models
from django.template.defaultfilters import date
from django.core.validators import MinValueValidator
from django.urls import reverse_lazy

from decimal import Decimal, InvalidOperation # Importar InvalidOperation para tratar erros

# Importar CHOICES de vendas ou redefini-los aqui se forem diferentes
try:
    # Tenta importar. É melhor redefinir se não forem idênticos.
    from djangosige.apps.vendas.models import TIPOS_DESCONTO_ESCOLHAS, MOD_FRETE_ESCOLHAS, STATUS_ORCAMENTO_ESCOLHAS
except ImportError:
    # Redefinir se a importação falhar ou se quiser desacoplar
    print("AVISO: Usando CHOICES definidos localmente em compras/models/compras.py")
    TIPOS_DESCONTO_ESCOLHAS = ( (u'0', u'Valor'), (u'1', u'Percentual'),)
    MOD_FRETE_ESCOLHAS = (
        (u'0', u'0 - Por conta do emitente (CIF)'),
        (u'1', u'1 - Por conta do destinatário/remetente (FOB)'),
        (u'2', u'2 - Por conta de terceiros'),
        (u'9', u'9 - Sem frete'),
    )
    STATUS_ORCAMENTO_ESCOLHAS = (
        (u'0', u'Aberto'),
        (u'1', u'Baixado'), # Significa que virou Pedido
        (u'2', u'Cancelado'),
    )

from djangosige.apps.estoque.models import DEFAULT_LOCAL_ID

import locale
# Configuração de locale mais robusta
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Aviso: Locale 'pt_BR' não pôde ser definido. Usando padrão do sistema.")
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            print("Erro: Não foi possível definir nenhum locale.")
            locale = None # Marcar que locale não está disponível para formatação

STATUS_PEDIDO_COMPRA_ESCOLHAS = (
    (u'0', u'Aberto'),
    (u'1', u'Confirmado'), # Mudado de Realizado para Confirmado?
    (u'2', u'Cancelado'),
    (u'3', u'Importado por XML'),
    (u'4', u'Recebido') # Indica que deu entrada no estoque
)


class ItensCompra(models.Model):
    produto = models.ForeignKey('cadastro.Produto', related_name="compra_produto",
                                on_delete=models.SET_NULL, null=True, blank=True) # Usar SET_NULL se o produto puder ser deletado mas o histórico mantido
    compra_id = models.ForeignKey(
        'compras.Compra', related_name="itens_compra", on_delete=models.CASCADE) # FK para a classe base Compra
    quantidade = models.DecimalField(max_digits=13, decimal_places=4, validators=[ # Aumentar precisão da quantidade?
                                     MinValueValidator(Decimal('0.00'))], default=Decimal('0.0000'))
    valor_unit = models.DecimalField(max_digits=13, decimal_places=4, validators=[ # Aumentar precisão unitária?
                                     MinValueValidator(Decimal('0.00'))], default=Decimal('0.0000'))
    tipo_desconto = models.CharField(
        max_length=1, choices=TIPOS_DESCONTO_ESCOLHAS, default='0')
    desconto = models.DecimalField(max_digits=15, decimal_places=4, validators=[ # Aumentar precisão do desconto?
                                   MinValueValidator(Decimal('0.00'))], default=Decimal('0.0000'))
    # Campo subtotal pode ser calculado, avaliar se precisa ser armazenado
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'), editable=False) # Tornar não editável, calculado via get_total
    inf_ad_prod = models.CharField(max_length=500, null=True, blank=True)

    # Impostos por item (simplificado, pode precisar de mais campos dependendo da NF)
    vicms = models.DecimalField(max_digits=13, decimal_places=2, default=Decimal('0.00'))
    vipi = models.DecimalField(max_digits=13, decimal_places=2, default=Decimal('0.00'))
    p_icms = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    p_ipi = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    # Opcoes (removidas pois não foram usadas nos cálculos ou formatação)
    # icms_incluido_preco = models.BooleanField(default=False)
    # ipi_incluido_preco = models.BooleanField(default=False)
    # incluir_bc_icms = models.BooleanField(default=False)
    # incluir_bc_icmsst = models.BooleanField(default=False)
    # auto_calcular_impostos = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guardar valores iniciais para verificar mudanças se necessário para recálculo
        self._original_quantidade = self.quantidade
        self._original_valor_unit = self.valor_unit
        self._original_desconto = self.desconto
        self._original_tipo_desconto = self.tipo_desconto

    # Usar property para vprod (valor bruto)
    @property
    def vprod(self):
        """Valor bruto: Quantidade * Valor Unitário. Retorna Decimal."""
        qtd = self.quantidade if self.quantidade is not None else Decimal('0')
        unit = self.valor_unit if self.valor_unit is not None else Decimal('0.00')
        try:
            return (qtd * unit).quantize(Decimal('0.01')) # Arredonda para 2 casas
        except (TypeError, InvalidOperation):
            return Decimal('0.00')

    # Função para calcular o valor do desconto (retorna Decimal)
    def get_valor_desconto(self):
        """Calcula o valor do desconto do item. Retorna Decimal."""
        try:
            desconto_field = self.desconto if self.desconto is not None else Decimal('0.00')
            subtotal_bruto = self.vprod # Usa a property vprod

            if self.tipo_desconto == '0': # Valor
                valor_desconto = desconto_field
            elif self.tipo_desconto == '1': # Percentual
                # Garante que desconto_field é usado como percentual
                valor_desconto = subtotal_bruto * (desconto_field / Decimal('100'))
            else: # Sem desconto ou tipo inválido
                valor_desconto = Decimal('0.00')

            # Arredonda para 2 casas decimais
            return valor_desconto.quantize(Decimal('0.01'))
        except (TypeError, InvalidOperation):
             return Decimal('0.00')

    # --- MÉTODO get_total ADICIONADO ---
    def get_total(self):
        """Calcula o valor total do item (Qtd * VlUnit - Desconto). Retorna Decimal."""
        try:
            subtotal_bruto = self.vprod # Property já calcula Qtd * VlUnit
            desconto_calculado = self.get_valor_desconto() # Pega o valor Decimal do desconto
            total = subtotal_bruto - desconto_calculado
            return total.quantize(Decimal('0.01'))
        except (TypeError, InvalidOperation):
            return Decimal('0.00')
    # --- FIM MÉTODO get_total ---

    # Método get_total_impostos revisado para tratar None
    def get_total_impostos(self):
        """Soma os impostos do item (ICMS, IPI). Retorna Decimal."""
        vicms_val = self.vicms if self.vicms is not None else Decimal('0.00')
        vipi_val = self.vipi if self.vipi is not None else Decimal('0.00')
        # Adicionar outros impostos de item aqui se existirem (ex: PIS/COFINS por item)
        try:
             return (vicms_val + vipi_val).quantize(Decimal('0.01'))
        except (TypeError, InvalidOperation):
             return Decimal('0.00')


    # Método get_total_com_impostos revisado para usar get_total()
    def get_total_com_impostos(self):
        """Calcula o total do item COM impostos. Retorna Decimal."""
        total_item_liquido = self.get_total() # Usa o novo método (já com desconto)
        impostos_item = self.get_total_impostos()
        try:
             return (total_item_liquido + impostos_item).quantize(Decimal('0.01'))
        except (TypeError, InvalidOperation):
             return Decimal('0.00')

    # Helper de formatação centralizado
    def _format_decimal(self, value, format_spec=u'%.2f', grouping=True):
        """Helper para formatar Decimal usando locale, tratando None."""
        if value is None: value = Decimal('0.00')
        if not isinstance(value, Decimal):
            try: value = Decimal(value)
            except (TypeError, InvalidOperation): value = Decimal('0.00')

        try:
            # Tenta usar locale, convertendo para float (pode perder precisão extrema)
            return locale.format_string(format_spec, float(value), grouping=grouping)
        except (NameError, TypeError, ValueError, locale.Error):
            # Fallback para formatação simples BRL se locale falhar
            try:
                return "R$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
            except Exception:
                return "N/A" # Último caso

    # Métodos format_* atualizados para usar _format_decimal
    def format_total_impostos(self):
        return self._format_decimal(self.get_total_impostos())

    def format_total_com_imposto(self):
        return self._format_decimal(self.get_total_com_impostos())

    def format_desconto(self):
        return self._format_decimal(self.get_valor_desconto())

    def format_quantidade(self):
        # Ajustar precisão se quantidade não for sempre 2 casas
        return self._format_decimal(self.quantidade, format_spec=u'%.2f')

    def format_valor_unit(self):
        return self._format_decimal(self.valor_unit)

    def format_total(self):
        return self._format_decimal(self.get_total())

    def format_vprod(self):
        return self._format_decimal(self.vprod)

    def format_valor_attr(self, nome_attr):
        try: return self._format_decimal(getattr(self, nome_attr))
        except (AttributeError, TypeError): return ''

    def save(self, *args, **kwargs):
        # Recalcular subtotal antes de salvar
        self.subtotal = self.get_total()
        super().save(*args, **kwargs)

    def __str__(self):
         return f"{self.quantidade} x {self.produto.descricao if self.produto else 'N/D'}"


class Compra(models.Model):
    # Fornecedor
    fornecedor = models.ForeignKey(
        'cadastro.Fornecedor', related_name="compra_fornecedor", on_delete=models.PROTECT) # Usar PROTECT para evitar deletar compra se fornecedor for excluído?
    # Transporte
    mod_frete = models.CharField(
        max_length=1, choices=MOD_FRETE_ESCOLHAS, default='9')
    # Estoque
    local_dest = models.ForeignKey(
        'estoque.LocalEstoque', related_name="compra_local_estoque", default=DEFAULT_LOCAL_ID, on_delete=models.PROTECT)
    movimentar_estoque = models.BooleanField(default=True)
    # Info
    data_emissao = models.DateField(null=True, blank=True)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00')) # Aumentar precisão total?
    tipo_desconto = models.CharField(
        max_length=1, choices=TIPOS_DESCONTO_ESCOLHAS, default='0')
    desconto = models.DecimalField(max_digits=15, decimal_places=4, default=Decimal('0.00')) # Permitir mais precisão no desconto geral?
    despesas = models.DecimalField(max_digits=13, decimal_places=2, default=Decimal('0.00'))
    frete = models.DecimalField(max_digits=13, decimal_places=2, default=Decimal('0.00'))
    seguro = models.DecimalField(max_digits=13, decimal_places=2, default=Decimal('0.00'))
    # Campos total_icms e total_ipi foram removidos, use o método get_total_impostos()
    # total_icms = models.DecimalField(...)
    # total_ipi = models.DecimalField(...)

    cond_pagamento = models.ForeignKey(
        'vendas.CondicaoPagamento', related_name="compra_pagamento", on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.CharField(max_length=1055, null=True, blank=True)

    # --- MÉTODO get_total_impostos ADICIONADO ---
    def get_total_impostos(self):
        """Soma o valor total de impostos (vicms + vipi) de todos os itens da compra."""
        total_imp = Decimal('0.00')
        # Usar prefetch_related na view pode otimizar isso para múltiplas compras
        for item in self.itens_compra.all():
            total_imp += item.get_total_impostos() # Usa o método do Item
        return total_imp.quantize(Decimal('0.01'))
    # --- FIM MÉTODO get_total_impostos ---

    # --- MÉTODO get_total_sem_imposto ADICIONADO ---
    def get_total_sem_imposto(self):
        """Soma o valor total (pós-desconto de item) de todos os itens."""
        total_itens_liquido = Decimal('0.00')
        for item in self.itens_compra.all():
             total_itens_liquido += item.get_total() # Usa o get_total() do item
        return total_itens_liquido.quantize(Decimal('0.01'))
    # --- FIM MÉTODO get_total_sem_imposto ---

    # Método para calcular o valor do desconto GERAL da compra
    def get_valor_desconto_total(self):
        """Calcula o valor do desconto GERAL aplicado sobre a soma dos itens. Retorna Decimal."""
        try:
            desconto_geral_field = self.desconto if self.desconto is not None else Decimal('0.00')
            if self.tipo_desconto == '0': # Valor
                valor_desconto = desconto_geral_field
            elif self.tipo_desconto == '1': # Percentual
                # Base para percentual: soma dos totais dos itens (get_total_sem_imposto)
                base_desconto = self.get_total_sem_imposto()
                valor_desconto = base_desconto * (desconto_geral_field / Decimal('100'))
            else:
                valor_desconto = Decimal('0.00')
            return valor_desconto.quantize(Decimal('0.01'))
        except (TypeError, InvalidOperation):
            return Decimal('0.00')

    # Calcular Total Geral (baseado nos componentes)
    def calcular_total_geral(self):
         """Calcula o valor total final da compra somando componentes."""
         total_itens = self.get_total_sem_imposto()
         desconto = self.get_valor_desconto_total()
         impostos = self.get_total_impostos() # Impostos dos itens
         fret = self.frete if self.frete is not None else Decimal('0.00')
         seg = self.seguro if self.seguro is not None else Decimal('0.00')
         desp = self.despesas if self.despesas is not None else Decimal('0.00')

         total_final = total_itens - desconto + impostos + fret + seg + desp
         return total_final.quantize(Decimal('0.01'))

    def get_total_produtos(self):
        """Soma o valor bruto (Qtd*VlUnit) de todos os itens."""
        tot = Decimal('0.00')
        for it in self.itens_compra.all():
            tot += it.vprod # Usa a property vprod do item
        return tot.quantize(Decimal('0.01'))

    def get_total_produtos_estoque(self):
        """Soma o valor bruto dos itens que controlam estoque."""
        tot = Decimal('0.00')
        for it in self.itens_compra.all():
            if it.produto and it.produto.controlar_estoque:
                tot += it.vprod
        return tot.quantize(Decimal('0.01'))

    @property
    def format_data_emissao(self):
        if self.data_emissao:
            return '%s' % date(self.data_emissao, "d/m/Y")
        return ''

    # Helper interno de formatação (igual ao de ItensCompra)
    def _format_decimal(self, value, format_spec=u'%.2f', grouping=True):
        if value is None: value = Decimal('0.00')
        if not isinstance(value, Decimal):
            try: value = Decimal(value)
            except (TypeError, InvalidOperation): value = Decimal('0.00')
        try:
            return locale.format_string(format_spec, float(value), grouping=grouping)
        except (NameError, TypeError, ValueError, locale.Error):
             try: return "R$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
             except Exception: return "N/A"

    # Métodos format_* corrigidos
    def format_total_produtos(self):
        return self._format_decimal(self.get_total_produtos())

    def format_valor_total(self):
        # Formata o valor calculado para garantir consistência
        return self._format_decimal(self.calcular_total_geral())

    def format_frete(self):
        return self._format_decimal(self.frete)

    def format_impostos(self):
        return self._format_decimal(self.get_total_impostos())

    def format_total_sem_imposto(self):
        return self._format_decimal(self.get_total_sem_imposto())

    def format_desconto(self):
        return self._format_decimal(self.get_valor_desconto_total())

    def format_seguro(self):
        return self._format_decimal(self.seguro)

    def format_despesas(self):
        return self._format_decimal(self.despesas)

    def get_forma_pagamento(self):
        if self.cond_pagamento:
            if hasattr(self.cond_pagamento, 'get_forma_display'):
                return self.cond_pagamento.get_forma_display()
            else:
                return str(self.cond_pagamento)
        return ""

    def get_local_dest_id(self):
        return self.local_dest.id if self.local_dest else None

    def get_child(self):
        if hasattr(self, 'orcamentocompra'): return self.orcamentocompra
        if hasattr(self, 'pedidocompra'): return self.pedidocompra
        try: return PedidoCompra.objects.get(pk=self.pk)
        except PedidoCompra.DoesNotExist:
            try: return OrcamentoCompra.objects.get(pk=self.pk)
            except OrcamentoCompra.DoesNotExist: return self
        except Exception: return self

    def save(self, *args, **kwargs):
        # Recalcular valor_total antes de salvar?
        # self.valor_total = self.calcular_total_geral() # Descomente se quiser que o total seja sempre recalculado
        super().save(*args, **kwargs)

    def __str__(self):
        # Usa get_child para obter o tipo correto dinamicamente
        child = self.get_child()
        tipo = 'Compra'
        status_display = ''
        if isinstance(child, OrcamentoCompra):
             tipo = 'Orçamento Compra'
             if hasattr(child, 'get_status_display'): status_display = child.get_status_display()
        elif isinstance(child, PedidoCompra):
             tipo = 'Pedido Compra'
             if hasattr(child, 'get_status_display'): status_display = child.get_status_display()

        s = f'{tipo} nº {self.pk or "(Nova)"}'
        if status_display:
             s += f' ({status_display})'
        return s


class OrcamentoCompra(Compra):
    data_vencimento = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=1, choices=STATUS_ORCAMENTO_ESCOLHAS, default='0')

    class Meta:
        verbose_name = "Orçamento de Compra"
        ordering = ('-id',) # Exemplo de ordenação padrão

    @property
    def format_data_vencimento(self):
        if self.data_vencimento:
            return '%s' % date(self.data_vencimento, "d/m/Y")
        return ''

    # tipo_compra é herdado/determinado pelo __str__ de Compra usando get_child
    # @property
    # def tipo_compra(self):
    #     return 'Orçamento'

    def edit_url(self):
        return reverse_lazy('compras:editarorcamentocompraview', kwargs={'pk': self.id})

    # __str__ é herdado de Compra


class PedidoCompra(Compra):
    orcamento = models.ForeignKey(
        'compras.OrcamentoCompra', related_name="orcamento_pedido", on_delete=models.SET_NULL, null=True, blank=True)
    data_entrega = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=1, choices=STATUS_PEDIDO_COMPRA_ESCOLHAS, default='0')

    class Meta:
        verbose_name = "Pedido de Compra"
        ordering = ('-id',) # Exemplo de ordenação padrão
        permissions = (
            ("faturar_pedidocompra", "Pode faturar Pedidos de Compra"),
        )

    @property
    def format_data_entrega(self):
        if self.data_entrega:
            return '%s' % date(self.data_entrega, "d/m/Y")
        return ''

    # tipo_compra é herdado/determinado pelo __str__ de Compra usando get_child
    # @property
    # def tipo_compra(self):
    #     return 'Pedido'

    def edit_url(self):
        return reverse_lazy('compras:editarpedidocompraview', kwargs={'pk': self.id})

    # __str__ é herdado de Compra