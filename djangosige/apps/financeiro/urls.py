# -*- coding: utf-8 -*-

from django.urls import path, include, re_path
from . import views

app_name = 'financeiro'
urlpatterns = [
    # Lancamentos
    # Gerar lancamento
    path('gerarlancamento/', views.GerarLancamentoView.as_view(),
        name='gerarlancamento'),
    # Lista todos lancamentos
    path('lancamentos/', views.LancamentoListView.as_view(),
        name='listalancamentoview'),

    # Contas a pagar
    # financeiro/contapagar/adicionar/
    path('contapagar/adicionar/',
        views.AdicionarContaPagarView.as_view(), name='addcontapagarview'),
    # financeiro/contapagar/listacontapagar
    path('contapagar/listacontapagar/',
        views.ContaPagarListView.as_view(), name='listacontapagarview'),
    # financeiro/contapagar/editar/
    path('contapagar/editar/<int:pk>/',
        views.EditarContaPagarView.as_view(), name='editarcontapagarview'),
    # financeiro/contapagar/listacontapagar/atrasadas/
    path('contapagar/listacontapagar/atrasadas/',
        views.ContaPagarAtrasadasListView.as_view(), name='listacontapagaratrasadasview'),
    # financeiro/contapagar/listacontapagar/hoje/
    path('contapagar/listacontapagar/hoje/',
        views.ContaPagarHojeListView.as_view(), name='listacontapagarhojeview'),

    # Contas a receber
    # financeiro/contareceber/adicionar/
    path('contareceber/adicionar/',
        views.AdicionarContaReceberView.as_view(), name='addcontareceberview'),
    # financeiro/contareceber/listacontapagar
    path('contareceber/listacontareceber/',
        views.ContaReceberListView.as_view(), name='listacontareceberview'),
    # financeiro/contareceber/editar/
    path('contareceber/editar/<int:pk>/',
        views.EditarContaReceberView.as_view(), name='editarcontareceberview'),
    # financeiro/contareceber/listacontapagar/atrasadas/
    path('contareceber/listacontareceber/atrasadas/',
        views.ContaReceberAtrasadasListView.as_view(), name='listacontareceberatrasadasview'),
    # financeiro/contareceber/listacontapagar/hoje/
    path('contareceber/listacontareceber/hoje/',
        views.ContaReceberHojeListView.as_view(), name='listacontareceberhojeview'),

    # Pagamentos
    # financeiro/pagamento/adicionar/
    path('pagamento/adicionar/',
        views.AdicionarSaidaView.as_view(), name='addpagamentoview'),
    # financeiro/pagamento/listacontapagar
    path('pagamento/listapagamento/',
        views.SaidaListView.as_view(), name='listapagamentosview'),
    # financeiro/pagamento/editar/
    path('pagamento/editar/<int:pk>/',
        views.EditarSaidaView.as_view(), name='editarpagamentoview'),

    # Recebimentos
    # financeiro/recebimento/adicionar/
    path('recebimento/adicionar/',
        views.AdicionarEntradaView.as_view(), name='addrecebimentoview'),
    # financeiro/recebimento/listarecebimento
    path('recebimento/listarecebimento/',
        views.EntradaListView.as_view(), name='listarecebimentosview'),
    # financeiro/recebimento/editar/
    path('recebimento/editar/<int:pk>/',
        views.EditarEntradaView.as_view(), name='editarrecebimentoview'),

    # Faturar Pedido de venda
    path('faturarpedidovenda/<int:pk>/',
        views.FaturarPedidoVendaView.as_view(), name='faturarpedidovenda'),
    # Faturar Pedido de compra
    path('faturarpedidocompra/<int:pk>/',
        views.FaturarPedidoCompraView.as_view(), name='faturarpedidocompra'),

    # Plano de contas
    # financeiro/planodecontas
    path('planodecontas/', views.PlanoContasView.as_view(), name='planocontasview'),
    # financeiro/planodecontas/adicionargrupo/
    path('planodecontas/adicionargrupo/',
        views.AdicionarGrupoPlanoContasView.as_view(), name='addgrupoview'),
    # financeiro/planodecontas/editargrupo/
    path('planodecontas/editargrupo/<int:pk>/',
        views.EditarGrupoPlanoContasView.as_view(), name='editargrupoview'),

    # Fluxo de caixa
    # financeiro/fluxodecaixa
    path('fluxodecaixa/', views.FluxoCaixaView.as_view(), name='fluxodecaixaview'),
]
