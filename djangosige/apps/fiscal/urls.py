# djangosige/apps/fiscal/urls.py
from django.urls import path
from .views.nota_fiscal import ( 
    NotaFiscalDetailView,
    NotaFiscalEmitirView,
    NotaFiscalConsultarStatusView, 
    NotaFiscalCancelarView,
    NotaFiscalBaixarXMLView, 
    ListaNotasFiscaisSaidaView, 
    ListaNotasFiscaisEntradaView,
    ConfiguracaoNotaFiscalView,
    ConsultarCadastroSefazView,
    InutilizarNotasFiscaisView,
    ConsultarNotaFiscalSefazView, 
    # Certifique-se de que a view ManifestacaoDestinatarioView existe e está importada abaixo
    # from .views.nota_fiscal import ManifestacaoDestinatarioView # DESCOMENTE E AJUSTE QUANDO A VIEW EXISTIR
)
# Se ManifestacaoDestinatarioView estiver em outro arquivo, importe de lá.
# Para o exemplo, vamos assumir que será criada em views/nota_fiscal.py
# Se você já a criou, apenas garanta que a importação acima está correta.
# Se não, você precisará criar esta view.

# Placeholder para a view, substitua pela importação real quando a view for criada
from django.views.generic import TemplateView # Apenas para o placeholder funcionar
class ManifestacaoDestinatarioView(TemplateView): # CRIE ESTA VIEW CORRETAMENTE
    template_name = "base/pagina_em_construcao.html" # Exemplo de template

from .views.natureza_operacao import (
    NaturezaOperacaoListView,
    AdicionarNaturezaOperacaoView,
    EditarNaturezaOperacaoView,
)
from .views.tributos import (
    GrupoFiscalListView, 
    AdicionarGrupoFiscalView, 
    EditarGrupoFiscalView
)

app_name = 'fiscal' 

urlpatterns = [
    # URLs para NotaFiscal
    path('notafiscal/saida/lista/', ListaNotasFiscaisSaidaView.as_view(), name='listanotafiscalsaidaview'),
    path('notafiscal/entrada/lista/', ListaNotasFiscaisEntradaView.as_view(), name='listanotafiscalentradaview'),
    
    path('configuracao/nfe/', ConfiguracaoNotaFiscalView.as_view(), name='configuracaonotafiscal'),
    path('nota-fiscal/<int:pk>/', NotaFiscalDetailView.as_view(), name='nota_fiscal_detail'),
    path('nota-fiscal/<int:pk>/emitir/', NotaFiscalEmitirView.as_view(), name='nota_fiscal_emitir'),
    path('nota-fiscal/<int:pk>/consultar-status/', NotaFiscalConsultarStatusView.as_view(), name='nota_fiscal_consultar_status'),
    path('nota-fiscal/<int:pk>/cancelar/', NotaFiscalCancelarView.as_view(), name='nota_fiscal_cancelar'),
    path('nota-fiscal/<int:pk>/baixar-xml/', NotaFiscalBaixarXMLView.as_view(), name='baixarnota'), 
    
    # URLs para Natureza da Operação
    path('naturezaoperacao/lista/', NaturezaOperacaoListView.as_view(), name='listanaturezaoperacaoview'),
    path('naturezaoperacao/adicionar/', AdicionarNaturezaOperacaoView.as_view(), name='addnaturezaoperacaoview'),
    path('naturezaoperacao/editar/<int:pk>/', EditarNaturezaOperacaoView.as_view(), name='editarnaturezaoperacaoview'),
    
    # URLs para Grupo Fiscal
    path('grupofiscal/lista/', GrupoFiscalListView.as_view(), name='listagrupofiscalview'),
    path('grupofiscal/adicionar/', AdicionarGrupoFiscalView.as_view(), name='addgrupofiscalview'),
    path('grupofiscal/editar/<int:pk>/', EditarGrupoFiscalView.as_view(), name='editargrupofiscalview'),

    # URLs de Serviços SEFAZ
    path('sefaz/consultar-cadastro/', ConsultarCadastroSefazView.as_view(), name='consultarcadastro'),
    path('sefaz/inutilizar-notas/', InutilizarNotasFiscaisView.as_view(), name='inutilizarnotas'),
    path('sefaz/consultar-nota/', ConsultarNotaFiscalSefazView.as_view(), name='consultarnota'), 
    path('sefaz/consultar-nota/<int:pk>/', ConsultarNotaFiscalSefazView.as_view(), name='consultarnotapk'), 
    # URL para Manifestação do Destinatário (ATIVA)
    path('sefaz/manifestacao-destinatario/', ManifestacaoDestinatarioView.as_view(), name='manifestacaodestinatario'),
]
