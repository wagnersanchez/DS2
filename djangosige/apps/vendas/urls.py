# -*- coding: utf-8 -*-

from django.urls import path, include, re_path
from . import views

app_name = 'vendas'
urlpatterns = [
    # Orcamentos de venda
    # vendas/orcamentovenda/adicionar/
    path('orcamentovenda/adicionar/',
        views.AdicionarOrcamentoVendaView.as_view(), name='addorcamentovendaview'),
    # vendas/orcamentovenda/listaorcamentovenda
    path('orcamentovenda/listaorcamentovenda/',
        views.OrcamentoVendaListView.as_view(), name='listaorcamentovendaview'),
    # vendas/orcamentovenda/editar/
    path('orcamentovenda/editar/<int:pk>/',
        views.EditarOrcamentoVendaView.as_view(), name='editarorcamentovendaview'),
    # vendas/orcamentovenda/listaorcamentovenda/vencidos
    path('orcamentovenda/listaorcamentovenda/vencidos/',
        views.OrcamentoVendaVencidosListView.as_view(), name='listaorcamentovendavencidoview'),
    # vendas/orcamentovenda/listaorcamentovenda/hoje
    path('orcamentovenda/listaorcamentovenda/hoje/',
        views.OrcamentoVendaVencimentoHojeListView.as_view(), name='listaorcamentovendahojeview'),

    # Pedidos de venda
    # vendas/pedidovenda/adicionar/
    path('pedidovenda/adicionar/',
        views.AdicionarPedidoVendaView.as_view(), name='addpedidovendaview'),
    # vendas/pedidovenda/listapedidovenda
    path('pedidovenda/listapedidovenda/',
        views.PedidoVendaListView.as_view(), name='listapedidovendaview'),
    # vendas/pedidovenda/editar/
    path('pedidovenda/editar/<int:pk>/',
        views.EditarPedidoVendaView.as_view(), name='editarpedidovendaview'),
    # vendas/pedidovenda/listapedidovenda/atrasados
    path('pedidovenda/listapedidovenda/atrasados/',
        views.PedidoVendaAtrasadosListView.as_view(), name='listapedidovendaatrasadosview'),
    # vendas/pedidovenda/listapedidovenda/hoje
    path('pedidovenda/listapedidovenda/hoje/',
        views.PedidoVendaEntregaHojeListView.as_view(), name='listapedidovendahojeview'),

    # Condicao pagamento
    # vendas/pagamento/adicionar/
    path('pagamento/adicionar/', views.AdicionarCondicaoPagamentoView.as_view(),
        name='addcondicaopagamentoview'),
    # vendas/pagamento/listacondicaopagamento
    path('pagamento/listacondicaopagamento/',
        views.CondicaoPagamentoListView.as_view(), name='listacondicaopagamentoview'),
    # vendas/pagamento/editar/
    path('pagamento/editar/<int:pk>/', views.EditarCondicaoPagamentoView.as_view(
    ), name='editarcondicaopagamentoview'),

    # Request ajax views
    path('infocondpagamento/', views.InfoCondicaoPagamento.as_view(),
        name='infocondpagamento'),
    path('infovenda/', views.InfoVenda.as_view(), name='infovenda'),

    # Gerar pdf orcamento
    path('gerarpdforcamentovenda/<int:pk>/',
        views.GerarPDFOrcamentoVenda.as_view(), name='gerarpdforcamentovenda'),
    # Gerar pdf pedido
    path('gerarpdfpedidovenda/<int:pk>/',
        views.GerarPDFPedidoVenda.as_view(), name='gerarpdfpedidovenda'),
    # Gerar pedido a partir de um orçamento
    path('gerarpedidovenda/<int:pk>/',
        views.GerarPedidoVendaView.as_view(), name='gerarpedidovenda'),
    # Copiar orcamento cancelado ou baixado
    path('copiarorcamentovenda/<int:pk>/',
        views.GerarCopiaOrcamentoVendaView.as_view(), name='copiarorcamentovenda'),
    # Copiar pedido cancelado ou baixado
    path('copiarpedidovenda/<int:pk>/',
        views.GerarCopiaPedidoVendaView.as_view(), name='copiarpedidovenda'),
    # Cancelar Orcamento de venda
    path('cancelarorcamentovenda/<int:pk>/',
        views.CancelarOrcamentoVendaView.as_view(), name='cancelarorcamentovenda'),
    # Cancelar Pedido de venda
    path('cancelarpedidovenda/<int:pk>/',
        views.CancelarPedidoVendaView.as_view(), name='cancelarpedidovenda'),
]
