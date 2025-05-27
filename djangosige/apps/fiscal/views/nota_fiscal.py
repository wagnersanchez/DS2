# djangosige/apps/fiscal/views/nota_fiscal.py
# -*- coding: utf-8 -*-

from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, ListView, TemplateView, FormView, View
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render 
from django.contrib import messages 
from django.contrib.auth.mixins import LoginRequiredMixin 
from django.conf import settings 
from datetime import datetime
from django import forms 

import logging # Adicionar importação de logging
logger = logging.getLogger(__name__) # Definir o logger para este módulo

from djangosige.apps.base.custom_views import (
    CustomView, 
    CustomCreateView, 
    CustomUpdateView, 
    CustomListView, 
    CustomFormView,
    CustomDetailView 
)

from djangosige.apps.fiscal.models import NotaFiscal
from djangosige.apps.cadastro.models import MinhaEmpresa, Empresa 
from djangosige.apps.fiscal.services import EmissorNFeService 

from djangosige.apps.fiscal.forms import ConsultarCadastroForm, InutilizarNotasForm, ConsultarNotaForm, ManifestacaoDestinatarioForm


class NotaFiscalDetailView(CustomDetailView): 
    model = NotaFiscal
    template_name = 'fiscal/nota_fiscal/notafiscal_detail.html' 
    context_object_name = 'object' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = f'Detalhes da NF-e: {self.object.serie}/{self.object.numero}'
        if self.object.natureza_operacao and self.object.natureza_operacao.tipo_operacao == 'S':
            context['return_url'] = reverse_lazy('fiscal:listanotafiscalsaidaview')
        elif self.object.natureza_operacao and self.object.natureza_operacao.tipo_operacao == 'E':
            context['return_url'] = reverse_lazy('fiscal:listanotafiscalentradaview')
        else:
            context['return_url'] = reverse_lazy('base:index') 
        return context

class NotaFiscalEmitirView(CustomView): 
    def post(self, request, *args, **kwargs):
        nota_fiscal_id = kwargs.get('pk')
        nota = get_object_or_404(NotaFiscal, pk=nota_fiscal_id)

        if nota.status == 'A':
            messages.warning(request, f"A NF-e {nota.serie}/{nota.numero} já está autorizada.")
            return redirect('fiscal:nota_fiscal_detail', pk=nota.pk)
        if nota.status not in ['E', 'V', 'R']: 
            messages.error(request, f"A NF-e {nota.serie}/{nota.numero} não pode ser emitida neste status ({nota.get_status_display()}).")
            return redirect('fiscal:nota_fiscal_detail', pk=nota.pk)
        
        if hasattr(nota, 'calcular_totais'):
            nota.calcular_totais() 
            nota.save() 

        config_servico_dict = nota.get_configuracao_servico() if hasattr(nota, 'get_configuracao_servico') else {}
        resultado = EmissorNFeService.emitir(nota) 

        if resultado.get('sucesso'):
            messages.success(request, f"NF-e {nota.serie}/{nota.numero} enviada para autorização com sucesso! Protocolo: {resultado.get('protocolo')}")
        else:
            messages.error(request, f"Erro ao emitir NF-e {nota.serie}/{nota.numero}: {resultado.get('erro')}")

        return redirect('fiscal:nota_fiscal_detail', pk=nota.pk)


class NotaFiscalConsultarStatusView(CustomView): 
    def get(self, request, *args, **kwargs): 
        nota_fiscal_id = kwargs.get('pk')
        nota = get_object_or_404(NotaFiscal, pk=nota_fiscal_id)

        if not nota.chave:
            messages.error(request, "Nota Fiscal não possui chave para consulta.")
            return redirect('fiscal:nota_fiscal_detail', pk=nota.pk)

        config_servico_dict = nota.get_configuracao_servico() if hasattr(nota, 'get_configuracao_servico') else {}
        resultado = EmissorNFeService.consultar_status(nota.chave, config_servico_dict)

        if resultado.get('sucesso'):
            messages.info(request, f"Consulta de Status para NF-e {nota.chave}: {resultado.get('status')} - {resultado.get('motivo')}")
        else:
            messages.error(request, f"Erro ao consultar status da NF-e: {resultado.get('erro')}")
        
        return redirect('fiscal:nota_fiscal_detail', pk=nota.pk)


