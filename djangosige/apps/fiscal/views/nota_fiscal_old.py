# djangosige/apps/fiscal/views/nota_fiscal.py
# Código completo revisado e com placeholders para funcionalidades futuras

# -*- coding: utf-8 -*-

# Imports Django e Python
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render # Adicionado render
from django.http import HttpResponse, JsonResponse
from django.views.generic import CreateView, UpdateView, ListView, View, TemplateView, DeleteView
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin # Para mensagens de sucesso
import traceback
from decimal import Decimal, InvalidOperation
from datetime import datetime
import tempfile
import os
import operator
from functools import reduce
import logging
import locale # Importar locale

# Imports de Base e Custom Views (VERIFICAR CAMINHOS)
from djangosige.apps.base.custom_views import CustomView, CustomCreateView, CustomListView, CustomUpdateView, CustomTemplateView
from djangosige.apps.base.views_mixins import FormValidationMessageMixin

# Imports de Forms Fiscais (VERIFICAR CAMINHOS)
from djangosige.apps.fiscal.forms import (
    NotaFiscalSaidaForm, NotaFiscalEntradaForm, AutXMLFormSet,
    ConfiguracaoNotaFiscalForm, EmissaoNotaFiscalForm, CancelamentoNotaFiscalForm,
    ConsultarCadastroForm, InutilizarNotasForm, ConsultarNotaForm, BaixarNotaForm,
    ManifestacaoDestinatarioForm
)
# Imports de Modelos Fiscais (VERIFICAR CAMINHOS E NOMES)
from djangosige.apps.fiscal.models import (
    NotaFiscalSaida, NotaFiscalEntrada, NotaFiscal, ConfiguracaoNotaFiscal,
    AutXML, ErrosValidacaoNotaFiscal, RespostaSefazNotaFiscal,
   
)
# Imports de Modelos Cadastro (VERIFICAR CAMINHOS)
from djangosige.apps.cadastro.models import MinhaEmpresa, Empresa, Cliente, Fornecedor, Produto, Pessoa, PessoaJuridica, PessoaFisica, Transportadora, Veiculo # Adicionar os necessários
# Imports de Modelos Login (VERIFICAR CAMINHOS)
from djangosige.apps.login.models import Usuario as UsuarioProfile

# Imports de Modelos Vendas/Compras (se necessário)
from djangosige.apps.vendas.models import PedidoVenda, ItensVenda

# Import do Processador (VERIFICAR CAMINHO)
try:
    # Tentar caminhos relativos e absolutos
    try: from .processador_nf import ProcessadorNotaFiscal
    except ImportError: from ..processador_nf import ProcessadorNotaFiscal
except ImportError:
    try: from djangosige.apps.fiscal.processador_nf import ProcessadorNotaFiscal
    except ImportError: ProcessadorNotaFiscal = None; print("ERRO CRÍTICO: Classe ProcessadorNotaFiscal não encontrada.")

logger = logging.getLogger(__name__)

# Configura locale (idealmente no settings.py ou wsgi.py)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try: locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error: print("AVISO: Locale 'pt_BR' não definido."); locale = None

class BaseNotaFiscalView(View): # Ou herdar de CustomView
    """
    Classe base para views de Nota Fiscal.
    (Adicione aqui métodos ou atributos comuns se necessário no futuro)
    """
    pass # Pode começar vazia se a lógica estiver nas filhas

# --- Mixin (Baseado no código original fornecido) ---
class NotaFiscalViewMixin(object):
    def atualizar_campos(self, post_data):
        values_dict = {}; itens_id = []
        decimal_fields = ['vq_bcpis', 'vq_bccofins', 'vpis', 'vcofins', 'vicms_deson', ] # VERIFICAR CAMPOS
        string_fields = ['inf_ad_prod', ] # VERIFICAR CAMPO
        for key, value in post_data.items():
            if key == 'pk_item': itens_id.append(value)
            elif key.startswith('editable_field_'): values_dict[key] = value
        for item_id in itens_id:
            try:
                # VERIFICAR MODELO DE ITEM AQUI (ItensVenda? ItemNotaFiscal?)
                item = ItensVenda.objects.get(pk=item_id)
                for key, value in values_dict.items():
                    if value:
                        for dfield in decimal_fields:
                            field_key = f"editable_field_{dfield}_{item_id}"
                            if key == field_key:
                                try: cleaned_value = re.sub(r'[^\d,-]', '', value).replace('.', '').replace(',', '.'); setattr(item, dfield, Decimal(cleaned_value))
                                except (AttributeError, InvalidOperation, ValueError): print(f"AVISO: Falha ao atualizar campo decimal {dfield} para item {item_id}")
                        for sfield in string_fields:
                            field_key = f"editable_field_{sfield}_{item_id}"
                            if key == field_key:
                                try: setattr(item, sfield, value)
                                except AttributeError: print(f"AVISO: Falha ao atualizar campo string {sfield} para item {item_id}")
                item.save()
            except ObjectDoesNotExist: print(f"Item {item_id} não encontrado para atualizar.") # Usar ObjectDoesNotExist
            except Exception as e: print(f"Erro inesperado ao atualizar campo do item {item_id}: {e}")


