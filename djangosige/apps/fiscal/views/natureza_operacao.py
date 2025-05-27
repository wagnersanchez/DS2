# djangosige/apps/fiscal/views/natureza_operacao.py
# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
# LoginRequiredMixin não é necessário aqui se CustomListView já o incluir
# from django.contrib.auth.mixins import LoginRequiredMixin 

# Supondo que suas CustomViews estão em base.custom_views e já incluem LoginRequiredMixin
from djangosige.apps.base.custom_views import CustomListView, CustomCreateView, CustomUpdateView

from djangosige.apps.fiscal.models import NaturezaOperacao
from djangosige.apps.fiscal.forms import NaturezaOperacaoForm 

class NaturezaOperacaoListView(CustomListView): # Removido LoginRequiredMixin daqui
    model = NaturezaOperacao
    template_name = 'fiscal/natureza_operacao/natureza_operacao_list.html' 
    context_object_name = 'all_naturezas'
    permission_codename = 'view_naturezaoperacao' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'NATUREZAS DE OPERAÇÃO CADASTRADAS'
        context['add_url'] = reverse_lazy('fiscal:addnaturezaoperacaoview') 
        return context

class AdicionarNaturezaOperacaoView(CustomCreateView): # CustomCreateView já deve ter LoginRequiredMixin
    form_class = NaturezaOperacaoForm
    template_name = "fiscal/natureza_operacao/natureza_operacao_form.html" 
    success_url = reverse_lazy('fiscal:listanaturezaoperacaoview')
    success_message = "Natureza de Operação <b>%(descricao)s </b>adicionada com sucesso."
    permission_codename = 'add_naturezaoperacao'

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, descricao=self.object.descricao)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'ADICIONAR NATUREZA DE OPERAÇÃO'
        context['return_url'] = reverse_lazy('fiscal:listanaturezaoperacaoview')
        return context

class EditarNaturezaOperacaoView(CustomUpdateView): # CustomUpdateView já deve ter LoginRequiredMixin
    form_class = NaturezaOperacaoForm
    model = NaturezaOperacao
    template_name = "fiscal/natureza_operacao/natureza_operacao_form.html" 
    success_url = reverse_lazy('fiscal:listanaturezaoperacaoview')
    success_message = "Natureza de Operação <b>%(descricao)s </b>editada com sucesso."
    permission_codename = 'change_naturezaoperacao'

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, descricao=self.object.descricao)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'EDITAR NATUREZA DE OPERAÇÃO'
        context['return_url'] = reverse_lazy('fiscal:listanaturezaoperacaoview')
        return context