class NotaFiscalCancelarView(CustomView): 
    def post(self, request, *args, **kwargs):
        nota_fiscal_id = kwargs.get('pk')
        nota = get_object_or_404(NotaFiscal, pk=nota_fiscal_id)
        justificativa = request.POST.get('justificativa_cancelamento', '') 

        if nota.status != 'A':
            messages.error(request, "Apenas notas fiscais autorizadas podem ser canceladas.")
            return redirect('fiscal:nota_fiscal_detail', pk=nota.pk)
        
        if len(justificativa.strip()) < 15:
            messages.error(request, "A justificativa para cancelamento deve ter no mínimo 15 caracteres.")
            return redirect('fiscal:nota_fiscal_detail', pk=nota.pk) 

        config_servico_dict = nota.get_configuracao_servico() if hasattr(nota, 'get_configuracao_servico') else {}
        resultado = EmissorNFeService.cancelar(nota, justificativa, config_servico_dict)

        if resultado.get('sucesso'):
            messages.success(request, f"NF-e {nota.serie}/{nota.numero} cancelada com sucesso! Protocolo: {resultado.get('protocolo')}")
        else:
            messages.error(request, f"Erro ao cancelar NF-e: {resultado.get('erro')}")

        return redirect('fiscal:nota_fiscal_detail', pk=nota.pk)

class NotaFiscalBaixarXMLView(LoginRequiredMixin, View): 
    def get(self, request, *args, **kwargs):
        nota_fiscal_id = kwargs.get('pk')
        nota = get_object_or_404(NotaFiscal, pk=nota_fiscal_id)

        if nota.xml_gerado:
            if nota.chave:
                filename = f"NFe_{nota.chave}.xml"
            elif nota.numero and nota.serie:
                filename = f"NFe_{nota.serie}_{nota.numero}.xml"
            else:
                filename = f"NFe_{nota.pk}.xml"
            
            response = HttpResponse(nota.xml_gerado, content_type='application/xml')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, "XML da NF-e não encontrado ou ainda não gerado.")
            if nota_fiscal_id:
                return redirect(reverse('fiscal:nota_fiscal_detail', kwargs={'pk': nota_fiscal_id}))
            raise Http404("XML não disponível e ID da nota não fornecido para redirecionamento.")

class ManifestacaoDestinatarioView(CustomFormView): 
    form_class = ManifestacaoDestinatarioForm
    template_name = 'fiscal/sefaz_forms/manifestacao_destinatario_form.html' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Manifestação do Destinatário'
        context['return_url'] = reverse_lazy('base:index') 
        context['btn_text'] = 'Enviar Manifestação'
        return context

    def form_valid(self, form):
        chave_nfe = form.cleaned_data.get('chave_nfe')
        tipo_manifestacao = form.cleaned_data.get('tipo_manifestacao')
        justificativa = form.cleaned_data.get('justificativa')
        empresa_manifestante = form.cleaned_data.get('empresa_manifestante')

        if not empresa_manifestante:
            messages.error(self.request, "Por favor, selecione a empresa que está realizando a manifestação.")
            return self.form_invalid(form)

        config_servico_dict = {
            'caminho_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['arquivo'],
            'senha_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['senha'],    
            'ambiente_sefaz': settings.NFE_CONFIG['AMBIENTE_NFE'], 
            'cnpj_empresa_emitente': empresa_manifestante.cnpj_apenas_numeros,
            'uf_sigla_emitente': empresa_manifestante.endereco.get('uf_sigla') if empresa_manifestante.endereco else None,
        }
        
        logger.info(f"Simulando manifestação: Chave={chave_nfe}, Tipo={tipo_manifestacao}, Just={justificativa}, CNPJ Dest={empresa_manifestante.cnpj_apenas_numeros}")
        resultado_servico = {'sucesso': True, 'mensagem': 'Manifestação registrada com sucesso (Simulação).', 'xml_enviado': '<envEvento>...</envEvento>', 'xml_recebido': '<retEnvEvento>...</retEnvEvento>'}

        if resultado_servico.get('sucesso'):
            messages.success(self.request, resultado_servico.get('mensagem', 'Manifestação enviada com sucesso!'))
        else:
            messages.error(self.request, resultado_servico.get('erro', 'Falha ao enviar manifestação.'))

        context = self.get_context_data(form=form, processo=resultado_servico)
        return render(self.request, self.template_name, context)


