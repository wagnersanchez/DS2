# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse

from djangosige.apps.base.custom_views import CustomView, CustomCreateView, CustomListView, CustomUpdateView

from djangosige.apps.vendas.forms import OrcamentoVendaForm, PedidoVendaForm, ItensVendaFormSet, PagamentoFormSet
from djangosige.apps.vendas.models import OrcamentoVenda, PedidoVenda, ItensVenda, Pagamento
from djangosige.apps.cadastro.models import MinhaEmpresa
from djangosige.apps.login.models import Usuario
from djangosige.configs.settings import MEDIA_ROOT


from datetime import datetime
from io import BytesIO

# from .report_vendas import VendaReport

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm, inch


class AdicionarVendaView(CustomCreateView):

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, id=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(AdicionarVendaView, self).get_context_data(**kwargs)
        return self.view_context(context)

    def get(self, request, form_class, *args, **kwargs):
        self.object = None

        form = self.get_form(form_class)
        form.initial['vendedor'] = request.user.first_name or request.user
        form.initial['data_emissao'] = datetime.today().strftime('%d/%m/%Y')

        produtos_form = ItensVendaFormSet(prefix='produtos_form')
        pagamento_form = PagamentoFormSet(prefix='pagamento_form')

        return self.render_to_response(self.get_context_data(form=form,
                                                             produtos_form=produtos_form,
                                                             pagamento_form=pagamento_form))

    def post(self, request, form_class, *args, **kwargs):
        self.object = None
        # Tirar . dos campos decimais
        req_post = request.POST.copy()

        for key in req_post:
            if ('desconto' in key or
                'quantidade' in key or
                'valor' in key or
                'frete' in key or
                'despesas' in key or
                'seguro' in key or
                    'total' in key):
                req_post[key] = req_post[key].replace('.', '')

        request.POST = req_post

        form = self.get_form(form_class)
        produtos_form = ItensVendaFormSet(request.POST, prefix='produtos_form')
        pagamento_form = PagamentoFormSet(
            request.POST, prefix='pagamento_form')

        if (form.is_valid() and produtos_form.is_valid() and pagamento_form.is_valid()):
            self.object = form.save(commit=False)
            self.object.save()

            for pform in produtos_form:
                if pform.cleaned_data != {}:
                    itens_venda_obj = pform.save(commit=False)
                    itens_venda_obj.venda_id = self.object
                    itens_venda_obj.calcular_pis_cofins()
                    itens_venda_obj.save()

            pagamento_form.instance = self.object
            pagamento_form.save()

            return self.form_valid(form)

        return self.form_invalid(form=form,
                                 produtos_form=produtos_form,
                                 pagamento_form=pagamento_form)


class AdicionarOrcamentoVendaView(AdicionarVendaView):
    form_class = OrcamentoVendaForm
    template_name = "vendas/orcamento_venda/orcamento_venda_add.html"
    success_url = reverse_lazy('vendas:listaorcamentovendaview')
    success_message = "<b>Orçamento de venda %(id)s </b>adicionado com sucesso."
    permission_codename = 'add_orcamentovenda'

    def view_context(self, context):
        context['title_complete'] = 'ADICIONAR ORÇAMENTO DE VENDA'
        context['return_url'] = reverse_lazy('vendas:listaorcamentovendaview')
        return context

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarOrcamentoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarOrcamentoVendaView, self).post(request, form_class, *args, **kwargs)


class AdicionarPedidoVendaView(AdicionarVendaView):
    form_class = PedidoVendaForm
    template_name = "vendas/pedido_venda/pedido_venda_add.html"
    success_url = reverse_lazy('vendas:listapedidovendaview')
    success_message = "<b>Pedido de venda %(id)s </b>adicionado com sucesso."
    permission_codename = 'add_pedidovenda'

    def view_context(self, context):
        context['title_complete'] = 'ADICIONAR PEDIDO DE VENDA'
        context['return_url'] = reverse_lazy('vendas:listapedidovendaview')
        return context

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarPedidoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        return super(AdicionarPedidoVendaView, self).post(request, form_class, *args, **kwargs)


class VendaListView(CustomListView):

    def get_context_data(self, **kwargs):
        context = super(VendaListView, self).get_context_data(**kwargs)
        return self.view_context(context)


