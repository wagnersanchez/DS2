# -*- coding: utf-8 -*-

from django.urls import path, include, re_path
from . import views

app_name = 'compras'
urlpatterns = [
    # Orcamentos de compra
    # compras/orcamentocompra/adicionar/
    path('orcamentocompra/adicionar/',
        views.AdicionarOrcamentoCompraView.as_view(), name='addorcamentocompraview'),
    # compras/orcamentocompra/listaorcamentocompra
    path('orcamentocompra/listaorcamentocompra/',
        views.OrcamentoCompraListView.as_view(), name='listaorcamentocompraview'),
    # compras/orcamentocompra/editar/
    path('orcamentocompra/editar/<int:pk>/',
        views.EditarOrcamentoCompraView.as_view(), name='editarorcamentocompraview'),
    # compras/orcamentocompra/listaorcamentocompra/vencidos/
    path('orcamentocompra/listaorcamentocompra/vencidos/',
        views.OrcamentoCompraVencidosListView.as_view(), name='listaorcamentocompravencidosview'),
    # compras/orcamentocompra/listaorcamentocompra/hoje/
    path('orcamentocompra/listaorcamentocompra/hoje/',
        views.OrcamentoCompraVencimentoHojeListView.as_view(), name='listaorcamentocomprahojeview'),

    # Pedidos de compra
    # compras/pedidocompra/adicionar/
    path('pedidocompra/adicionar/',
        views.AdicionarPedidoCompraView.as_view(), name='addpedidocompraview'),
    # compras/pedidocompra/listapedidocompra
    path('pedidocompra/listapedidocompra/',
        views.PedidoCompraListView.as_view(), name='listapedidocompraview'),
    # compras/pedidocompra/editar/
    path('pedidocompra/editar/<int:pk>/',
        views.EditarPedidoCompraView.as_view(), name='editarpedidocompraview'),
    # compras/pedidocompra/listapedidocompra/atrasados/
    path('pedidocompra/listapedidocompra/atrasados/',
        views.PedidoCompraAtrasadosListView.as_view(), name='listapedidocompraatrasadosview'),
    # compras/pedidocompra/listapedidocompra/hoje/
    path('pedidocompra/listapedidocompra/hoje/',
        views.PedidoCompraEntregaHojeListView.as_view(), name='listapedidocomprahojeview'),

    # Request ajax
    path('infocompra/', views.InfoCompra.as_view(), name='infocompra'),

    # Gerar pdf orcamento
    path('gerarpdforcamentocompra/<int:pk>/',
        views.GerarPDFOrcamentoCompra.as_view(), name='gerarpdforcamentocompra'),
    # Gerar pdf pedido
    path('gerarpdfpedidocompra/<int:pk>/',
        views.GerarPDFPedidoCompra.as_view(), name='gerarpdfpedidocompra'),
    # Gerar pedido a partir de um orçamento
    path('gerarpedidocompra/<int:pk>/',
        views.GerarPedidoCompraView.as_view(), name='gerarpedidocompra'),
    # Copiar orcamento cancelado ou realizado
    path('copiarorcamentocompra/<int:pk>/',
        views.GerarCopiaOrcamentoCompraView.as_view(), name='copiarorcamentocompra'),
    # Copiar pedido cancelado ou realizado
    path('copiarpedidocompra/<int:pk>/',
        views.GerarCopiaPedidoCompraView.as_view(), name='copiarpedidocompra'),
    # Cancelar Pedido de compra
    path('cancelarpedidocompra/<int:pk>/',
        views.CancelarPedidoCompraView.as_view(), name='cancelarpedidocompra'),
    # Cancelar Orcamento de compra
    path('cancelarorcamentocompra/<int:pk>/',
        views.CancelarOrcamentoCompraView.as_view(), name='cancelarorcamentocompra'),
    # Receber Pedido de compra
    path('receberpedidocompra/<int:pk>/',
        views.ReceberPedidoCompraView.as_view(), name='receberpedidocompra'),
]
