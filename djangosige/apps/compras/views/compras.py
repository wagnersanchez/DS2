# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404 # Adicionado get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import get_user_model # Importar para buscar User padrão

# Imports de Base e Custom Views
from djangosige.apps.base.custom_views import CustomView, CustomCreateView, CustomListView, CustomUpdateView

# Imports do App Compras
from djangosige.apps.compras.forms import OrcamentoCompraForm, PedidoCompraForm, ItensCompraFormSet, PagamentoFormSet
from djangosige.apps.compras.models import OrcamentoCompra, PedidoCompra, ItensCompra, Pagamento

# Imports de outros Apps
# Certifique-se que Empresa e outros modelos de cadastro estão importados se forem usados diretamente
from djangosige.apps.cadastro.models import MinhaEmpresa, Empresa
from djangosige.apps.estoque.models import ProdutoEstocado, EntradaEstoque, ItensMovimento
# Importar o modelo de Usuario/Perfil e renomear para clareza
from djangosige.apps.login.models import Usuario as UsuarioProfile

# Imports Python e Configs
from djangosige.configs.settings import MEDIA_ROOT
from datetime import datetime
from decimal import Decimal, InvalidOperation # Import Decimal e InvalidOperation
from io import BytesIO # Usar BytesIO
import locale # Import locale

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm, cm, inch # Importar unidades necessárias
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Configurar Locale (idealmente configurado uma vez no settings ou wsgi/asgi)
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
            locale = None


# Views de Adicionar Compra (Orçamento e Pedido)
class AdicionarCompraView(CustomCreateView):

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, id=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(AdicionarCompraView, self).get_context_data(**kwargs)
        return self.view_context(context)

    def get(self, request, form_class, *args, **kwargs):
        self.object = None
        form = self.get_form(form_class)
        form.initial['data_emissao'] = datetime.today().strftime('%d/%m/%Y')
        produtos_form = ItensCompraFormSet(prefix='produtos_form')
        pagamento_form = PagamentoFormSet(prefix='pagamento_form')
        return self.render_to_response(self.get_context_data(form=form,
                                                              produtos_form=produtos_form,
                                                              pagamento_form=pagamento_form))

    def post(self, request, form_class, *args, **kwargs):
        self.object = None
        req_post = request.POST.copy()
        for key in req_post:
            if ('desconto' in key or 'quantidade' in key or 'valor' in key or
                    'frete' in key or 'despesas' in key or 'seguro' in key or 'total' in key):
                req_post[key] = req_post[key].replace('.', '')
        request.POST = req_post
        form = self.get_form(form_class)
        produtos_form = ItensCompraFormSet(request.POST, prefix='produtos_form')
        pagamento_form = PagamentoFormSet(request.POST, prefix='pagamento_form')

        if (form.is_valid() and produtos_form.is_valid() and pagamento_form.is_valid()):
            self.object = form.save(commit=False)
            self.object.save()
            produtos_form.instance = self.object
            produtos_form.save()
            pagamento_form.instance = self.object
            pagamento_form.save()
            return self.form_valid(form)

        return self.form_invalid(form=form,
                                 produtos_form=produtos_form,
                                 pagamento_form=pagamento_form)

    def form_invalid(self, form, produtos_form, pagamento_form):
         context = self.get_context_data(form=form,
                                        produtos_form=produtos_form,
                                        pagamento_form=pagamento_form)
         return self.render_to_response(context)


class AdicionarOrcamentoCompraView(AdicionarCompraView):
    form_class = OrcamentoCompraForm
    template_name = "compras/orcamento_compra/orcamento_compra_add.html"
    success_url = reverse_lazy('compras:listaorcamentocompraview')
    success_message = "<b>Orçamento de compra %(id)s </b>adicionado com sucesso."
    permission_codename = 'add_orcamentocompra'
    def view_context(self, context):
        context['title_complete'] = 'ADICIONAR ORÇAMENTO DE COMPRA'
        context['return_url'] = reverse_lazy('compras:listaorcamentocompraview')
        return context
    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarOrcamentoCompraView, self).get(request, form_class, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarOrcamentoCompraView, self).post(request, form_class, *args, **kwargs)


class AdicionarPedidoCompraView(AdicionarCompraView):
    form_class = PedidoCompraForm
    template_name = "compras/pedido_compra/pedido_compra_add.html"
    success_url = reverse_lazy('compras:listapedidocompraview')
    success_message = "<b>Pedido de compra %(id)s </b>adicionado com sucesso."
    permission_codename = 'add_pedidocompra'
    def view_context(self, context):
        context['title_complete'] = 'ADICIONAR PEDIDO DE COMPRA'
        context['return_url'] = reverse_lazy('compras:listapedidocompraview')
        return context
    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarPedidoCompraView, self).get(request, form_class, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarPedidoCompraView, self).post(request, form_class, *args, **kwargs)


