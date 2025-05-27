# djangosige/apps/base/custom_views.py
# -*- coding: utf-8 -*-

from django.views.generic import TemplateView, ListView, View, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView # Adicionado FormView
from django.contrib.auth.mixins import LoginRequiredMixin # Importado para usar em Custom Views
from django.contrib.messages.views import SuccessMessageMixin # Para mensagens de sucesso
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django import forms # Importado para o isinstance no get_form

# Supondo que CheckPermissionMixin e FormValidationMessageMixin estão definidos em outro lugar
# ou que você os adicionará/ajustará conforme necessário.
# Se eles não existirem, você pode precisar removê-los da herança ou implementá-los.
# Por agora, vou manter como no seu arquivo original.
from djangosige.apps.base.views_mixins import CheckPermissionMixin, FormValidationMessageMixin


class CustomView(CheckPermissionMixin, LoginRequiredMixin, View): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview') # Definido login_url
    redirect_field_name = 'next'

    def __init__(self, *args, **kwargs):
        super(CustomView, self).__init__(*args, **kwargs)


class CustomTemplateView(CheckPermissionMixin, LoginRequiredMixin, TemplateView): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'

    def __init__(self, *args, **kwargs):
        super(CustomTemplateView, self).__init__(*args, **kwargs)


class CustomDetailView(CheckPermissionMixin, LoginRequiredMixin, DetailView): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'

    def __init__(self, *args, **kwargs):
        super(CustomDetailView, self).__init__(*args, **kwargs)


class CustomCreateView(CheckPermissionMixin, LoginRequiredMixin, FormValidationMessageMixin, CreateView): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'

    def __init__(self, *args, **kwargs):
        super(CustomCreateView, self).__init__(*args, **kwargs)

    # O método post original já lida com success_message através do FormValidationMessageMixin
    # e CreateView já lida com o save e redirect.
    # Este post customizado pode ser desnecessário se FormValidationMessageMixin já faz o que precisa.
    # def post(self, request, *args, **kwargs):
    #     self.object = None
    #     form_class = self.get_form_class()
    #     form = self.get_form(form_class)
    #     if form.is_valid():
    #         self.object = form.save()
    #         # FormValidationMessageMixin deve cuidar da mensagem de sucesso
    #         return redirect(self.get_success_url()) # Usar get_success_url()
    #     return self.form_invalid(form)

    def get_form(self, form_class=None):
        form = super(CustomCreateView, self).get_form(form_class)
        for field_name, field in form.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control selectpicker', 'data-live-search': 'true'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'filled-in chk-col-blue'})
        return form


class CustomListView(CheckPermissionMixin, LoginRequiredMixin, ListView): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'

    def __init__(self, *args, **kwargs):
        super(CustomListView, self).__init__(*args, **kwargs)

    def get_queryset(self):
        # É melhor que a view que herda defina o queryset ou o modelo.
        # Se model está definido, ListView já faz model.objects.all() por padrão.
        if self.model:
            return self.model.objects.all()
        return super().get_queryset()

    def post(self, request, *args, **kwargs):
        # A lógica de deleção em POST numa ListView é incomum.
        # Geralmente, deleções são feitas por views específicas (DeleteView) ou ações.
        # Certifique-se de que check_user_delete_permission está implementado no CheckPermissionMixin.
        if self.check_user_delete_permission(request, self.model):
            for key, value in request.POST.items():
                if value == "on" and key.isdigit(): # Adicionado key.isdigit() para segurança
                    try:
                        instance = self.model.objects.get(id=int(key))
                        instance.delete()
                    except self.model.DoesNotExist:
                        pass # Ou logar um aviso
        return redirect(self.get_success_url()) # Usar get_success_url()


class CustomUpdateView(CheckPermissionMixin, LoginRequiredMixin, FormValidationMessageMixin, UpdateView): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'

    def __init__(self, *args, **kwargs):
        super(CustomUpdateView, self).__init__(*args, **kwargs)

    # O método post original já lida com success_message através do FormValidationMessageMixin
    # e UpdateView já lida com o save e redirect.
    # def post(self, request, *args, **kwargs):
    #     self.object = self.get_object()
    #     form_class = self.get_form_class()
    #     form = form_class(request.POST, instance=self.object) # Correto: form_class(request.POST, ...)
    #     if form.is_valid():
    #         self.object = form.save()
    #         return redirect(self.get_success_url()) # Usar get_success_url()
    #     return self.form_invalid(form)

    def get_form(self, form_class=None):
        form = super(CustomUpdateView, self).get_form(form_class)
        for field_name, field in form.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control selectpicker', 'data-live-search': 'true'})
            elif isinstance(field.widget, forms.CheckboxInput):
                 field.widget.attrs.update({'class': 'filled-in chk-col-blue'})
        return form

# View para Deletar objetos (se você precisar dela em algum momento)
class CustomDeleteView(CheckPermissionMixin, LoginRequiredMixin, SuccessMessageMixin, DeleteView): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'
    # success_url é obrigatório para DeleteView
    # permission_codename = None

    # def get_permission_required(self):
    #     if self.permission_codename is not None:
    #         return (self.permission_codename,)
    #     return ()

# --- DEFINIÇÃO DE CustomFormView ---
class CustomFormView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'
    # permission_codename = None # Defina na view que herda, se necessário

    # def get_permission_required(self):
    #     if self.permission_codename:
    #         return (self.permission_codename,)
    #     return ()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, field in form.fields.items():
            # Verifica se o widget é uma instância das classes de widget do Django
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.EmailInput, forms.PasswordInput, forms.URLInput, forms.NumberInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control selectpicker', 'data-live-search': 'true'})
            elif isinstance(field.widget, forms.CheckboxInput):
                 field.widget.attrs.update({'class': 'filled-in chk-col-blue'}) # Estilo Materialize/AdminLTE
            # Adicione outros tipos de widget se necessário
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Exemplo de como adicionar contexto padrão
        # context['title_complete'] = getattr(self, 'title_complete', 'Formulário Padrão')
        # context['return_url'] = getattr(self, 'return_url', reverse_lazy('base:index'))
        return context

    # O método form_valid é geralmente sobrescrito na view que herda desta
    # para realizar a ação desejada com os dados do formulário.
    # SuccessMessageMixin requer que success_url seja definido ou que get_success_url seja sobrescrito.
    # def form_valid(self, form):
    #     # Lógica de processamento do formulário aqui
    #     return super().form_valid(form)

# View para TemplateView simples
class CustomTemplateView(LoginRequiredMixin, TemplateView): # Adicionado LoginRequiredMixin
    login_url = reverse_lazy('login:loginview')
    redirect_field_name = 'next'