class ListaNotasFiscaisSaidaView(CustomListView): 
    model = NotaFiscal
    template_name = 'fiscal/nota_fiscal/nota_fiscal_list.html' 
    context_object_name = 'all_notasfiscais'
    permission_codename = 'view_notafiscal' 

    def get_queryset(self):
        queryset = NotaFiscal.objects.select_related('natureza_operacao', 'emitente', 'destinatario').filter(natureza_operacao__tipo_operacao='S')
        return queryset.order_by('-data_emissao', '-numero')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Notas Fiscais Emitidas (Saída)'
        # context['add_url'] = reverse_lazy('fiscal:addnotafiscalsaidaview') 
        return context

    def get_success_url(self): 
        return reverse_lazy('fiscal:listanotafiscalsaidaview')

    def post(self, request, *args, **kwargs):
        logger.info("Método POST chamado em ListaNotasFiscaisSaidaView.")
        logger.info(f"Conteúdo de request.POST: {request.POST}")
        
        notas_selecionadas_ids_chaves = [key for key in request.POST if key.startswith('remover-nota-')]
        if notas_selecionadas_ids_chaves:
            ids_para_remover = [int(sid.split('-')[-1]) for sid in notas_selecionadas_ids_chaves]
            qs = NotaFiscal.objects.filter(id__in=ids_para_remover)
            count = qs.count()
            qs.delete() 
            messages.success(request, f"{count} nota(s) fiscal(is) removida(s) com sucesso.")
        else:
            messages.warning(request, "Nenhuma nota fiscal selecionada para remoção.")
            
        return redirect(self.get_success_url())


class ListaNotasFiscaisEntradaView(CustomListView): 
    model = NotaFiscal
    template_name = 'fiscal/nota_fiscal/nota_fiscal_list.html' 
    context_object_name = 'all_notasfiscais'
    permission_codename = 'view_notafiscal' 

    def get_queryset(self):
        queryset = NotaFiscal.objects.select_related('natureza_operacao', 'emitente', 'destinatario').filter(natureza_operacao__tipo_operacao='E')
        return queryset.order_by('-data_emissao', '-numero')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Notas Fiscais Recebidas (Entrada)'
        # context['add_url'] = reverse_lazy('fiscal:addnotafiscalentradaview') 
        return context
    
    def get_success_url(self): 
        return reverse_lazy('fiscal:listanotafiscalentradaview')

    def post(self, request, *args, **kwargs):
        logger.info("Método POST chamado em ListaNotasFiscaisEntradaView.")
        logger.info(f"Conteúdo de request.POST: {request.POST}")
        
        notas_selecionadas_ids_chaves = [key for key in request.POST if key.startswith('remover-nota-')]
        if notas_selecionadas_ids_chaves:
            ids_para_remover = [int(sid.split('-')[-1]) for sid in notas_selecionadas_ids_chaves]
            qs = NotaFiscal.objects.filter(id__in=ids_para_remover)
            count = qs.count()
            qs.delete()
            messages.success(request, f"{count} nota(s) fiscal(is) removida(s) com sucesso.")
        else:
            messages.warning(request, "Nenhuma nota fiscal selecionada para remoção.")
            
        return redirect(self.get_success_url())


class ConfiguracaoNotaFiscalView(SuccessMessageMixin, CustomUpdateView): 
    template_name = 'fiscal/configuracao/configuracao_nfe_form.html' 
    success_url = reverse_lazy('fiscal:configuracaonotafiscal') 
    success_message = "Configurações da NF-e salvas com sucesso!"
    
    def get_object(self, queryset=None):
        messages.warning(self.request, "Modelo e formulário de Configuração NF-e precisam ser implementados para esta página funcionar completamente.")
        return None 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Configurações da Nota Fiscal Eletrônica'
        if not self.object and not context.get('form'): 
             pass
        return context

    def form_valid(self, form):
        messages.success(self.request, self.get_success_message(form.cleaned_data))
        return super().form_valid(form)