# Views de Listagem
class CompraListView(CustomListView):
    def get_context_data(self, **kwargs):
        context = super(CompraListView, self).get_context_data(**kwargs)
        return self.view_context(context)

class OrcamentoCompraListView(CompraListView):
    template_name = 'compras/orcamento_compra/orcamento_compra_list.html'
    model = OrcamentoCompra
    context_object_name = 'all_orcamentos'
    success_url = reverse_lazy('compras:listaorcamentocompraview')
    permission_codename = 'view_orcamentocompra'
    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE COMPRA'
        context['add_url'] = reverse_lazy('compras:addorcamentocompraview')
        return context

class OrcamentoCompraVencidosListView(OrcamentoCompraListView):
    success_url = reverse_lazy('compras:listaorcamentocompravencidosview')
    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE COMPRA VENCIDOS'
        context['add_url'] = reverse_lazy('compras:addorcamentocompraview')
        return context
    def get_queryset(self):
        return OrcamentoCompra.objects.filter(data_vencimento__lte=datetime.now().date(), status='0')

class OrcamentoCompraVencimentoHojeListView(OrcamentoCompraListView):
    success_url = reverse_lazy('compras:listaorcamentocomprahojeview')
    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE COMPRA COM VENCIMENTO DIA ' + datetime.now().date().strftime('%d/%m/%Y')
        context['add_url'] = reverse_lazy('compras:addorcamentocompraview')
        return context
    def get_queryset(self):
        return OrcamentoCompra.objects.filter(data_vencimento=datetime.now().date(), status='0')

class PedidoCompraListView(CompraListView):
    template_name = 'compras/pedido_compra/pedido_compra_list.html'
    model = PedidoCompra
    context_object_name = 'all_pedidos'
    success_url = reverse_lazy('compras:listapedidocompraview')
    permission_codename = 'view_pedidocompra'
    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE COMPRA'
        context['add_url'] = reverse_lazy('compras:addpedidocompraview')
        return context

class PedidoCompraAtrasadosListView(PedidoCompraListView):
    success_url = reverse_lazy('compras:listapedidocompraatrasadosview')
    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE COMPRA ATRASADOS'
        context['add_url'] = reverse_lazy('compras:addpedidocompraview')
        return context
    def get_queryset(self):
        return PedidoCompra.objects.filter(data_entrega__lte=datetime.now().date(), status='0')

class PedidoCompraEntregaHojeListView(PedidoCompraListView):
    success_url = reverse_lazy('compras:listapedidocomprahojeview')
    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE COMPRA COM ENTREGA DIA ' + datetime.now().date().strftime('%d/%m/%Y')
        context['add_url'] = reverse_lazy('compras:addpedidocompraview')
        return context
    def get_queryset(self):
        return PedidoCompra.objects.filter(data_entrega=datetime.now().date(), status='0')


# Views de Edição
class EditarCompraView(CustomUpdateView):
    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, id=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(EditarCompraView, self).get_context_data(**kwargs)
        if 'produtos_form' not in context:
            context['produtos_form'] = ItensCompraFormSet(instance=self.object, prefix='produtos_form')
            if ItensCompra.objects.filter(compra_id=self.object.pk).count():
                 context['produtos_form'].extra = 0
        if 'pagamento_form' not in context:
             context['pagamento_form'] = PagamentoFormSet(instance=self.object, prefix='pagamento_form')
             if Pagamento.objects.filter(compra_id=self.object.pk).exists(): # Ajuste da FK se necessário
                  context['pagamento_form'].extra = 0
        return self.view_context(context)

    def form_invalid(self, form, produtos_form, pagamento_form):
         context = self.get_context_data(form=form,
                                        produtos_form=produtos_form,
                                        pagamento_form=pagamento_form)
         return self.render_to_response(context)


class EditarOrcamentoCompraView(EditarCompraView):
    form_class = OrcamentoCompraForm
    model = OrcamentoCompra
    template_name = "compras/orcamento_compra/orcamento_compra_edit.html"
    success_url = reverse_lazy('compras:listaorcamentocompraview')
    success_message = "<b>Orçamento de compra %(id)s </b>editado com sucesso."
    permission_codename = 'change_orcamentocompra'

    def view_context(self, context):
        context['title_complete'] = f'EDITAR ORÇAMENTO DE COMPRA N°{self.object.pk}'
        context['return_url'] = reverse_lazy('compras:listaorcamentocompraview')
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        produtos_form = ItensCompraFormSet(instance=self.object, prefix='produtos_form')
        if ItensCompra.objects.filter(compra_id=self.object.pk).exists():
             produtos_form.extra = 0
        pagamento_form = PagamentoFormSet(instance=self.object, prefix='pagamento_form')
        if Pagamento.objects.filter(compra_id=self.object.pk).exists():
             pagamento_form.extra = 0
        context = self.get_context_data(form=form, produtos_form=produtos_form, pagamento_form=pagamento_form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        req_post = request.POST.copy()
        for key in req_post:
            if ('desconto' in key or 'quantidade' in key or 'valor' in key or
                    'frete' in key or 'despesas' in key or 'seguro' in key or 'total' in key):
                req_post[key] = req_post[key].replace('.', '')

        form = self.get_form_class()(req_post, instance=self.object)
        produtos_form = ItensCompraFormSet(req_post, prefix='produtos_form', instance=self.object)
        pagamento_form = PagamentoFormSet(req_post, prefix='pagamento_form', instance=self.object)

        if form.is_valid() and produtos_form.is_valid() and pagamento_form.is_valid():
            self.object = form.save()
            produtos_form.save()
            pagamento_form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form, produtos_form, pagamento_form)


