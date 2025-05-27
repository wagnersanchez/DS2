# djangosige/urls.py (Arquivo principal de URLs do seu projeto)
# -*- coding: utf-8 -*-

from django.urls import path, include # re_path não foi usado, removido para limpeza
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    # Para cada 'include', adicionamos a tupla (urlconf_module, app_name) e o namespace.
    # Isso garante que a resolução de URLs com namespace (ex: {% url 'fiscal:minha_url' %}) funcione.
    path('', include(('djangosige.apps.base.urls', 'base'), namespace='base')),
    path('login/', include(('djangosige.apps.login.urls', 'login'), namespace='login')),
    path('cadastro/', include(('djangosige.apps.cadastro.urls', 'cadastro'), namespace='cadastro')),
    path('fiscal/', include(('djangosige.apps.fiscal.urls', 'fiscal'), namespace='fiscal')),
    path('vendas/', include(('djangosige.apps.vendas.urls', 'vendas'), namespace='vendas')),
    path('compras/', include(('djangosige.apps.compras.urls', 'compras'), namespace='compras')),
    path('financeiro/', include(('djangosige.apps.financeiro.urls', 'financeiro'), namespace='financeiro')),
    path('estoque/', include(('djangosige.apps.estoque.urls', 'estoque'), namespace='estoque')),
]

# Servir arquivos de media em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