# --- Views Base CRUD (Baseadas no código original) ---
class AdicionarNotaFiscalView(CustomCreateView, NotaFiscalViewMixin):
    # Classe base para Adicionar NF (Saída/Entrada)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'aut_form' not in context: context['aut_form'] = AutXMLFormSet(prefix='aut_form')
        return self.view_context(context)

    def get_success_message(self, cleaned_data):
        if isinstance(self.object, NotaFiscalSaida): n_nf = getattr(self.object, 'n_nf_saida', self.object.pk)
        elif isinstance(self.object, NotaFiscalEntrada): n_nf = getattr(self.object, 'n_nf_entrada', self.object.pk)
        else: n_nf = self.object.pk
        return self.success_message % dict(cleaned_data, n_nf=n_nf) # Usar success_message da subclasse

    def get(self, request, *args, **kwargs):
        self.object = None; form_class = self.get_form_class()
        form = self.get_form(form_class)
        if hasattr(self, 'set_form_initial_data'): form = self.set_form_initial_data(form, request.user)
        aut_form = AutXMLFormSet(prefix='aut_form')
        return self.render_to_response(self.get_context_data(form=form, aut_form=aut_form))

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = None; form_class = self.get_form_class()
        req_post = request.POST.copy()
        for key in req_post:
            if 'v_' in key and isinstance(req_post[key], str): req_post[key] = req_post[key].replace('.', '')
        form = form_class(req_post, request.FILES or None)
        aut_form = AutXMLFormSet(req_post, prefix='aut_form')
        if form.is_valid() and aut_form.is_valid():
            try:
                self.object = form.save(commit=False); self.object.save()
                aut_form.instance = self.object; aut_form.save()
                if isinstance(self.object, NotaFiscalSaida) and hasattr(self, 'atualizar_campos'): self.atualizar_campos(req_post)
                return self.form_valid(form) # Chama form_valid do CreateView (redirect e msg)
            except Exception as e: messages.error(request, f"Erro ao salvar dados: {e}"); return self.form_invalid(form, aut_form)
        else: return self.form_invalid(form, aut_form)

    def form_invalid(self, form, aut_form): # Aceitar aut_form
        messages.error(self.request, "Erro ao salvar nota fiscal. Verifique os dados.")
        return self.render_to_response(self.get_context_data(form=form, aut_form=aut_form))

class NotaFiscalListView(CustomListView, NotaFiscalViewMixin):
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); return self.view_context(context)
    def view_context(self, context): raise NotImplementedError

class EditarNotaFiscalView(CustomUpdateView, NotaFiscalViewMixin):
    template_name = "fiscal/nota_fiscal/nota_fiscal_edit.html" # Template genérico
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['edit_nfe'] = True
        if 'aut_form' not in context and isinstance(self.object, NotaFiscalSaida):
             context['aut_form'] = AutXMLFormSet(prefix='aut_form', instance=self.object)
             if AutXML.objects.filter(nfe=self.object.pk).exists(): context['aut_form'].extra = 0
        context['errors_validacao'] = ErrosValidacaoNotaFiscal.objects.filter(nfe=self.object)
        context['resposta_sefaz'] = RespostaSefazNotaFiscal.objects.filter(nfe=self.object)
        return self.view_context(context)

    def get_success_message(self, cleaned_data):
        if isinstance(self.object, NotaFiscalSaida): n_nf = getattr(self.object, 'n_nf_saida', self.object.pk)
        elif isinstance(self.object, NotaFiscalEntrada): n_nf = getattr(self.object, 'n_nf_entrada', self.object.pk)
        else: n_nf = self.object.pk
        return self.success_message % dict(cleaned_data, n_nf=n_nf) # Usa success_message da subclasse

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        req_post = request.POST.copy() # Copiar para não alterar original
        for key in req_post:
            if ('v_orig' in key or 'v_desc' in key or 'v_liq' in key) and isinstance(req_post[key], str): # Ajustar chaves
                 req_post[key] = req_post[key].replace('.', '')
        form = self.get_form_class()(req_post, request.FILES or None, instance=self.object) # Usar req_post tratado
        aut_form = None; aut_form_is_valid = True # Default
        if isinstance(self.object, NotaFiscalSaida):
            aut_form = AutXMLFormSet(req_post, prefix='aut_form', instance=self.object)
            aut_form_is_valid = aut_form.is_valid()

        if form.is_valid() and aut_form_is_valid:
            try:
                self.object = form.save(commit=False)
                self.object.status_nfe = '0' # Volta para 'Em Digitação'? VERIFICAR CONSTANTE
                self.object.save()
                if aut_form: aut_form.save()
                if isinstance(self.object, NotaFiscalSaida) and hasattr(self, 'atualizar_campos'): self.atualizar_campos(req_post)
                return self.form_valid(form) # Chama form_valid do UpdateView
            except Exception as e: messages.error(request, f"Erro ao salvar alterações: {e}"); return self.form_invalid(form, aut_form)
        else: return self.form_invalid(form, aut_form)

    def form_invalid(self, form, aut_form=None): # Aceitar aut_form opcional
        messages.error(self.request, "Erro ao salvar. Verifique os dados.")
        context_kwargs = {'form': form}
        if aut_form: context_kwargs['aut_form'] = aut_form
        return self.render_to_response(self.get_context_data(**context_kwargs))


