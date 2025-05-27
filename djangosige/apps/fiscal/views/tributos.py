# djangosige/apps/fiscal/views/tributos.py
# -*- coding: utf-8 -*-

from django.urls import reverse_lazy
from django.http import HttpResponse 
from django.core import serializers 
from django.views import View 
# LoginRequiredMixin é importado aqui, mas as CustomViews já devem usá-lo.
# Se uma view não herdar de uma CustomView que já tenha LoginRequiredMixin,
# então ela precisará herdar de LoginRequiredMixin diretamente.
from django.contrib.auth.mixins import LoginRequiredMixin 

# Importar as views base customizadas
# Assumimos que estas já herdam de LoginRequiredMixin onde apropriado.
from djangosige.apps.base.custom_views import CustomCreateView, CustomListView, CustomUpdateView

# Importar os nomes corretos dos formulários
from djangosige.apps.fiscal.forms import (
    GrupoFiscalForm, 
    ICMSForm, 
    TributoICMSSNForm,    
    TributoICMSUFDestForm, 
    IPIForm, 
    PISForm, 
    COFINSForm
)
# Importar os nomes corretos dos modelos
from djangosige.apps.fiscal.models import (
    GrupoFiscal, 
    TributoICMS, 
    TributoICMSSN, 
    TributoICMSUFDest, 
    TributoIPI,
    TributoPIS, 
    TributoCOFINS 
)
from djangosige.apps.cadastro.models import MinhaEmpresa, Produto 
from djangosige.apps.login.models import Usuario