class EditarPedidoCompraView(EditarCompraView):
    form_class = PedidoCompraForm
    model = PedidoCompra
    template_name = "compras/pedido_compra/pedido_compra_edit.html"
    success_url = reverse_lazy('compras:listapedidocompraview')
    success_message = "<b>Pedido de compra %(id)s </b>editado com sucesso."
    permission_codename = 'change_pedidocompra'

    def view_context(self, context):
        context['title_complete'] = f'EDITAR PEDIDO DE COMPRA N°{self.object.pk}'
        context['return_url'] = reverse_lazy('compras:listapedidocompraview')
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        produtos_form = ItensCompraFormSet(instance=self.object, prefix='produtos_form')
        if ItensCompra.objects.filter(compra_id=self.object.pk).exists():
             produtos_form.extra = 0
        pagamento_form = PagamentoFormSet(instance=self.object, prefix='pagamento_form')
        if Pagamento.objects.filter(compra_id=self.object.pk).exists():
             pagamento_form.extra = 0
        context = self.get_context_data(form=form, produtos_form=produtos_form, pagamento_form=pagamento_form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        req_post = request.POST.copy()
        for key in req_post:
            if ('desconto' in key or 'quantidade' in key or 'valor' in key or
                    'frete' in key or 'despesas' in key or 'seguro' in key or 'total' in key):
                req_post[key] = req_post[key].replace('.', '')

        form = self.get_form_class()(req_post, instance=self.object)
        produtos_form = ItensCompraFormSet(req_post, prefix='produtos_form', instance=self.object)
        pagamento_form = PagamentoFormSet(req_post, prefix='pagamento_form', instance=self.object)

        if form.is_valid() and produtos_form.is_valid() and pagamento_form.is_valid():
            self.object = form.save()
            produtos_form.save()
            pagamento_form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form, produtos_form, pagamento_form)


# Views de Ações (Gerar Pedido, Cancelar, Copiar, Receber)
class GerarPedidoCompraView(CustomView):
    permission_codename = ['add_pedidocompra', 'change_pedidocompra', ]
    def get(self, request, *args, **kwargs):
        orcamento_id = kwargs.get('pk', None)
        orcamento = get_object_or_404(OrcamentoCompra, id=orcamento_id)
        if orcamento.status != '0':
             messages.warning(request, f"Orçamento {orcamento.pk} não está mais Aberto e não pode ser convertido em pedido.")
             return redirect(reverse_lazy('compras:listaorcamentocompraview'))
        itens_compra = list(orcamento.itens_compra.all())
        pagamentos = list(orcamento.parcela_pagamento.all())
        novo_pedido = PedidoCompra()
        campos_a_copiar = [f.name for f in Compra._meta.fields if f.name not in ['id', 'pk']]
        for field_name in campos_a_copiar:
             if hasattr(orcamento, field_name):
                 setattr(novo_pedido, field_name, getattr(orcamento, field_name))
        novo_pedido.status = '0'
        novo_pedido.orcamento = orcamento
        novo_pedido.data_emissao = datetime.now().date()
        novo_pedido.save()
        for item_orc in itens_compra:
            item_orc.pk = None
            item_orc.id = None
            item_orc.compra_id = novo_pedido
            item_orc.save()
        for pag_orc in pagamentos:
             pag_orc.pk = None
             pag_orc.id = None
             pag_orc.compra_id = novo_pedido # (VERIFICAR FK EM PAGAMENTO)
             pag_orc.save()
        orcamento.status = '1'
        orcamento.save(update_fields=['status'])
        messages.success(request, f"Pedido de compra {novo_pedido.pk} gerado a partir do orçamento {orcamento.pk}.")
        return redirect(reverse_lazy('compras:editarpedidocompraview', kwargs={'pk': novo_pedido.id}))

class CancelarOrcamentoCompraView(CustomView):
    permission_codename = 'change_orcamentocompra'
    def get(self, request, *args, **kwargs):
        compra_id = kwargs.get('pk', None)
        instance = get_object_or_404(OrcamentoCompra, id=compra_id)
        instance.status = '2'
        instance.save(update_fields=['status'])
        messages.success(request, f"Orçamento de compra {instance.pk} cancelado.")
        return redirect(reverse_lazy('compras:listaorcamentocompraview'))

