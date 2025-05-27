# -*- coding: utf-8 -*-

from django.urls import path, include, re_path
from . import views

app_name = 'cadastro'
urlpatterns = [
    # Empresa
    # cadastro/empresa/adicionar/
    path('empresa/adicionar/',
        views.AdicionarEmpresaView.as_view(), name='addempresaview'),
    # cadastro/empresa/listaempresas
    path('empresa/listaempresas/',
        views.EmpresasListView.as_view(), name='listaempresasview'),
    # cadastro/empresa/editar/
    path('empresa/editar/<int:pk>/',
        views.EditarEmpresaView.as_view(), name='editarempresaview'),

    # Cliente
    # cadastro/cliente/adicionar/
    path('cliente/adicionar/',
        views.AdicionarClienteView.as_view(), name='addclienteview'),
    # cadastro/cliente/listaclientes
    path('cliente/listaclientes/',
        views.ClientesListView.as_view(), name='listaclientesview'),
    # cadastro/cliente/editar/
    path('cliente/editar/<int:pk>/',
        views.EditarClienteView.as_view(), name='editarclienteview'),

    # Fornecedor
    # cadastro/fornecedor/adicionar/
    path('fornecedor/adicionar/',
        views.AdicionarFornecedorView.as_view(), name='addfornecedorview'),
    # cadastro/fornecedor/listafornecedores
    path('fornecedor/listafornecedores/',
        views.FornecedoresListView.as_view(), name='listafornecedoresview'),
    # cadastro/fornecedor/editar/
    path('fornecedor/editar/<int:pk>/',
        views.EditarFornecedorView.as_view(), name='editarfornecedorview'),

    # Transportadora
    # cadastro/transportadora/adicionar/
    path('transportadora/adicionar/',
        views.AdicionarTransportadoraView.as_view(), name='addtransportadoraview'),
    # cadastro/transportadora/listatransportadoras
    path('transportadora/listatransportadoras/',
        views.TransportadorasListView.as_view(), name='listatransportadorasview'),
    # cadastro/transportadora/editar/
    path('transportadora/editar/<int:pk>/',
        views.EditarTransportadoraView.as_view(), name='editartransportadoraview'),

    # Produto
    # cadastro/produto/adicionar/
    path('produto/adicionar/',
        views.AdicionarProdutoView.as_view(), name='addprodutoview'),
    # cadastro/produto/listaprodutos
    path('produto/listaprodutos/',
        views.ProdutosListView.as_view(), name='listaprodutosview'),
    # cadastro/produto/listaprodutos/baixoestoque
    path('produto/listaprodutos/baixoestoque/',
        views.ProdutosBaixoEstoqueListView.as_view(), name='listaprodutosbaixoestoqueview'),
    # cadastro/produto/editar/
    path('produto/editar/<int:pk>/',
        views.EditarProdutoView.as_view(), name='editarprodutoview'),

    # Outros
    # Categorias
    # cadastro/outros/adicionarcategoria/
    path('outros/adicionarcategoria/',
        views.AdicionarCategoriaView.as_view(), name='addcategoriaview'),
    # cadastro/outros/listacategorias/
    path('outros/listacategorias/',
        views.CategoriasListView.as_view(), name='listacategoriasview'),
    # cadastro/outros/editarcategoria/
    path('outros/editarcategoria/<int:pk>/',
        views.EditarCategoriaView.as_view(), name='editarcategoriaview'),

    # Unidades
    # cadastro/outros/adicionarunidade/
    path('outros/adicionarunidade/',
        views.AdicionarUnidadeView.as_view(), name='addunidadeview'),
    # cadastro/outros/listaunidades/
    path('outros/listaunidades/',
        views.UnidadesListView.as_view(), name='listaunidadesview'),
    # cadastro/outros/editarcunidade/
    path('outros/editarunidade/<int:pk>/',
        views.EditarUnidadeView.as_view(), name='editarunidadeview'),

    # Marcas
    # cadastro/outros/adicionarmarca/
    path('outros/adicionarmarca/',
        views.AdicionarMarcaView.as_view(), name='addmarcaview'),
    # cadastro/outros/listamarcas/
    path('outros/listamarcas/',
        views.MarcasListView.as_view(), name='listamarcasview'),
    # cadastro/outros/editarmarca/
    path('outros/editarmarca/<int:pk>/',
        views.EditarMarcaView.as_view(), name='editarmarcaview'),

    # Informacoes de dada empresa (Ajax request)
    path('infoempresa/', views.InfoEmpresa.as_view(), name='infoempresa'),
    path('infofornecedor/', views.InfoFornecedor.as_view(), name='infofornecedor'),
    path('infocliente/', views.InfoCliente.as_view(), name='infocliente'),
    path('infotransportadora/', views.InfoTransportadora.as_view(),
        name='infotransportadora'),
    path('infoproduto/', views.InfoProduto.as_view(), name='infoproduto'),
]