class ConsultarCadastroSefazView(CustomFormView): 
    form_class = ConsultarCadastroForm
    template_name = 'fiscal/sefaz_forms/consultar_cadastro_form.html' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Consultar Cadastro de Contribuinte na SEFAZ'
        context['return_url'] = reverse_lazy('base:index') 
        context['btn_text'] = 'Consultar' 
        return context

    def form_valid(self, form):
        empresa_obj = form.cleaned_data.get('empresa_para_certificado') 
        uf_consulta = form.cleaned_data.get('uf_consulta')
        documento_consulta = form.cleaned_data.get('documento_consulta') 
        
        config_servico_dict = {
            'caminho_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['arquivo'],
            'senha_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['senha'],    
            'ambiente_sefaz': settings.NFE_CONFIG['AMBIENTE_NFE'],                
            'cnpj_empresa_emitente': empresa_obj.cnpj_apenas_numeros if empresa_obj else None,
            'uf_sigla_emitente': empresa_obj.endereco.get('uf_sigla') if empresa_obj and empresa_obj.endereco else None,
        }
        
        resultado_servico = EmissorNFeService.consultar_cadastro(
            config_servico_dict=config_servico_dict, 
            uf_consulta_sigla=uf_consulta,      
            documento=documento_consulta 
        )
        
        context = self.get_context_data(form=form, processo=resultado_servico) 
        return render(self.request, self.template_name, context)

class InutilizarNotasFiscaisView(CustomFormView): 
    form_class = InutilizarNotasForm 
    template_name = 'fiscal/sefaz_forms/inutilizar_notas_form.html' 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Inutilizar Faixa de Numeração de NF-e/NFC-e'
        context['return_url'] = reverse_lazy('base:index') 
        context['btn_text'] = 'Inutilizar Numeração'
        return context

    def form_valid(self, form):
        messages.info(self.request, "Funcionalidade de Inutilização de Notas ainda não implementada no backend.")
        context = self.get_context_data(form=form, processo={'resposta': {'xml': 'Simulação XML Inutilização'}}) 
        return render(self.request, self.template_name, context)

class ConsultarNotaFiscalSefazView(CustomFormView): 
    form_class = ConsultarNotaForm 
    template_name = 'fiscal/sefaz_forms/consultar_nota_form.html' 

    def get_initial(self):
        initial = super().get_initial()
        nota_pk = self.kwargs.get('pk') 
        if nota_pk:
            try:
                nota = NotaFiscal.objects.get(pk=nota_pk)
                if nota.chave:
                    initial['chave_consulta'] = nota.chave
                if nota.emitente: 
                    initial['empresa_para_certificado'] = nota.emitente
            except NotaFiscal.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Consultar Situação de NF-e na SEFAZ'
        context['return_url'] = reverse_lazy('base:index') 
        context['btn_text'] = 'Consultar Nota'
        nota_pk = self.kwargs.get('pk')
        if nota_pk:
            context['object'] = get_object_or_404(NotaFiscal, pk=nota_pk)
        return context

    def form_valid(self, form):
        empresa_obj = form.cleaned_data.get('empresa_para_certificado')
        chave_consulta = form.cleaned_data.get('chave_consulta')
        ambiente = form.cleaned_data.get('ambiente') 
        
        config_servico_dict = {
            'caminho_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['arquivo'],
            'senha_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['senha'],    
            'ambiente_sefaz': ambiente, 
            'cnpj_empresa_emitente': empresa_obj.cnpj_apenas_numeros if empresa_obj else None,
            'uf_sigla_emitente': empresa_obj.endereco.get('uf_sigla') if empresa_obj and empresa_obj.endereco else None,
        }
        
        resultado_servico = EmissorNFeService.consultar_status(chave_consulta, config_servico_dict) 

        context = self.get_context_data(form=form, processo=resultado_servico)
        nota_pk = self.kwargs.get('pk')
        if nota_pk:
            context['object'] = get_object_or_404(NotaFiscal, pk=nota_pk)
        return render(self.request, self.template_name, context)