class CancelarPedidoCompraView(CustomView):
    permission_codename = 'change_pedidocompra'
    def get(self, request, *args, **kwargs):
        compra_id = kwargs.get('pk', None)
        instance = get_object_or_404(PedidoCompra, id=compra_id)
        if instance.status == '4':
            messages.error(request, f"Pedido de compra {instance.pk} já foi recebido e não pode ser cancelado.")
            return redirect(reverse_lazy('compras:listapedidocompraview'))
        instance.status = '2'
        instance.save(update_fields=['status'])
        messages.success(request, f"Pedido de compra {instance.pk} cancelado.")
        return redirect(reverse_lazy('compras:listapedidocompraview'))

class GerarCopiaOrcamentoCompraView(CustomView):
    permission_codename = 'add_orcamentocompra'
    def get(self, request, *args, **kwargs):
        compra_id = kwargs.get('pk', None)
        instance_orig = get_object_or_404(OrcamentoCompra, id=compra_id)
        nova_copia = OrcamentoCompra()
        campos_a_copiar = [f.name for f in Compra._meta.fields if f.name not in ['id', 'pk']]
        for field_name in campos_a_copiar:
            if hasattr(instance_orig, field_name):
                setattr(nova_copia, field_name, getattr(instance_orig, field_name))
        if hasattr(instance_orig, 'data_vencimento'): nova_copia.data_vencimento = instance_orig.data_vencimento
        nova_copia.status = '0'
        nova_copia.data_emissao = datetime.now().date()
        nova_copia.save()
        for item_orig in instance_orig.itens_compra.all():
            item_orig.pk = None; item_orig.id = None; item_orig.compra_id = nova_copia; item_orig.save()
        for pag_orig in instance_orig.parcela_pagamento.all():
             pag_orig.pk = None; pag_orig.id = None; pag_orig.compra_id = nova_copia; pag_orig.save() # VERIFICAR FK
        messages.success(request, f"Orçamento de compra {nova_copia.pk} copiado do orçamento {compra_id}.")
        return redirect(reverse_lazy('compras:editarorcamentocompraview', kwargs={'pk': nova_copia.id}))

class GerarCopiaPedidoCompraView(CustomView):
    permission_codename = 'add_pedidocompra'
    def get(self, request, *args, **kwargs):
        compra_id = kwargs.get('pk', None)
        instance_orig = get_object_or_404(PedidoCompra, id=compra_id)
        nova_copia = PedidoCompra()
        campos_a_copiar = [f.name for f in Compra._meta.fields if f.name not in ['id', 'pk']]
        for field_name in campos_a_copiar:
             if hasattr(instance_orig, field_name):
                setattr(nova_copia, field_name, getattr(instance_orig, field_name))
        if hasattr(instance_orig, 'data_entrega'): nova_copia.data_entrega = instance_orig.data_entrega
        nova_copia.status = '0'
        nova_copia.data_emissao = datetime.now().date()
        nova_copia.orcamento = None # Não copiar link para orçamento ao copiar pedido?
        nova_copia.save()
        for item_orig in instance_orig.itens_compra.all():
            item_orig.pk = None; item_orig.id = None; item_orig.compra_id = nova_copia; item_orig.save()
        for pag_orig in instance_orig.parcela_pagamento.all():
             pag_orig.pk = None; pag_orig.id = None; pag_orig.compra_id = nova_copia; pag_orig.save() # VERIFICAR FK
        messages.success(request, f"Pedido de compra {nova_copia.pk} copiado do pedido {compra_id}.")
        return redirect(reverse_lazy('compras:editarpedidocompraview', kwargs={'pk': nova_copia.id}))