# --- Views Específicas (Saída) ---

class AdicionarNotaFiscalSaidaView(AdicionarNotaFiscalView):
    form_class = NotaFiscalSaidaForm
    template_name = "fiscal/nota_fiscal/nota_fiscal_add.html" # Verificar path
    success_url = reverse_lazy('fiscal:listanotafiscalsaidaview')
    success_message = "Nota fiscal N°<b>%(n_nf)s </b>criada com sucesso."
    permission_codename = 'add_notafiscalsaida'
    def view_context(self, context):
        context['title_complete'] = 'GERAR NOTA FISCAL DE SAÍDA'; context['return_url'] = self.success_url; context['saida'] = True
        return context
    def set_form_initial_data(self, form, user):
        form.initial['dhemi'] = timezone.now()
        try: user_profile = UsuarioProfile.objects.get(user=user); minha_empresa_obj = MinhaEmpresa.objects.select_related('m_empresa').get(m_usuario=user_profile); form.initial['emit_saida'] = minha_empresa_obj.m_empresa
        except (UsuarioProfile.DoesNotExist, MinhaEmpresa.DoesNotExist): messages.warning(self.request, "Configure 'Minha Empresa'.")
        except Exception as e: print(f"Erro initial emit_saida: {e}")
        try: conf_nfe = ConfiguracaoNotaFiscal.objects.first(); form.initial.update({'serie': conf_nfe.serie_atual, 'tp_amb': conf_nfe.ambiente, 'tp_imp': conf_nfe.imp_danfe})
        except Exception as e: print(f"Erro initial conf_nfe: {e}")
        form.initial['status_nfe'] = '0' # Usar constante
        try: ultima_nfe = NotaFiscalSaida.objects.filter(serie=form.initial.get('serie')).latest('n_nf_saida'); form.initial['n_nf_saida'] = int(ultima_nfe.n_nf_saida) + 1
        except NotaFiscalSaida.DoesNotExist: form.initial['n_nf_saida'] = 1
        except (ValueError, TypeError): form.initial['n_nf_saida'] = NotaFiscalSaida.objects.count() + 1 # Fallback
        return form

class NotaFiscalSaidaListView(NotaFiscalListView):
    template_name = 'fiscal/nota_fiscal/nota_fiscal_list.html'; model = NotaFiscalSaida; context_object_name = 'all_notas'; permission_codename = 'view_notafiscalsaida'
    def view_context(self, context):
        context['title_complete'] = 'NOTAS FISCAIS DE SAÍDA'; context['add_url'] = reverse_lazy('fiscal:addnotafiscalsaidaview'); context['importar_nota_url'] = reverse_lazy('fiscal:importar_xml'); context['saida'] = True; context['entrada'] = False
        return context
    def get_queryset(self): return NotaFiscalSaida.objects.select_related('emit_saida', 'dest_saida').order_by('-id')

class EditarNotaFiscalSaidaView(EditarNotaFiscalView):
    form_class = NotaFiscalSaidaForm; model = NotaFiscalSaida; success_url = reverse_lazy('fiscal:listanotafiscalsaidaview')
    success_message = "Nota fiscal N°<b>%(n_nf)s </b>editada com sucesso."; permission_codename = 'change_notafiscalsaida'
    def view_context(self, context):
        n_nf = getattr(self.object, 'n_nf_saida', self.object.pk); serie = getattr(self.object, 'serie', '-')
        context['title_complete'] = f'EDITAR NF-e SAÍDA {serie}/{n_nf}'; context['return_url'] = self.success_url; context['saida'] = True; context['entrada'] = False
        return context