class OrcamentoVendaListView(VendaListView):
    template_name = 'vendas/orcamento_venda/orcamento_venda_list.html'
    model = OrcamentoVenda
    context_object_name = 'all_orcamentos'
    success_url = reverse_lazy('vendas:listaorcamentovendaview')
    permission_codename = 'view_orcamentovenda'

    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE VENDA'
        context['add_url'] = reverse_lazy('vendas:addorcamentovendaview')
        return context


class OrcamentoVendaVencidosListView(OrcamentoVendaListView):
    success_url = reverse_lazy('vendas:listaorcamentovendavencidoview')

    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE VENDA VENCIDOS'
        context['add_url'] = reverse_lazy('vendas:addorcamentovendaview')
        return context

    def get_queryset(self):
        return OrcamentoVenda.objects.filter(data_vencimento__lte=datetime.now().date(), status='0')


class OrcamentoVendaVencimentoHojeListView(OrcamentoVendaListView):
    success_url = reverse_lazy('vendas:listaorcamentovendahojeview')

    def view_context(self, context):
        context['title_complete'] = 'ORÇAMENTOS DE VENDA COM VENCIMENTO DIA ' + \
            datetime.now().date().strftime('%d/%m/%Y')
        context['add_url'] = reverse_lazy('vendas:addorcamentovendaview')
        return context

    def get_queryset(self):
        return OrcamentoVenda.objects.filter(data_vencimento=datetime.now().date(), status='0')


class PedidoVendaListView(VendaListView):
    template_name = 'vendas/pedido_venda/pedido_venda_list.html'
    model = PedidoVenda
    context_object_name = 'all_pedidos'
    success_url = reverse_lazy('vendas:listapedidovendaview')
    permission_codename = 'view_pedidovenda'

    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE VENDA'
        context['add_url'] = reverse_lazy('vendas:addpedidovendaview')
        return context


class PedidoVendaAtrasadosListView(PedidoVendaListView):
    success_url = reverse_lazy('vendas:listapedidovendaatrasadosview')

    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE VENDA ATRASADOS'
        context['add_url'] = reverse_lazy('vendas:addpedidovendaview')
        return context

    def get_queryset(self):
        return PedidoVenda.objects.filter(data_entrega__lte=datetime.now().date(), status='0')


class PedidoVendaEntregaHojeListView(PedidoVendaListView):
    success_url = reverse_lazy('vendas:listapedidovendahojeview')

    def view_context(self, context):
        context['title_complete'] = 'PEDIDOS DE VENDA COM ENTREGA DIA ' + \
            datetime.now().date().strftime('%d/%m/%Y')
        context['add_url'] = reverse_lazy('vendas:addpedidovendaview')
        return context

    def get_queryset(self):
        return PedidoVenda.objects.filter(data_entrega=datetime.now().date(), status='0')


class EditarVendaView(CustomUpdateView):

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, id=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(EditarVendaView, self).get_context_data(**kwargs)
        return self.view_context(context)

    def get(self, request, form_class, *args, **kwargs):

        form = form = self.get_form(form_class)
        form.initial['total_sem_imposto'] = self.object.get_total_sem_imposto()

        produtos_form = ItensVendaFormSet(
            instance=self.object, prefix='produtos_form')
        itens_list = ItensVenda.objects.filter(venda_id=self.object.id)
        produtos_form.initial = [{'total_sem_desconto': item.get_total_sem_desconto(),
                                  'total_impostos': item.get_total_impostos(),
                                  'total_com_impostos': item.get_total_com_impostos()} for item in itens_list]

        pagamento_form = PagamentoFormSet(
            instance=self.object, prefix='pagamento_form')

        if ItensVenda.objects.filter(venda_id=self.object.pk).count():
            produtos_form.extra = 0
        if Pagamento.objects.filter(venda_id=self.object.pk).count():
            pagamento_form.extra = 0

        return self.render_to_response(self.get_context_data(form=form, produtos_form=produtos_form, pagamento_form=pagamento_form))

    def post(self, request, form_class, *args, **kwargs):
        # Tirar . dos campos decimais
        req_post = request.POST.copy()

        for key in req_post:
            if ('desconto' in key or
                'quantidade' in key or
                'valor' in key or
                'frete' in key or
                'despesas' in key or
                'seguro' in key or
                    'total' in key):
                req_post[key] = req_post[key].replace('.', '')

        request.POST = req_post

        form = self.get_form(form_class)
        produtos_form = ItensVendaFormSet(
            request.POST, prefix='produtos_form', instance=self.object)
        pagamento_form = PagamentoFormSet(
            request.POST, prefix='pagamento_form', instance=self.object)

        if (form.is_valid() and produtos_form.is_valid() and pagamento_form.is_valid()):
            self.object = form.save(commit=False)
            self.object.save()

            for pform in produtos_form:
                if pform.cleaned_data != {}:
                    itens_venda_obj = pform.save(commit=False)
                    itens_venda_obj.venda_id = self.object
                    itens_venda_obj.calcular_pis_cofins()
                    itens_venda_obj.save()

            pagamento_form.instance = self.object
            pagamento_form.save()

            return self.form_valid(form)

        return self.form_invalid(form=form,
                                 produtos_form=produtos_form,
                                 pagamento_form=pagamento_form)