class ReceberPedidoCompraView(CustomView):
    permission_codename = ['change_pedidocompra', 'add_entradaestoque']
    def get(self, request, *args, **kwargs):
        compra_id = kwargs.get('pk', None)
        pedido = get_object_or_404(PedidoCompra, id=compra_id)

        if pedido.status == '4':
             messages.warning(request, f"Pedido de compra {pedido.id} já consta como recebido.")
             return redirect(reverse_lazy('compras:listapedidocompraview'))
        elif pedido.status == '2':
             messages.error(request, f"Pedido de compra {pedido.id} está cancelado e não pode ser recebido.")
             return redirect(reverse_lazy('compras:listapedidocompraview'))

        lista_prod_estocado_atualizar = []
        lista_itens_movimento_criar = []
        valor_total_movimento = Decimal('0.00')

        if pedido.movimentar_estoque and pedido.local_dest:
            itens_pedido = pedido.itens_compra.select_related('produto').all()
            for item in itens_pedido:
                if item.produto and item.produto.controlar_estoque:
                    prod_estocado, created = ProdutoEstocado.objects.get_or_create(
                        local=pedido.local_dest, produto=item.produto,
                        defaults={'quantidade': Decimal('0.00')}
                    )
                    qtd_item = item.quantidade if item.quantidade is not None else Decimal('0')
                    if qtd_item <= 0: continue

                    # Preparar atualização de estoque
                    estoque_atual_prod = prod_estocado.produto.estoque_atual if prod_estocado.produto.estoque_atual is not None else Decimal('0')
                    novo_estoque_produto = estoque_atual_prod + qtd_item
                    qtd_local_atual = prod_estocado.quantidade if prod_estocado.quantidade is not None else Decimal('0')
                    nova_qtd_local = qtd_local_atual + qtd_item
                    lista_prod_estocado_atualizar.append({
                        'obj_prod_est': prod_estocado, 'nova_qtd_local': nova_qtd_local,
                        'obj_produto': prod_estocado.produto, 'novo_estoque_produto': novo_estoque_produto,
                    })

                    # Preparar item de movimento
                    item_mvmt = ItensMovimento(
                        produto = item.produto,
                        quantidade = qtd_item,
                        valor_unit = item.valor_unit if item.valor_unit is not None else Decimal('0.00')
                    )
                    subtotal_item = item.get_total() if hasattr(item, 'get_total') else item.vprod
                    item_mvmt.subtotal = subtotal_item if subtotal_item is not None else Decimal('0.00')
                    lista_itens_movimento_criar.append(item_mvmt)
                    valor_total_movimento += item_mvmt.subtotal

            if lista_itens_movimento_criar:
                 from django.db import transaction
                 try:
                     with transaction.atomic():
                         entrada_estoque = EntradaEstoque(
                             data_movimento = pedido.data_entrega if pedido.data_entrega else datetime.now().date(),
                             quantidade_itens = len(lista_itens_movimento_criar),
                             observacoes = f'Entrada de estoque pelo pedido de compra nº{pedido.id}',
                             tipo_movimento = '1',
                             valor_total = valor_total_movimento.quantize(Decimal('0.01')),
                             pedido_compra = pedido,
                             local_dest = pedido.local_dest
                         )
                         entrada_estoque.save()
                         for item_m in lista_itens_movimento_criar:
                             item_m.movimento_id = entrada_estoque
                         ItensMovimento.objects.bulk_create(lista_itens_movimento_criar)
                         for item_atualizar in lista_prod_estocado_atualizar:
                             prod = item_atualizar['obj_produto']
                             prod_est = item_atualizar['obj_prod_est']
                             prod.estoque_atual = item_atualizar['novo_estoque_produto']
                             prod_est.quantidade = item_atualizar['nova_qtd_local']
                             prod.save(update_fields=['estoque_atual'])
                             prod_est.save(update_fields=['quantidade'])
                         pedido.status = '4'
                         pedido.save(update_fields=['status'])
                         messages.success(request, f"<b>Pedido de compra {pedido.id} </b>recebido com sucesso e estoque atualizado.")
                 except Exception as e:
                      messages.error(request, f"Erro ao processar recebimento e estoque: {e}")
            else:
                 messages.info(request, f"Pedido {pedido.id} não continha itens válidos com controle de estoque. Nenhuma movimentação.")
                 # pedido.status = '4' # Mudar status mesmo sem movimentação?
                 # pedido.save(update_fields=['status'])
        else:
             pedido.status = '4' # Recebido sem estoque
             pedido.save(update_fields=['status'])
             messages.info(request, f"Pedido {pedido.id} marcado como recebido (sem movimentação de estoque).")

        return redirect(reverse_lazy('compras:listapedidocompraview'))