class GerarNotaFiscalSaidaView(CustomView): # Gerar a partir do PedidoVenda
    permission_codename = ['add_notafiscalsaida', 'change_notafiscalsaida', 'view_pedidovenda']
    def get(self, request, *args, **kwargs):
        pedido_id = kwargs.get('pk', None); pedido = get_object_or_404(PedidoVenda, id=pedido_id)
        if NotaFiscalSaida.objects.filter(venda=pedido).exists():
             messages.warning(request, f"Já existe NF para o Pedido {pedido_id}."); existing_note = NotaFiscalSaida.objects.filter(venda=pedido).first()
             return redirect(reverse_lazy('fiscal:editarnotafiscalsaidaview', kwargs={'pk': existing_note.pk}))
        nova_nota = NotaFiscalSaida(); nova_nota.tpnf = '1'
        try: user_profile = UsuarioProfile.objects.get(user=request.user); minha_empresa_obj = MinhaEmpresa.objects.select_related('m_empresa').get(m_usuario=user_profile); nova_nota.emit_saida = minha_empresa_obj.m_empresa
        except Exception as e: messages.error(request, f"Erro emitente: {e}"); return redirect(pedido.get_absolute_url()) # Assumindo get_absolute_url
        try: conf_nfe = ConfiguracaoNotaFiscal.objects.first(); assert conf_nfe; nova_nota.serie = conf_nfe.serie_atual; nova_nota.tp_amb = conf_nfe.ambiente; nova_nota.tp_imp = conf_nfe.imp_danfe
        except (ConfiguracaoNotaFiscal.DoesNotExist, AssertionError): messages.error(request, "Config NF-e não encontrada."); return redirect(pedido.get_absolute_url())
        nova_nota.status_nfe = '0'; nova_nota.dhemi = timezone.now()
        nova_nota.dest_saida = pedido.cliente; nova_nota.venda = pedido # VERIFICAR CAMPOS
        nova_nota.fin_nfe = '1'; nova_nota.ind_final = '1' if pedido.ind_final else '0'; nova_nota.ind_pres = '1'
        if pedido.cond_pagamento: nova_nota.indpag = '1' if pedido.cond_pagamento.n_parcelas > 1 else '0'
        else: nova_nota.indpag = '2'
        nova_nota.mod = '65' if nova_nota.ind_final == '1' else '55'
        try: ultima_nfe = NotaFiscalSaida.objects.filter(serie=nova_nota.serie).latest('n_nf_saida'); nova_nota.n_nf_saida = int(ultima_nfe.n_nf_saida) + 1
        except: nova_nota.n_nf_saida = 1
        nova_nota.valor_total = pedido.valor_total # VERIFICAR CAMPO
        # --- Mapear outros totais do pedido para a nota ---
        try:
             nova_nota.full_clean(); nova_nota.save()
             # --- Opcional: Copiar itens/pagamentos do pedido para a nota ---
             messages.success(request, f"Nota Fiscal {nova_nota.n_nf_saida} pré-gerada a partir do pedido {pedido_id}.")
             return redirect(reverse_lazy('fiscal:editarnotafiscalsaidaview', kwargs={'pk': nova_nota.pk}))
        except Exception as e: messages.error(request, f"Erro ao gerar nota: {e}"); return redirect(reverse_lazy('vendas:editarpedidovendaview', kwargs={'pk': pedido_id}))


# --- Views Específicas (Entrada) ---

class AdicionarNotaFiscalEntradaView(AdicionarNotaFiscalView): # Herda da base Adicionar
    form_class = NotaFiscalEntradaForm
    template_name = "fiscal/nota_fiscal/nota_fiscal_add.html" # Usar mesmo template add?
    success_url = reverse_lazy('fiscal:listanotafiscalentradaview')
    success_message = "Nota fiscal de entrada N°<b>%(n_nf)s </b>criada com sucesso." # Usar % format
    permission_codename = 'add_notafiscalentrada'
    def view_context(self, context):
         context['title_complete'] = 'ADICIONAR NOTA FISCAL DE ENTRADA MANUALMENTE'; context['return_url'] = self.success_url; context['entrada'] = True; context['saida'] = False
         return context
    def set_form_initial_data(self, form, user):
        form.initial['dhemi'] = timezone.now()
        try: user_profile = UsuarioProfile.objects.get(user=user); minha_empresa_obj = MinhaEmpresa.objects.select_related('m_empresa').get(m_usuario=user_profile); form.initial['dest_entrada'] = minha_empresa_obj.m_empresa # VERIFICAR CAMPO
        except Exception as e: messages.warning(self.request, f"Configure 'Minha Empresa': {e}")
        form.initial['status_nfe'] = '9' # Importada/Digitada? VERIFICAR CONSTANTE
        return form