class AdicionarGrupoFiscalView(CustomCreateView): 
    form_class = GrupoFiscalForm
    template_name = "fiscal/grupo_fiscal/grupo_fiscal_form.html" 
    success_url = reverse_lazy('fiscal:listagrupofiscalview')
    success_message = "Grupo fiscal <b>%(descricao)s </b>adicionado com sucesso."
    permission_codename = 'add_grupofiscal' 

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, descricao=self.object.descricao)

    def get_context_data(self, **kwargs):
        context = super(AdicionarGrupoFiscalView, self).get_context_data(**kwargs)
        context['title_complete'] = 'ADICIONAR GRUPO FISCAL'
        context['return_url'] = reverse_lazy('fiscal:listagrupofiscalview')
        context['icms_form'] = ICMSForm(prefix='icms_form')
        context['icmssn_form'] = TributoICMSSNForm(prefix='icmssn_form')
        context['icms_dest_form'] = TributoICMSUFDestForm(prefix='icms_dest_form')
        context['ipi_form'] = IPIForm(prefix='ipi_form')
        context['pis_form'] = PISForm(prefix='pis_form')
        context['cofins_form'] = COFINSForm(prefix='cofins_form')
        return context

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form(self.get_form_class()) 

        try:
            user_empresa = MinhaEmpresa.objects.get(
                m_usuario=Usuario.objects.get(user=request.user)).m_empresa
            if hasattr(user_empresa, 'pessoa_jur_info') and user_empresa.pessoa_jur_info.sit_fiscal in ('LR', 'LP'):
                form.initial = {'regime_trib': '2'} 
            else:
                form.initial = {'regime_trib': '0'} 
        except Exception: 
            pass
        
        return self.render_to_response(self.get_context_data(form=form))


    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form(self.get_form_class()) 
        
        novo_icms_form = None 
        if request.POST.get('regime_trib') == '2': 
            novo_icms_form = ICMSForm(request.POST, prefix='icms_form')
        elif request.POST.get('regime_trib') == '0': 
            novo_icms_form = TributoICMSSNForm(request.POST, prefix='icmssn_form') 
        else:
            if not form.is_valid(): 
                icms_form = ICMSForm(request.POST, prefix='icms_form')
                icmssn_form = TributoICMSSNForm(request.POST, prefix='icmssn_form')
                icms_dest_form = TributoICMSUFDestForm(request.POST, prefix='icms_dest_form')
                ipi_form = IPIForm(request.POST, prefix='ipi_form')
                pis_form = PISForm(request.POST, prefix='pis_form')
                cofins_form = COFINSForm(request.POST, prefix='cofins_form')
                return self.form_invalid(form=form, icms_form=icms_form, icmssn_form=icmssn_form,
                                         icms_dest_form=icms_dest_form, ipi_form=ipi_form,
                                         pis_form=pis_form, cofins_form=cofins_form)
            else: 
                form.add_error('regime_trib', 'Regime tributário inválido ou não selecionado.')


        icms_dest_form = TributoICMSUFDestForm(request.POST, prefix='icms_dest_form') 
        ipi_form = IPIForm(request.POST, prefix='ipi_form')
        pis_form = PISForm(request.POST, prefix='pis_form')
        cofins_form = COFINSForm(request.POST, prefix='cofins_form')

        if novo_icms_form is None: 
            if form.is_valid(): 
                 form.add_error('regime_trib', 'Seleção de regime tributário é necessária para definir o ICMS.')
            if request.POST.get('regime_trib') == '2':
                 novo_icms_form = ICMSForm(prefix='icms_form') 
            elif request.POST.get('regime_trib') == '0':
                 novo_icms_form = TributoICMSSNForm(prefix='icmssn_form')
            else: 
                 novo_icms_form = ICMSForm(prefix='icms_form')


        all_forms_valid = form.is_valid()
        if novo_icms_form:
            all_forms_valid = all_forms_valid and novo_icms_form.is_valid()
        else: 
            all_forms_valid = False 
            if form.is_valid(): 
                form.add_error('regime_trib', 'Configuração de ICMS (Normal ou Simples Nacional) é necessária.')
        
        all_forms_valid = all_forms_valid and icms_dest_form.is_valid() and \
                          ipi_form.is_valid() and pis_form.is_valid() and \
                          cofins_form.is_valid()

        if all_forms_valid:
            self.object = form.save() 

            if novo_icms_form:
                novo_icms_form.instance.grupo_fiscal = self.object
                novo_icms_form.save()
            
            icms_dest_form.instance.grupo_fiscal = self.object
            icms_dest_form.save_m2m() if hasattr(icms_dest_form, 'save_m2m') else icms_dest_form.save()
            
            ipi_form.instance.grupo_fiscal = self.object
            ipi_form.save_m2m() if hasattr(ipi_form, 'save_m2m') else ipi_form.save()
            
            pis_form.instance.grupo_fiscal = self.object
            pis_form.save_m2m() if hasattr(pis_form, 'save_m2m') else pis_form.save()
            
            cofins_form.instance.grupo_fiscal = self.object
            cofins_form.save_m2m() if hasattr(cofins_form, 'save_m2m') else cofins_form.save()

            return self.form_valid(form) 
        
        if request.POST.get('regime_trib') == '2':
            icms_to_render = novo_icms_form if novo_icms_form else ICMSForm(request.POST, prefix='icms_form')
            icmssn_to_render = TributoICMSSNForm(prefix='icmssn_form') 
        elif request.POST.get('regime_trib') == '0':
            icms_to_render = ICMSForm(prefix='icms_form') 
            icmssn_to_render = novo_icms_form if novo_icms_form else TributoICMSSNForm(request.POST, prefix='icmssn_form')
        else: 
            icms_to_render = ICMSForm(request.POST, prefix='icms_form')
            icmssn_to_render = TributoICMSSNForm(request.POST, prefix='icmssn_form')

        return self.form_invalid(form=form,
                                 icms_form=icms_to_render,
                                 icmssn_form=icmssn_to_render,
                                 icms_dest_form=icms_dest_form,
                                 ipi_form=ipi_form,
                                 pis_form=pis_form,
                                 cofins_form=cofins_form)


class GrupoFiscalListView(CustomListView): # CustomListView já deve herdar de LoginRequiredMixin
    model = GrupoFiscal 
    template_name = 'fiscal/grupo_fiscal/grupo_fiscal_list.html' 
    context_object_name = 'all_grupos'
    permission_codename = 'view_grupofiscal'

    def get_context_data(self, **kwargs):
        context = super(GrupoFiscalListView, self).get_context_data(**kwargs)
        context['title_complete'] = 'GRUPOS FISCAIS CADASTRADOS'
        context['add_url'] = reverse_lazy('fiscal:addgrupofiscalview')
        return context