# --- Views de Geração de PDF para Compras (Refatorado com ReportLab) ---
class GerarPDFCompra(CustomView):

    def format_currency(self, value):
        """Helper para formatar moeda BRL, tratando None."""
        if value is None: value = Decimal('0.00')
        if not isinstance(value, Decimal):
            try: value = Decimal(value)
            except (TypeError, InvalidOperation): value = Decimal('0.00')
        if locale:
            try: return locale.format_string('%.2f', value, grouping=True)
            except (TypeError, ValueError, locale.Error): pass
        try: return "R$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception: return "R$ N/A"

    def gerar_pdf(self, title, compra, request): # Recebe request completo
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm, title=title)
        styles = getSampleStyleSheet()
        story = []

        # --- Estilos ---
        styles['Title'].fontSize = 14
        styles['Title'].alignment = TA_CENTER
        styles['Title'].spaceAfter = 8*mm
        style_normal = ParagraphStyle(name='NormalSmall', parent=styles['Normal'], fontSize=9, alignment=TA_LEFT, leading=11)
        style_normal_bold = ParagraphStyle(name='NormalBold', parent=style_normal, fontName='Helvetica-Bold')
        style_direita = ParagraphStyle(name='DireitaSmall', parent=style_normal, alignment=TA_RIGHT)
        style_direita_bold = ParagraphStyle(name='DireitaBoldSmall', parent=style_normal_bold, alignment=TA_RIGHT)
        style_heading = ParagraphStyle(name='SecaoHeading', parent=styles['h5'], fontSize=10, alignment=TA_LEFT, spaceBefore=3*mm, spaceAfter=3*mm)

        # --- Conteúdo ---
        # Cabeçalho: Logo e Dados da Empresa
        try:
            auth_user = request.user # Usar o usuário da requisição diretamente
            if not auth_user.is_authenticated: raise Exception("Usuário não autenticado.")
            try:
                 usuario_profile = UsuarioProfile.objects.select_related('user').get(user=auth_user)
            except UsuarioProfile.DoesNotExist:
                 raise Exception(f"Perfil de usuário (login.Usuario) não encontrado para {auth_user.username}")
            try:
                 m_empresa = MinhaEmpresa.objects.select_related('m_empresa', 'm_empresa__endereco_padrao', 'm_empresa__telefone_padrao').get(m_usuario=usuario_profile)
            except MinhaEmpresa.DoesNotExist:
                 raise Exception("Configuração 'Minha Empresa' não encontrada para o perfil deste usuário.")
            empresa = m_empresa.m_empresa
            if not empresa: raise Exception("Registro 'Minha Empresa' não está vinculado a uma Empresa.")

            dados_cabecalho = []
            logo_adicionado = False
            if empresa.logo_file and hasattr(empresa.logo_file, 'path'):
                 try:
                     logo = Image(empresa.logo_file.path, width=1.5*inch, height=0.75*inch); logo.hAlign = 'LEFT'
                     dados_cabecalho.append(logo); logo_adicionado = True
                 except FileNotFoundError: print(f"Aviso: Logo não encontrado"); dados_cabecalho.append(Paragraph("(Logo N/E)", style_normal))
                 except Exception as e_img: print(f"Erro logo: {e_img}"); dados_cabecalho.append(Paragraph("(Erro logo)", style_normal))
            else: dados_cabecalho.append(Paragraph("", style_normal))

            info_empresa_str = f"<b>{empresa.nome_razao_social}</b><br/>"
            if empresa.endereco_padrao: info_empresa_str += f"{getattr(empresa.endereco_padrao, 'format_endereco_completo', str(empresa.endereco_padrao))()}<br/>"
            if hasattr(empresa, 'format_cpf_cnpj'): info_empresa_str += f"CNPJ: {empresa.format_cpf_cnpj()}<br/>"
            if hasattr(empresa, 'inscricao_estadual') and empresa.inscricao_estadual: info_empresa_str += f"IE: {empresa.inscricao_estadual}<br/>"
            if empresa.telefone_padrao: info_empresa_str += f"Telefone: {empresa.telefone_padrao.telefone}"
            dados_cabecalho.append(Paragraph(info_empresa_str, style_normal))

            col_width_logo = 2*inch if logo_adicionado else 0.1*inch; col_width_info = doc.width - col_width_logo
            table_cabecalho = Table([dados_cabecalho], colWidths=[col_width_logo, col_width_info]); table_cabecalho.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),])); story.append(table_cabecalho)
            story.append(Spacer(1, 8*mm))

        except Exception as e:
             print(f"Erro ao carregar dados da empresa para PDF (usuário: {request.user.username if request.user.is_authenticated else 'Anônimo'}): {e}")
             story.append(Paragraph(f"Erro: Dados da empresa emitente não configurados ou erro ao carregar ({e}).", style_normal)); story.append(Spacer(1, 8*mm))
             # Considere retornar erro HTTP aqui se os dados da empresa são essenciais
             # return HttpResponse(f"Erro ao carregar dados da empresa: {e}", status=500)

        # Título
        story.append(Paragraph(title, styles['Title']))

        # Dados da Compra
        story.append(Paragraph("<b>DADOS DA COMPRA</b>", style_heading))
        data_emissao_str = compra.data_emissao.strftime("%d/%m/%Y") if compra.data_emissao else "N/I"
        compra_info = [
             [Paragraph("<b>Número:</b>", style_normal_bold), Paragraph(str(compra.pk), style_normal)],
             [Paragraph("<b>Data de Emissão:</b>", style_normal_bold), Paragraph(data_emissao_str, style_normal)],]
        if isinstance(compra, OrcamentoCompra): compra_info.append([Paragraph("<b>Data de Validade:</b>", style_normal_bold), Paragraph(compra.data_vencimento.strftime("%d/%m/%Y") if compra.data_vencimento else "N/I", style_normal)])
        elif isinstance(compra, PedidoCompra): compra_info.append([Paragraph("<b>Data de Entrega:</b>", style_normal_bold), Paragraph(compra.data_entrega.strftime("%d/%m/%Y") if compra.data_entrega else "N/I", style_normal)])
        compra_table = Table(compra_info, colWidths=[4*cm, None]); compra_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),('TOPPADDING', (0, 0), (-1, -1), 1),])); story.append(compra_table); story.append(Spacer(1, 5*mm))

        # Dados do Fornecedor
        if hasattr(compra, 'fornecedor') and compra.fornecedor:
             story.append(Paragraph("<b>DADOS DO FORNECEDOR</b>", style_heading)); fornecedor = compra.fornecedor
             forn_cpf_cnpj = fornecedor.format_cpf_cnpj() if hasattr(fornecedor, 'format_cpf_cnpj') else '(N/D)'
             fornecedor_info = [
                 [Paragraph("<b>Nome/Razão Social:</b>", style_normal_bold), Paragraph(fornecedor.nome_razao_social or '', style_normal)],
                 [Paragraph("<b>CPF/CNPJ:</b>", style_normal_bold), Paragraph(forn_cpf_cnpj, style_normal)],]
             if fornecedor.endereco_padrao: endereco_forn = fornecedor.endereco_padrao.format_endereco_completo() if hasattr(fornecedor.endereco_padrao, 'format_endereco_completo') else str(fornecedor.endereco_padrao); fornecedor_info.append([Paragraph("<b>Endereço:</b>", style_normal_bold), Paragraph(endereco_forn or '', style_normal)])
             if fornecedor.telefone_padrao: fornecedor_info.append([Paragraph("<b>Telefone:</b>", style_normal_bold), Paragraph(fornecedor.telefone_padrao.telefone or '', style_normal)])
             if fornecedor.email_padrao: fornecedor_info.append([Paragraph("<b>E-mail:</b>", style_normal_bold), Paragraph(fornecedor.email_padrao.email or '', style_normal)])
             fornecedor_table = Table(fornecedor_info, colWidths=[4*cm, None]); fornecedor_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0),('BOTTOMPADDING', (0, 0), (-1, -1), 1), ('TOPPADDING', (0, 0), (-1, -1), 1),])); story.append(fornecedor_table); story.append(Spacer(1, 5*mm))
        else: story.append(Paragraph("Fornecedor não informado.", style_normal)); story.append(Spacer(1, 5*mm))

        # Itens da Compra
        story.append(Paragraph("<b>ITENS DA COMPRA</b>", style_heading))
        itens_header = [ Paragraph("<b>Produto</b>", style_normal_bold), Paragraph("<b>Qtd.</b>", style_direita_bold), Paragraph("<b>Vl. Unit.</b>", style_direita_bold), Paragraph("<b>Total Item</b>", style_direita_bold) ]
        itens_data = [itens_header]; total_itens_calc = Decimal('0.00')
        for item in compra.itens_compra.all():
            if not item.produto: continue
            # *** USA get_total() DE ItensCompra ***
            total_item = item.get_total() if hasattr(item, 'get_total') else Decimal('0.00'); total_itens_calc += total_item
            itens_data.append([ Paragraph(item.produto.descricao or 'N/D', style_normal), Paragraph(str(item.quantidade or '0'), style_direita), Paragraph(self.format_currency(item.valor_unit), style_direita), Paragraph(self.format_currency(total_item), style_direita)])
        itens_table = Table(itens_data, colWidths=[None, 2*cm, 3*cm, 3*cm]); itens_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),('TEXTCOLOR', (0, 0), (-1, 0), colors.black),('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('ALIGN', (1, 1), (-1, -1), 'RIGHT'), ('ALIGN', (0, 1), (0, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 4), ('TOPPADDING', (0, 0), (-1, 0), 4), ('BOTTOMPADDING', (0, 1), (-1, -1), 2), ('TOPPADDING', (0, 1), (-1, -1), 2), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)])); story.append(itens_table); story.append(Spacer(1, 5*mm))

        # Totais
        story.append(Paragraph("<b>TOTAIS</b>", style_heading))
        # *** USA get_total_sem_imposto e get_total_impostos DE Compra ***
        subtotal_itens = compra.get_total_sem_imposto() if hasattr(compra, 'get_total_sem_imposto') else total_itens_calc
        impostos_totais = compra.get_total_impostos() if hasattr(compra, 'get_total_impostos') else Decimal('0.00')
        desconto_total = compra.get_valor_desconto_total() if hasattr(compra, 'get_valor_desconto_total') else Decimal('0.00')
        frete = compra.frete if hasattr(compra, 'frete') and compra.frete is not None else Decimal('0.00')
        seguro = compra.seguro if hasattr(compra, 'seguro') and compra.seguro is not None else Decimal('0.00')
        despesas = compra.despesas if hasattr(compra, 'despesas') and compra.despesas is not None else Decimal('0.00')
        total_geral_calc = subtotal_itens - desconto_total + impostos_totais + frete + seguro + despesas
        total_geral_display = compra.valor_total if compra.valor_total is not None else total_geral_calc

        totais_data = [
            [Paragraph("Subtotal Itens:", style_direita), Paragraph(self.format_currency(total_itens_calc), style_direita)],
            [Paragraph("Desconto Total:", style_direita), Paragraph(f"(-) {self.format_currency(desconto_total)}", style_direita)],
            [Paragraph("Frete:", style_direita), Paragraph(f"(+) {self.format_currency(frete)}", style_direita)],
            [Paragraph("Seguro:", style_direita), Paragraph(f"(+) {self.format_currency(seguro)}", style_direita)],
            [Paragraph("Despesas:", style_direita), Paragraph(f"(+) {self.format_currency(despesas)}", style_direita)],
            [Paragraph("Impostos (Itens):", style_direita), Paragraph(f"(+) {self.format_currency(impostos_totais)}", style_direita)],
            [Paragraph("Total Geral:", style_direita_bold), Paragraph(self.format_currency(total_geral_display), style_direita_bold)],]
        totais_table = Table(totais_data, colWidths=[None, 3.5*cm]); totais_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'RIGHT'), ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 1), ('TOPPADDING', (0, 0), (-1, -1), 1), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), ('LINEABOVE', (0, -1), (-1,-1), 0.5, colors.grey),])); story.append(totais_table); story.append(Spacer(1, 5*mm))

        # Condições de Pagamento
        if hasattr(compra, 'cond_pagamento') and compra.cond_pagamento:
            story.append(Paragraph("<b>CONDIÇÕES DE PAGAMENTO</b>", style_heading))
            cond_desc = compra.cond_pagamento.descricao if compra.cond_pagamento.descricao else "Não informado"; story.append(Paragraph(cond_desc, style_normal))
            parcelas = compra.parcela_pagamento.all()
            if parcelas:
                story.append(Spacer(1, 2*mm))
                parcela_header = [ Paragraph("<b>P.</b>", style_normal_bold), Paragraph("<b>Venc.</b>", style_normal_bold), Paragraph("<b>Valor</b>", style_direita_bold) ]; parcela_data = [parcela_header]
                for p in parcelas:
                     venc_str = p.vencimento.strftime("%d/%m/%Y") if p.vencimento else "N/D"; valor_str = self.format_currency(p.valor_parcela)
                     parcela_data.append([ Paragraph(str(p.indice_parcela) if p.indice_parcela else "-", style_normal), Paragraph(venc_str, style_normal), Paragraph(valor_str, style_direita)])
                parcela_table = Table(parcela_data, colWidths=[2*cm, 4*cm, 4*cm]); parcela_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('ALIGN', (0, 1), (1, -1), 'CENTER'), ('ALIGN', (2, 1), (2, -1), 'RIGHT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 4), ('TOPPADDING', (0, 0), (-1, 0), 4), ('BOTTOMPADDING', (0, 1), (-1, -1), 2), ('TOPPADDING', (0, 1), (-1, -1), 2), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)])); story.append(parcela_table)
            story.append(Spacer(1, 5*mm))

        # Observações
        if compra.observacoes:
            story.append(Paragraph("<b>OBSERVAÇÕES</b>", style_heading)); obs_text = compra.observacoes.replace('\n', '<br/>'); story.append(Paragraph(obs_text, style_normal)); story.append(Spacer(1, 5*mm))

        # --- Geração ---
        try:
            doc.build(story)
            pdf = buffer.getvalue()
            buffer.close()
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{title}.pdf"' # Abre no navegador
            response.write(pdf)
            return response
        except Exception as e:
            print(f"Erro final ao construir PDF de compra: {e}")
            import traceback
            traceback.print_exc()
            return HttpResponse(f"Erro interno ao gerar o PDF: {e}", status=500)


# Views específicas que herdam da base e chamam gerar_pdf
class GerarPDFOrcamentoCompra(GerarPDFCompra):
    permission_codename = 'change_orcamentocompra'

    def get(self, request, *args, **kwargs):
        compra_id = kwargs.get('pk', None)
        obj = get_object_or_404(OrcamentoCompra, pk=compra_id)
        title = f'Orçamento de Compra nº {compra_id}'
        # Chama o método gerar_pdf da classe base, passando request
        return self.gerar_pdf(title, obj, request)


class GerarPDFPedidoCompra(GerarPDFCompra):
    permission_codename = 'change_pedidocompra'

    def get(self, request, *args, **kwargs):
        compra_id = kwargs.get('pk', None)
        obj = get_object_or_404(PedidoCompra, pk=compra_id)
        title = f'Pedido de Compra nº {compra_id}'
        # Chama o método gerar_pdf da classe base, passando request
        return self.gerar_pdf(title, obj, request)

# --- FIM DA SEÇÃO DE PDF ATUALIZADA ---