class EditarOrcamentoVendaView(EditarVendaView):
    form_class = OrcamentoVendaForm
    model = OrcamentoVenda
    template_name = "vendas/orcamento_venda/orcamento_venda_edit.html"
    success_url = reverse_lazy('vendas:listaorcamentovendaview')
    success_message = "<b>Orçamento de venda %(id)s </b>editado com sucesso."
    permission_codename = 'change_orcamentovenda'

    def view_context(self, context):
        context['title_complete'] = 'EDITAR ORÇAMENTO DE VENDA N°' + \
            str(self.object.id)
        context['return_url'] = reverse_lazy('vendas:listaorcamentovendaview')
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarOrcamentoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarOrcamentoVendaView, self).post(request, form_class, *args, **kwargs)


class EditarPedidoVendaView(EditarVendaView):
    form_class = PedidoVendaForm
    model = PedidoVenda
    template_name = "vendas/pedido_venda/pedido_venda_edit.html"
    success_url = reverse_lazy('vendas:listapedidovendaview')
    success_message = "<b>Pedido de venda %(id)s </b>editado com sucesso."
    permission_codename = 'change_pedidovenda'

    def view_context(self, context):
        context['title_complete'] = 'EDITAR PEDIDO DE VENDA N°' + \
            str(self.object.id)
        context['return_url'] = reverse_lazy('vendas:listapedidovendaview')
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarPedidoVendaView, self).get(request, form_class, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        return super(EditarPedidoVendaView, self).post(request, form_class, *args, **kwargs)


class GerarPedidoVendaView(CustomView):
    permission_codename = ['add_pedidovenda', 'change_pedidovenda', ]

    def get(self, request, *args, **kwargs):
        orcamento_id = kwargs.get('pk', None)
        orcamento = OrcamentoVenda.objects.get(id=orcamento_id)
        itens_venda = orcamento.itens_venda.all()
        pagamentos = orcamento.parcela_pagamento.all()
        novo_pedido = PedidoVenda()

        for field in orcamento._meta.fields:
            setattr(novo_pedido, field.name, getattr(orcamento, field.name))

        novo_pedido.venda_ptr = None
        novo_pedido.pk = None
        novo_pedido.id = None
        novo_pedido.status = '0'
        orcamento.status = '1'  # Baixado
        orcamento.save()
        novo_pedido.orcamento = orcamento
        novo_pedido.save()

        for item in itens_venda:
            item.pk = None
            item.id = None
            item.save()
            novo_pedido.itens_venda.add(item)

        for pagamento in pagamentos:
            pagamento.pk = None
            pagamento.id = None
            pagamento.save()
            novo_pedido.parcela_pagamento.add(pagamento)

        return redirect(reverse_lazy('vendas:editarpedidovendaview', kwargs={'pk': novo_pedido.id}))


class CancelarOrcamentoVendaView(CustomView):
    permission_codename = 'change_orcamentovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = OrcamentoVenda.objects.get(id=venda_id)
        instance.status = '2'
        instance.save()
        return redirect(reverse_lazy('vendas:editarorcamentovendaview', kwargs={'pk': instance.id}))


class CancelarPedidoVendaView(CustomView):
    permission_codename = 'change_pedidovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = PedidoVenda.objects.get(id=venda_id)
        instance.status = '2'
        instance.save()
        return redirect(reverse_lazy('vendas:editarpedidovendaview', kwargs={'pk': instance.id}))


class GerarCopiaVendaView(CustomView):

    def get(self, request, instance, redirect_url, *args, **kwargs):
        itens_venda = instance.itens_venda.all()
        pagamentos = instance.parcela_pagamento.all()

        instance.pk = None
        instance.id = None
        instance.status = '0'
        instance.save()

        for item in itens_venda:
            item.pk = None
            item.id = None
            item.save()
            instance.itens_venda.add(item)

        for pagamento in pagamentos:
            pagamento.pk = None
            pagamento.id = None
            pagamento.save()
            instance.parcela_pagamento.add(pagamento)

        return redirect(reverse_lazy(redirect_url, kwargs={'pk': instance.id}))


class GerarCopiaOrcamentoVendaView(GerarCopiaVendaView):
    permission_codename = 'add_orcamentovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = OrcamentoVenda.objects.get(id=venda_id)
        redirect_url = 'vendas:editarorcamentovendaview'
        return super(GerarCopiaOrcamentoVendaView, self).get(request, instance, redirect_url, *args, **kwargs)


class GerarCopiaPedidoVendaView(GerarCopiaVendaView):
    permission_codename = 'add_pedidovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        instance = PedidoVenda.objects.get(id=venda_id)
        redirect_url = 'vendas:editarpedidovendaview'
        return super(GerarCopiaPedidoVendaView, self).get(request, instance, redirect_url, *args, **kwargs)


class GerarPDFVenda(CustomView):
    def gerar_pdf(self, title, venda, user_id):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=title
        )
        
        styles = getSampleStyleSheet()
        elements = []

        # Estilo personalizado
        style_title = ParagraphStyle(
            name='Title',
            parent=styles['Title'],
            fontSize=14,
            alignment=1,
            spaceAfter=12,
        )
        style_normal = styles['Normal']
        style_heading = styles['Heading4']

        # Logo da empresa
        try:
            usuario = Usuario.objects.get(pk=user_id)
            m_empresa = MinhaEmpresa.objects.get(m_usuario=usuario)
            empresa = m_empresa.m_empresa
            
            if empresa.logo_file and empresa.logo_file != 'imagens/logo.png':
                logo_path = f"{MEDIA_ROOT}{empresa.logo_file}"
                logo = Image(logo_path, width=2*inch, height=1*inch)
                elements.append(logo)
                elements.append(Spacer(1, 12))
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")

        # Título do documento
        elements.append(Paragraph(title, style_title))
        elements.append(Spacer(1, 12))

        # Dados da Empresa
        try:
            elements.append(Paragraph(f"<b>{empresa.nome_razao_social}</b>", style_heading))
            
            if empresa.endereco_padrao:
                endereco = empresa.endereco_padrao.format_endereco_completo
                elements.append(Paragraph(endereco, style_normal))
            
            if empresa.telefone_padrao:
                telefone = empresa.telefone_padrao.telefone
                elements.append(Paragraph(f"Telefone: {telefone}", style_normal))
            
            elements.append(Spacer(1, 12))
        except Exception as e:
            print(f"Erro ao carregar dados da empresa: {e}")

        # Dados da Venda
        elements.append(Paragraph("<b>DADOS DA VENDA</b>", style_heading))
        
        # Tratamento para datas nulas
        data_emissao = venda.data_emissao.strftime("%d/%m/%Y") if venda.data_emissao else "Não informada"
        
        # Verifica o tipo de venda antes de acessar campos específicos
        if isinstance(venda, OrcamentoVenda):
            data_vencimento = venda.data_vencimento.strftime("%d/%m/%Y") if venda.data_vencimento else "Não informada"
        elif isinstance(venda, PedidoVenda):
            data_entrega = venda.data_entrega.strftime("%d/%m/%Y") if venda.data_entrega else "Não informada"
        else:
            data_vencimento = ""
            data_entrega = ""
        
        venda_data = [
            ["Número:", str(venda.id)],
            ["Data de Emissão:", data_emissao],
        ]
        
        if isinstance(venda, OrcamentoVenda):
            venda_data.append(["Data de Validade:", data_vencimento])
        elif isinstance(venda, PedidoVenda):
            venda_data.append(["Data de Entrega:", data_entrega])
        
        venda_table = Table(venda_data, colWidths=[80 * mm, 100 * mm])
        venda_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(venda_table)
        elements.append(Spacer(1, 12))

        # Dados do Cliente
        elements.append(Paragraph("<b>DADOS DO CLIENTE</b>", style_heading))
        
        cliente = venda.cliente
        cliente_data = [
            ["Nome/Razão Social:", cliente.nome_razao_social],
            ["CPF/CNPJ:", cliente.format_cpf_cnpj()],
        ]
        
        if cliente.endereco_padrao:
            cliente_data.append(["Endereço:", cliente.endereco_padrao.format_endereco_completo])
        if cliente.telefone_padrao:
            cliente_data.append(["Telefone:", cliente.telefone_padrao.telefone])
        if cliente.email_padrao:
            cliente_data.append(["E-mail:", cliente.email_padrao.email])
        
        cliente_table = Table(cliente_data, colWidths=[80 * mm, 100 * mm])
        cliente_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(cliente_table)
        elements.append(Spacer(1, 12))

        # Itens da Venda
        elements.append(Paragraph("<b>ITENS DA VENDA</b>", style_heading))
        
        itens = venda.itens_venda.all()
        itens_data = [["Produto", "Quantidade", "Valor Unit.", "Total"]]
        
        for item in itens:
            itens_data.append([
                item.produto.descricao,
                str(item.quantidade),
                f"R$ {item.valor_unit:.2f}",
                f"R$ {item.get_total():.2f}",
            ])
        
        itens_table = Table(itens_data, colWidths=[100 * mm, 30 * mm, 30 * mm, 30 * mm])
        itens_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#CCCCCC")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        elements.append(itens_table)
        elements.append(Spacer(1, 12))

        # Totais
        elements.append(Paragraph("<b>TOTAIS</b>", style_heading))
        
        totais_data = [
            ["Subtotal:", f"R$ {venda.get_total_sem_imposto():.2f}"],
            ["Impostos:", f"R$ {venda.get_total_impostos():.2f}"],
            ["Total:", f"R$ {venda.valor_total:.2f}"],
        ]
        
        totais_table = Table(totais_data, colWidths=[130 * mm, 50 * mm])
        totais_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(totais_table)
        elements.append(Spacer(1, 12))

        # Condições de Pagamento
        if venda.cond_pagamento:
            elements.append(Paragraph("<b>CONDIÇÕES DE PAGAMENTO</b>", style_heading))
            elements.append(Paragraph(venda.cond_pagamento.descricao, style_normal))
            elements.append(Spacer(1, 12))

        # Observações
        elements.append(Paragraph("<b>OBSERVAÇÕES</b>", style_heading))
        elements.append(Paragraph(venda.observacoes or "Nenhuma observação.", style_normal))
        elements.append(Spacer(1, 12))

        # Vendedor
        elements.append(Paragraph(f"<b>Vendedor:</b> {venda.vendedor}", style_normal))

        # Gera o PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{title}.pdf"'
        response.write(pdf)
        return response


class GerarPDFOrcamentoVenda(GerarPDFVenda):
    permission_codename = 'change_orcamentovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        if not venda_id:
            return HttpResponse('Objeto não encontrado.')

        obj = get_object_or_404(OrcamentoVenda, pk=venda_id)  # Agora a função está disponível
        title = f'Orçamento de venda nº {venda_id}'
        return self.gerar_pdf(title, obj, request.user.id)


class GerarPDFPedidoVenda(GerarPDFVenda):
    permission_codename = 'change_pedidovenda'

    def get(self, request, *args, **kwargs):
        venda_id = kwargs.get('pk', None)
        if not venda_id:
            return HttpResponse('Objeto não encontrado.')

        obj = get_object_or_404(PedidoVenda, pk=venda_id)  # Agora a função está disponível
        title = f'Pedido de venda nº {venda_id}'
        return self.gerar_pdf(title, obj, request.user.id)
        