class EditarGrupoFiscalView(CustomUpdateView): # CustomUpdateView já deve herdar de LoginRequiredMixin
    form_class = GrupoFiscalForm
    model = GrupoFiscal 
    template_name = "fiscal/grupo_fiscal/grupo_fiscal_form.html" 
    success_url = reverse_lazy('fiscal:listagrupofiscalview')
    success_message = "Grupo fiscal <b>%(descricao)s </b>editado com sucesso."
    permission_codename = 'change_grupofiscal'

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, descricao=self.object.descricao)

    def get_context_data(self, **kwargs):
        context = super(EditarGrupoFiscalView, self).get_context_data(**kwargs)
        context['title_complete'] = f'EDITAR GRUPO FISCAL: {self.object.descricao}'
        context['return_url'] = reverse_lazy('fiscal:listagrupofiscalview')
        
        icms_form = ICMSForm(prefix='icms_form')
        icmssn_form = TributoICMSSNForm(prefix='icmssn_form') 

        if self.object.regime_trib == '2': 
            try:
                icms_instance = TributoICMS.objects.get(grupo_fiscal=self.object)
                icms_form = ICMSForm(instance=icms_instance, prefix='icms_form')
            except TributoICMS.DoesNotExist: pass
        elif self.object.regime_trib == '0': 
            try:
                icmssn_instance = TributoICMSSN.objects.get(grupo_fiscal=self.object)
                icmssn_form = TributoICMSSNForm(instance=icmssn_instance, prefix='icmssn_form') 
            except TributoICMSSN.DoesNotExist: pass
        
        try:
            icms_dest_instance = TributoICMSUFDest.objects.get(grupo_fiscal=self.object)
            context['icms_dest_form'] = TributoICMSUFDestForm(instance=icms_dest_instance, prefix='icms_dest_form') 
        except TributoICMSUFDest.DoesNotExist:
            context['icms_dest_form'] = TributoICMSUFDestForm(prefix='icms_dest_form')

        try:
            ipi_instance = TributoIPI.objects.get(grupo_fiscal=self.object)
            context['ipi_form'] = IPIForm(instance=ipi_instance, prefix='ipi_form')
        except TributoIPI.DoesNotExist:
            context['ipi_form'] = IPIForm(prefix='ipi_form')

        try:
            pis_instance = TributoPIS.objects.get(grupo_fiscal=self.object) 
            context['pis_form'] = PISForm(instance=pis_instance, prefix='pis_form')
        except TributoPIS.DoesNotExist: 
            context['pis_form'] = PISForm(prefix='pis_form')

        try:
            cofins_instance = TributoCOFINS.objects.get(grupo_fiscal=self.object) 
            context['cofins_form'] = COFINSForm(instance=cofins_instance, prefix='cofins_form')
        except TributoCOFINS.DoesNotExist: 
            context['cofins_form'] = COFINSForm(prefix='cofins_form')
            
        context['icms_form'] = icms_form
        context['icmssn_form'] = icmssn_form
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = GrupoFiscalForm(request.POST, instance=self.object)

        novo_icms_form = None
        icms_instance_existing = TributoICMS.objects.filter(grupo_fiscal=self.object).first()
        icmssn_instance_existing = TributoICMSSN.objects.filter(grupo_fiscal=self.object).first()
            
        if request.POST.get('regime_trib') == '2': 
            novo_icms_form = ICMSForm(request.POST, instance=icms_instance_existing, prefix='icms_form')
            if icmssn_instance_existing: icmssn_instance_existing.delete()
        elif request.POST.get('regime_trib') == '0': 
            novo_icms_form = TributoICMSSNForm(request.POST, instance=icmssn_instance_existing, prefix='icmssn_form') 
            if icms_instance_existing: icms_instance_existing.delete()
        else: 
            if not form.is_valid():
                icms_form = ICMSForm(request.POST, instance=icms_instance_existing, prefix='icms_form')
                icmssn_form = TributoICMSSNForm(request.POST, instance=icmssn_instance_existing, prefix='icmssn_form')
                icms_dest_form = TributoICMSUFDestForm(request.POST, instance=TributoICMSUFDest.objects.filter(grupo_fiscal=self.object).first(), prefix='icms_dest_form')
                ipi_form = IPIForm(request.POST, instance=TributoIPI.objects.filter(grupo_fiscal=self.object).first(), prefix='ipi_form')
                pis_form = PISForm(request.POST, instance=TributoPIS.objects.filter(grupo_fiscal=self.object).first(), prefix='pis_form')
                cofins_form = COFINSForm(request.POST, instance=TributoCOFINS.objects.filter(grupo_fiscal=self.object).first(), prefix='cofins_form')
                return self.form_invalid(form=form, icms_form=icms_form, icmssn_form=icmssn_form,
                                         icms_dest_form=icms_dest_form, ipi_form=ipi_form,
                                         pis_form=pis_form, cofins_form=cofins_form)
            else:
                 form.add_error('regime_trib', 'Regime tributário inválido ou não selecionado.')

        icms_dest_instance = TributoICMSUFDest.objects.filter(grupo_fiscal=self.object).first()
        icms_dest_form = TributoICMSUFDestForm(request.POST, instance=icms_dest_instance, prefix='icms_dest_form')

        ipi_instance = TributoIPI.objects.filter(grupo_fiscal=self.object).first()
        ipi_form = IPIForm(request.POST, instance=ipi_instance, prefix='ipi_form')

        pis_instance = TributoPIS.objects.filter(grupo_fiscal=self.object).first() 
        pis_form = PISForm(request.POST, instance=pis_instance, prefix='pis_form')

        cofins_instance = TributoCOFINS.objects.filter(grupo_fiscal=self.object).first() 
        cofins_form = COFINSForm(request.POST, instance=cofins_instance, prefix='cofins_form')

        all_forms_valid = form.is_valid()
        if novo_icms_form:
            all_forms_valid = all_forms_valid and novo_icms_form.is_valid()
        else: 
            all_forms_valid = False 
            if form.is_valid(): 
                form.add_error('regime_trib', 'Configuração de ICMS (Normal ou Simples Nacional) é necessária.')
        
        all_forms_valid = all_forms_valid and icms_dest_form.is_valid() and \
                          ipi_form.is_valid() and pis_form.is_valid() and \
                          cofins_form.is_valid()

        if all_forms_valid:
            self.object = form.save() 

            if novo_icms_form:
                novo_icms_form.instance.grupo_fiscal = self.object
                novo_icms_form.save()
            
            icms_dest_form.instance.grupo_fiscal = self.object
            icms_dest_form.save_m2m() if hasattr(icms_dest_form, 'save_m2m') else icms_dest_form.save()
            
            ipi_form.instance.grupo_fiscal = self.object
            ipi_form.save_m2m() if hasattr(ipi_form, 'save_m2m') else ipi_form.save()
            
            pis_form.instance.grupo_fiscal = self.object
            pis_form.save_m2m() if hasattr(pis_form, 'save_m2m') else pis_form.save()
            
            cofins_form.instance.grupo_fiscal = self.object
            cofins_form.save_m2m() if hasattr(cofins_form, 'save_m2m') else cofins_form.save()

            return self.form_valid(form)

        if request.POST.get('regime_trib') == '2':
            icms_to_render = novo_icms_form if novo_icms_form else ICMSForm(request.POST, instance=icms_instance_existing, prefix='icms_form')
            icmssn_to_render = TributoICMSSNForm(instance=icmssn_instance_existing, prefix='icmssn_form') 
        elif request.POST.get('regime_trib') == '0':
            icms_to_render = ICMSForm(instance=icms_instance_existing, prefix='icms_form') 
            icmssn_to_render = novo_icms_form if novo_icms_form else TributoICMSSNForm(request.POST, instance=icmssn_instance_existing, prefix='icmssn_form')
        else: 
            icms_to_render = ICMSForm(request.POST, instance=icms_instance_existing, prefix='icms_form')
            icmssn_to_render = TributoICMSSNForm(request.POST, instance=icmssn_instance_existing, prefix='icmssn_form')

        return self.form_invalid(form=form,
                                 icms_form=icms_to_render,
                                 icmssn_form=icmssn_to_render,
                                 icms_dest_form=icms_dest_form,
                                 ipi_form=ipi_form,
                                 pis_form=pis_form,
                                 cofins_form=cofins_form)