class NotaFiscalEntradaListView(NotaFiscalListView):
    template_name = 'fiscal/nota_fiscal/nota_fiscal_list.html'; model = NotaFiscalEntrada; context_object_name = 'all_notas'; permission_codename = 'view_notafiscalentrada'
    def view_context(self, context):
        context['title_complete'] = 'NOTAS FISCAIS DE ENTRADA'; context['add_url'] = reverse_lazy('fiscal:addnotafiscalentradaview'); context['importar_nota_url'] = reverse_lazy('fiscal:importar_xml'); context['saida'] = False; context['entrada'] = True
        return context
    def get_queryset(self): return NotaFiscalEntrada.objects.select_related('emit_entrada', 'dest_entrada').order_by('-id')

class EditarNotaFiscalEntradaView(EditarNotaFiscalView): # Herda da base Editar
    form_class = NotaFiscalEntradaForm; model = NotaFiscalEntrada
    success_url = reverse_lazy('fiscal:listanotafiscalentradaview')
    success_message = "Nota fiscal de entrada N°<b>%(n_nf)s </b>editada com sucesso." # Usar % format
    permission_codename = 'change_notafiscalentrada'
    def view_context(self, context):
        n_nf = getattr(self.object, 'n_nf_entrada', self.object.pk); serie = getattr(self.object, 'serie', '-')
        context['title_complete'] = f'EDITAR NF-e ENTRADA {serie}/{n_nf}'; context['return_url'] = self.success_url; context['entrada'] = True; context['saida'] = False
        if 'aut_form' in context: del context['aut_form'] # Não tem AutXML em nota de entrada
        return context
    # POST herdado da base é suficiente se não precisar de AutXMLFormSet


# --- View de Importação (Atualizada com Debug) ---
class ImportarNotaView(CustomView):
    # (Código desta classe como fornecido na resposta #63, com debug de CNPJ)
    def post(self, request, *args, **kwargs):
        if not ProcessadorNotaFiscal: messages.error(request, "Proc NF não conf."); return redirect(reverse_lazy('base:index')) # Simplificado
        if request.FILES.get('arquivo_xml'):
            processador_nota = ProcessadorNotaFiscal(); processador_nota.importar_xml(request)
            if processador_nota.erro:
                specific_error_msg = "CNPJ do destinatário no XML não confere com a 'Minha Empresa'."
                if processador_nota.message and specific_error_msg in processador_nota.message:
                    print("*" * 20); print("*** DEBUG DA VIEW: Erro de comparação de CNPJ detectado.")
                    xml_cnpj = getattr(processador_nota, 'last_dest_cnpj_xml', 'N/A'); db_cnpj = getattr(processador_nota, 'last_my_comp_cnpj_db', 'N/A')
                    print(f"*** DEBUG DA VIEW: CNPJ XML (guardado): '{xml_cnpj}' (Tipo: {type(xml_cnpj)})")
                    print(f"*** DEBUG DA VIEW: CNPJ DB (guardado): '{db_cnpj}' (Tipo: {type(db_cnpj)})"); print("*" * 20)
                messages.error(request, processador_nota.message)
            else:
                 if processador_nota.message: messages.success(request, processador_nota.message)
                 else: messages.info(request, "Importação finalizada.")
        else: messages.error(request, 'Nenhum arquivo XML selecionado.')
        # Redirecionar para uma URL genérica ou a lista de notas de entrada?
        return redirect(request.META.get('HTTP_REFERER', reverse_lazy('fiscal:listanotafiscalentradaview'))) # Tenta voltar ou vai pra lista

class ImportarNotaSaidaView(ImportarNotaView):
    permission_codename = ['add_notafiscalsaida','view_notafiscalsaida', 'change_notafiscalsaida']
    def get_redirect_url(self): return redirect(reverse_lazy('fiscal:listanotafiscalsaidaview'))

class ImportarNotaEntradaView(ImportarNotaView):
    permission_codename = ['add_notafiscalentrada','view_notafiscalentrada', 'change_notafiscalentrada']
    def get_redirect_url(self): return redirect(reverse_lazy('fiscal:listanotafiscalentradaview'))


# --- Views de Ações (Emitir, Cancelar, Consultar, DANFE - Usando Processador Refatorado) ---
class EmitirNotaFiscalView(View): # Adicionar Mixins de Permissão/Login se necessário
    # permission_required = 'fiscal.emitir_notafiscal' # Exemplo

    @transaction.atomic
    def post(self, request, *args, **kwargs): # Receber pk pela URL
        nota_id = kwargs.get('pk')
        nota = get_object_or_404(NotaFiscalSaida, pk=nota_id)

        # Verificar se Processador foi carregado
        if not ProcessadorNotaFiscal:
            messages.error(request, "Erro crítico: Processador de NF não carregado.")
            return JsonResponse({'status': 'error','errors': ['Processador NF não carregado']}, status=500)

        processador = ProcessadorNotaFiscal()

        # Verificar permissão (exemplo)
        # if not request.user.has_perm(self.permission_required):
        #     messages.error(request, "Sem permissão para emitir NF-e.")
        #     return JsonResponse({'status': 'error','errors': ['Sem permissão']}, status=403)

        # Chama o método refatorado que usa PyNFe
        if processador.emitir_nfe(nota):
            msg_sucesso = processador.message or f'NF-e {nota.numero}/{nota.serie} enviada e/ou autorizada!'
            messages.success(request, msg_sucesso)
            return JsonResponse({
                'status': 'success',
                'message': msg_sucesso,
                'chave': getattr(nota, 'chave', None),
                'protocolo': getattr(nota, 'protocolo', None)
            })
        else:
            msg_erro = processador.message or f'Erro desconhecido ao emitir NF-e {nota.numero}/{nota.serie}.'
            messages.error(request, msg_erro)
            return JsonResponse({'status': 'error', 'errors': processador.erros or [msg_erro]}, status=400)

    def get(self, request, *args, **kwargs):
        # Emissão normalmente só deve ocorrer via POST
        messages.warning(request, "A emissão de NF-e deve ser feita via POST.")
        nota_id = kwargs.get('pk')
        # Redirecionar para a página de detalhes ou edição
        return redirect('fiscal:editarnotafiscalsaidaview', pk=nota_id) # Ou detail view

class CancelarNotaFiscalView(View): # Adicionar Mixins
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        nota_id = kwargs.get('pk'); justificativa = request.POST.get('justificativa', '').strip()
        if len(justificativa) < 15: messages.error(request, 'Justif. curta'); return JsonResponse({'status': 'error','errors': ['Justificativa curta']}, status=400)
        nota = get_object_or_404(NotaFiscalSaida, pk=nota_id)
        if not ProcessadorNotaFiscal: return JsonResponse({'status': 'error','errors': ['Proc NF não conf.']}, status=500)
        processador = ProcessadorNotaFiscal()
        if processador.cancelar_nfe(nota, justificativa): msg = processador.message or 'NF-e cancelada.'; messages.success(request, msg); return JsonResponse({'status': 'success', 'message': msg})
        else: msg = processador.message or 'Erro desconhecido no cancelamento.'; messages.error(request, msg); return JsonResponse({'status': 'error', 'errors': processador.erros or [msg]}, status=400)
    def get(self, request, *args, **kwargs): return redirect('fiscal:editarnotafiscalsaidaview', pk=kwargs.get('pk'))

class ConsultarNotaFiscalView(View): # Adicionar Mixins
    def get(self, request, *args, **kwargs):
        nota_id = kwargs.get('pk'); tipo_nota = kwargs.get('tipo', 'saida')
        model = NotaFiscalSaida if tipo_nota == 'saida' else NotaFiscalEntrada
        nota = get_object_or_404(model, pk=nota_id)
        if not ProcessadorNotaFiscal: return JsonResponse({'status': 'erro', 'mensagem': 'Proc NF não conf.'}, status=500)
        processador = ProcessadorNotaFiscal()
        resultado = processador.consultar_nota(nota.chave)
        if resultado.get('status') != 'erro':
            status_sefaz = resultado.get('status_geral'); updated = False
            # Implementar lógica de atualização de status local se necessário
            if updated: nota.save(); messages.info(request, f"Status local atualizado para: {nota.get_status_nfe_display()}.")
        # Adicionar mensagem para feedback ao usuário
        if resultado.get('status') == 'erro': messages.error(request, f"Consulta SEFAZ: {resultado.get('mensagem', 'Erro')}")
        else: messages.success(request, f"Consulta SEFAZ: {resultado.get('motivo_sefaz', 'OK')} ({resultado.get('status_sefaz', 'OK')})")
        return JsonResponse(resultado) # Retorna JSON para AJAX

class GerarDanfeView(View): # Adicionar Mixins
    def get(self, request, *args, **kwargs):
        nota_id = kwargs.get('pk')
        nota = get_object_or_404(NotaFiscalSaida, pk=nota_id)
        if not ProcessadorNotaFiscal: messages.error(request, "Proc NF não conf."); return redirect('fiscal:editarnotafiscalsaidaview', pk=nota.pk)
        processador = ProcessadorNotaFiscal()
        danfe_pdf_bytes = processador.gerar_danfe(nota)
        if danfe_pdf_bytes:
            response = HttpResponse(danfe_pdf_bytes, content_type='application/pdf')
            filename = f'DANFE_{nota.n_nf_saida or nota.pk}_{nota.serie or ""}.pdf'; response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        else: messages.error(request, f'Erro ao gerar DANFE: {processador.message}'); return redirect('fiscal:editarnotafiscalsaidaview', pk=nota.pk)


# --- Outras Views Fiscais (Placeholders/Originais - Precisam de Revisão/Implementação com PyNFe) ---
# Estas views chamam métodos em ProcessadorNotaFiscal que foram removidos/comentados
# pois dependiam de pysignfe. Precisam ser reimplementadas se a funcionalidade for necessária.

class ConfiguracaoNotaFiscalView(SuccessMessageMixin, CustomUpdateView): # Usando UpdateView
    model = ConfiguracaoNotaFiscal; form_class = ConfiguracaoNotaFiscalForm
    template_name = 'fiscal/nota_fiscal/nota_fiscal_config.html'
    success_url = reverse_lazy('fiscal:configuracaonotafiscal')
    success_message = "Configuração de NF-e salva com sucesso."
    permission_codename = 'configurar_nfe'
    def get_object(self, queryset=None): obj, created = ConfiguracaoNotaFiscal.objects.get_or_create(pk=1); return obj
    def get_context_data(self, **kwargs): context = super().get_context_data(**kwargs); context['title_complete'] = 'CONFIGURAÇÃO DE EMISSÃO NF-e'; return context

class ValidarNotaView(CustomView):
    permission_codename = 'change_notafiscalsaida'
    def get(self, request, *args, **kwargs):
        messages.warning(request, "Funcionalidade 'Validar Nota' (offline) não implementada com PyNFe.")
        return redirect(request.META.get('HTTP_REFERER', reverse_lazy('fiscal:listanotafiscalsaidaview')))

class GerarCopiaNotaView(CustomView):
    permission_codename = ['add_notafiscalsaida', 'change_notafiscalsaida']
    def get(self, request, *args, **kwargs): messages.warning(request, "Funcionalidade 'Gerar Cópia NF' não revisada."); return redirect(request.META.get('HTTP_REFERER', '/')) # Implementar cópia

class GerarDanfceView(CustomView):
    permission_codename = ['view_notafiscalsaida', 'change_notafiscalsaida', 'gerar_danfe']
    def get(self, request, *args, **kwargs): messages.warning(request, "Geração de DANFCE não implementada com PyNFe nesta versão."); return redirect(request.META.get('HTTP_REFERER', '/'))

class ConsultarCadastroView(CustomTemplateView):
    template_name = 'fiscal/nota_fiscal/nota_fiscal_sefaz.html'; permission_codename = ['view_notafiscalsaida', 'consultar_cadastro']
    form_class = ConsultarCadastroForm # Necessita form
    def post(self, request, *args, **kwargs): messages.warning(request, "Consulta de Cadastro SEFAZ precisa ser reimplementada com PyNFe."); return redirect(reverse_lazy('fiscal:listanotafiscalsaidaview'))
    def get_context_data(self, **kwargs): context = super().get_context_data(**kwargs); context['title_complete'] = 'CONSULTAR CADASTRO SEFAZ'; context['btn_text'] = 'CONSULTAR'; return context
    def get(self, request, *args, **kwargs): form = self.form_class(); return self.render_to_response(self.get_context_data(form=form))

class InutilizarNotasView(CustomTemplateView):
    template_name = 'fiscal/nota_fiscal/nota_fiscal_sefaz.html'; permission_codename = ['view_notafiscalsaida', 'change_notafiscalsaida', 'inutilizar_notafiscal']
    form_class = InutilizarNotasForm # Necessita form
    def post(self, request, *args, **kwargs): messages.warning(request, "Inutilização de Notas precisa ser reimplementada com PyNFe."); return redirect(reverse_lazy('fiscal:listanotafiscalsaidaview'))
    def get_context_data(self, **kwargs): context = super().get_context_data(**kwargs); context['title_complete'] = 'INUTILIZAR NOTAS'; context['btn_text'] = 'INUTILIZAR'; return context
    def get(self, request, *args, **kwargs): form = self.form_class(); return self.render_to_response(self.get_context_data(form=form))

class ConsultarNotaView(CustomTemplateView): # Renomeado para não conflitar com ConsultarNotaFiscalView(View)
    template_name = 'fiscal/nota_fiscal/nota_fiscal_sefaz.html'; permission_codename = ['view_notafiscalsaida', 'change_notafiscalsaida', 'consultar_notafiscal']
    form_class = ConsultarNotaForm # Necessita form
    def post(self, request, *args, **kwargs): messages.warning(request, "Consulta específica de Nota via formulário precisa ser revisada/reimplementada."); return redirect(reverse_lazy('fiscal:listanotafiscalsaidaview'))
    def get_context_data(self, **kwargs): context = super().get_context_data(**kwargs); context['title_complete'] = 'CONSULTAR NOTA ESPECÍFICA'; context['btn_text'] = 'CONSULTAR'; return context
    def get(self, request, *args, **kwargs): form = self.form_class(); return self.render_to_response(self.get_context_data(form=form))

class BaixarNotaView(CustomTemplateView):
    template_name = 'fiscal/nota_fiscal/nota_fiscal_sefaz.html'; permission_codename = ['view_notafiscalsaida', 'change_notafiscalsaida', 'baixar_notafiscal']
    form_class = BaixarNotaForm # Necessita form
    def post(self, request, *args, **kwargs): messages.warning(request, "Download de NF-e (pysignfe) precisa ser reimplementado com PyNFe."); return redirect(reverse_lazy('fiscal:listanotafiscalsaidaview'))
    def get_context_data(self, **kwargs): context = super().get_context_data(**kwargs); context['title_complete'] = 'BAIXAR NOTA FISCAL'; context['btn_text'] = 'BAIXAR'; return context
    def get(self, request, *args, **kwargs): form = self.form_class(); return self.render_to_response(self.get_context_data(form=form))

class ManifestacaoDestinatarioView(CustomTemplateView):
    template_name = 'fiscal/nota_fiscal/nota_fiscal_sefaz.html'; permission_codename = ['view_notafiscalsaida', 'manifestacao_destinatario']
    form_class = ManifestacaoDestinatarioForm # Necessita form
    def post(self, request, *args, **kwargs): messages.warning(request, "Manifestação do Destinatário precisa ser reimplementada com PyNFe."); return redirect(reverse_lazy('fiscal:listanotafiscalsaidaview'))
    def get_context_data(self, **kwargs): context = super().get_context_data(**kwargs); context['title_complete'] = 'MANIFESTAÇÃO DO DESTINATÁRIO'; context['btn_text'] = 'ENVIAR'; return context
    def get(self, request, *args, **kwargs): form = self.form_class(); return self.render_to_response(self.get_context_data(form=form))

# Classe para Emitir NF-e (usando o Processador com PyNFe)
class EmitirNotaFiscalView(View): # Adicionar Mixins de Permissão/Login se necessário
    # permission_required = 'fiscal.emitir_notafiscal' # Definir permissão correta

    @transaction.atomic # Envolver em transação pode ser útil dependendo do que emitir_nfe faz
    def post(self, request, *args, **kwargs): # Receber pk da URL
        nota_id = kwargs.get('pk')
        nota = get_object_or_404(NotaFiscalSaida, pk=nota_id)

        # Verificar se Processador foi carregado
        if not ProcessadorNotaFiscal:
            messages.error(request, "Erro crítico: Processador de NF não carregado.")
            # Retornar JSON de erro se a intenção é usar AJAX
            return JsonResponse({'status': 'error','errors': ['Processador NF não carregado']}, status=500)

        processador = ProcessadorNotaFiscal()

        # Verificar permissão (exemplo, usar um mixin seria melhor)
        # if not request.user.has_perm(self.permission_required):
        #     messages.error(request, "Sem permissão para emitir NF-e.")
        #     return JsonResponse({'status': 'error','errors': ['Sem permissão']}, status=403)

        # Chama o método refatorado que usa PyNFe
        if processador.emitir_nfe(nota):
            # Mensagem de sucesso pode vir do processador ou ser definida aqui
            msg_sucesso = processador.message or f'NF-e {nota.numero}/{nota.serie} enviada e/ou autorizada!'
            messages.success(request, msg_sucesso)
            return JsonResponse({
                'status': 'success',
                'message': msg_sucesso,
                'chave': getattr(nota, 'chave', None), # Retorna chave se existir
                'protocolo': getattr(nota, 'protocolo', None) # Retorna protocolo se existir
            })
        else:
            # Mensagem de erro vem do processador
            msg_erro = processador.message or f'Erro desconhecido ao emitir NF-e {nota.numero}/{nota.serie}.'
            messages.error(request, msg_erro)
            # Retorna os erros específicos do processador, se houver
            return JsonResponse({'status': 'error', 'errors': processador.erros or [msg_erro]}, status=400)

    def get(self, request, *args, **kwargs):
        # Emissão normalmente só deve ocorrer via POST
        messages.warning(request, "A emissão de NF-e deve ser feita via POST.")
        nota_id = kwargs.get('pk')
        # Redirecionar para a página de detalhes ou edição
        return redirect('fiscal:editarnotafiscalsaidaview', pk=nota_id) # Redireciona GET para edição

# --- Fim da Classe EmitirNotaFiscalView ---

# --- MANTENHA AS OUTRAS CLASSES DE VIEW NO ARQUIVO ---
# ... (AdicionarNotaFiscalSaidaView, EditarNotaFiscalSaidaView, ImportarNotaView, etc.) ...