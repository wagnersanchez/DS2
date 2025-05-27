# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect, get_object_or_404 # Adicionado get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.views.generic import View, TemplateView, FormView, ListView, DeleteView
from django.views.generic.edit import UpdateView

from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth.models import Permission, User as AuthUser # Importar User padrão explicitamente ou via get_user_model

from django.db import DatabaseError
from django.db.models.query_utils import Q
from django.core.exceptions import ValidationError, ObjectDoesNotExist # Importar ObjectDoesNotExist
from django.core.mail import send_mail
from django.urls import reverse_lazy
# from django.contrib.auth.models import User # Redundante se usar get_user_model ou importar como AuthUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template import loader
from django.utils.decorators import method_decorator # Para LogoutView
from django.views.decorators.csrf import csrf_protect   # Para LogoutView
from django.views.decorators.http import require_POST # Para LogoutView

from djangosige.apps.base.views_mixins import SuperUserRequiredMixin

# Forms locais
from .forms import UserLoginForm, UserRegistrationForm, PasswordResetForm, SetPasswordForm, PerfilUsuarioForm
# Modelo de Perfil local
from .models import Usuario
# Configurações
from djangosige.configs.settings import DEFAULT_FROM_EMAIL

# Forms e Modelos de Cadastro (usados em EditarPerfilView e SelecionarMinhaEmpresaView)
from djangosige.apps.cadastro.forms import MinhaEmpresaForm
from djangosige.apps.cadastro.models import MinhaEmpresa, Empresa

import operator
from functools import reduce


# Constantes (mantidas)
DEFAULT_PERMISSION_MODELS = ['cliente', 'fornecedor', 'produto',
                             'empresa', 'transportadora', 'unidade', 'marca', 'categoria', 'orcamentocompra', 'pedidocompra', 'condicaopagamento', 'orcamentovenda', 'pedidovenda',
                             'naturezaoperacao', 'notafiscalentrada', 'notafiscalsaida', 'grupofiscal', 'lancamento', 'planocontasgrupo', 'localestoque', 'movimentoestoque', ]

CUSTOM_PERMISSIONS = ['configurar_nfe', 'emitir_notafiscal', 'cancelar_notafiscal', 'gerar_danfe', 'consultar_cadastro', 'inutilizar_notafiscal', 'consultar_notafiscal',
                      'baixar_notafiscal', 'manifestacao_destinatario', 'faturar_pedidovenda', 'faturar_pedidocompra', 'acesso_fluxodecaixa', 'consultar_estoque', ]


class UserFormView(View):
    form_class = UserLoginForm
    template_name = 'login/login.html'

    # SUGESTÃO: Considerar substituir por django.contrib.auth.views.LoginView

    def get(self, request):
        form = self.form_class(None)
      #  if request.user.is_authenticated:
      #      return redirect('base:index')
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST or None)
        if request.POST and form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # Assumindo que form.authenticate_user chama auth.authenticate
            user = form.authenticate_user(username=username, password=password)
            if user:
                if not request.POST.get('remember_me', None):
                    request.session.set_expiry(0)
                login(request, user)
                return redirect('base:index')
            # Se authenticate falhar, o form deve adicionar o erro apropriado
            # Certifique-se que UserLoginForm faz isso
        return render(request, self.template_name, {'form': form})


class UserRegistrationFormView(SuperUserRequiredMixin, SuccessMessageMixin, FormView):
    form_class = UserRegistrationForm
    template_name = 'login/registrar.html'
    success_url = reverse_lazy('login:usuariosview')
    success_message = "Novo usuário <b>%(username)s</b> criado com sucesso."

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, username=cleaned_data['username'])

    # Usar form_valid é mais padrão para FormView
    def form_valid(self, form):
        user = form.save(commit=False)
        password = form.cleaned_data['password']
        # A confirmação já deve ser feita no clean() do form
        user.set_password(password)
        user.save()

        # SUGESTÃO: Adicionar criação do perfil Usuario aqui, se necessário
        # try:
        #     Usuario.objects.create(user=user)
        # except Exception as e:
        #     # Lidar com erro na criação do perfil (logar, etc.)
        #     print(f"Erro ao criar perfil para {user.username}: {e}")
        #     pass # Ou adicionar uma mensagem de erro?

        return super().form_valid(form)

    # Simplificar get e post usando FormView
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = 'Registrar Novo Usuário' # Exemplo
        context['return_url'] = self.success_url
        return context

    # O post padrão do FormView chama form_valid/form_invalid


class UserLogoutView(View):
    # --- CÓDIGO CORRIGIDO PARA USAR POST ---
    @method_decorator(csrf_protect)
    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        print("--- EXECUTANDO UserLogoutView.post ---") # DEBUG
        logout(request)
        print("--- django.contrib.auth.logout() FOI CHAMADO ---") # DEBUG
        messages.success(request, 'Logout realizado com sucesso!')
        return redirect('login:loginview')

    # Adicionar um GET que talvez redirecione para o login ou mostre um erro
    def get(self, request, *args, **kwargs):
         messages.warning(request, 'Use o botão para sair com segurança.')
         return redirect('base:index') # Redireciona para o início em vez de fazer logout

# Classe mantida, mas considerar usar PasswordResetView padrão do Django
class ForgotPasswordView(FormView):
    template_name = "login/esqueceu_senha.html"
    success_url = reverse_lazy('login:loginview')
    form_class = PasswordResetForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        # Usar settings do Django é mais robusto que importar diretamente
        from django.conf import settings
        if not getattr(settings, 'DEFAULT_FROM_EMAIL', None):
            form.add_error(None, "Envio de email não configurado.")
            return self.form_invalid(form)

        if form.is_valid():
            data = form.cleaned_data["email_or_username"]
            UserModel = get_user_model() # Usar get_user_model
            associated_users = UserModel.objects.filter(Q(email__iexact=data) | Q(username__iexact=data))

            for user in associated_users: # Iterar sobre possíveis usuários encontrados
                try:
                    if user.email:
                        context = {
                            'email': user.email,
                            'domain': request.get_host(), # Melhor que request.META['HTTP_HOST']
                            'site_name': 'DjangoSIGE', # Talvez buscar de Sites framework?
                            'uid': urlsafe_base64_encode(force_bytes(user.pk)), # Não precisa decode aqui
                            'user': user,
                            'token': default_token_generator.make_token(user),
                            'protocol': 'https' if request.is_secure() else 'http', # Usar protocolo correto
                        }
                        subject = "Redefinir sua senha - DjangoSIGE" # Remover u''
                        email_template_name = 'login/trocar_senha_email.html'
                        # Usar EmailMultiAlternatives para enviar HTML e Texto
                        # from django.core.mail import EmailMultiAlternatives
                        email_mensagem = loader.render_to_string(email_template_name, context)
                        # Falta a versão em texto plano para email_mensagem
                        send_mail(subject, email_mensagem, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
                        messages.success(request, f'Um email foi enviado para {user.email} com instruções.')
                        # Não sair do loop se houver múltiplos usuários com mesmo email?
                        # A lógica padrão do Django envia para todos que encontrar

                    else:
                        messages.warning(request, f"O usuário {user.username} não possui email cadastrado.")

                except Exception as e:
                    messages.error(request, f"Erro ao enviar email para {user.username}: {e}")

            # Mensagem genérica se nenhum usuário foi encontrado ou todos falharam/não tinham email
            if not associated_users.exists():
                 messages.error(request, f"Usuário/Email '{data}' não encontrado.")
            # Redirecionar para success_url mesmo se email não foi enviado para evitar enumeração de usuários
            return self.form_valid(form)

        # Se o formulário for inválido
        return self.form_invalid(form)

# Classe mantida, mas considerar usar PasswordResetConfirmView padrão do Django
class PasswordResetConfirmView(FormView):
    template_name = "login/trocar_senha.html"
    success_url = reverse_lazy('login:loginview')
    form_class = SetPasswordForm
    token_generator = default_token_generator # Usar como atributo de classe

    def dispatch(self, request, uidb64=None, token=None, *args, **kwargs):
        self.user = self.get_user(uidb64)
        if self.user is not None:
            if not self.token_generator.check_token(self.user, token):
                 messages.error(request, "O link de redefinição de senha é inválido ou expirou.")
                 return redirect('login:forgotpasswordview') # Redireciona para pedir novo link
        else:
            messages.error(request, "O link de redefinição de senha é inválido.")
            return redirect('login:forgotpasswordview')
        return super().dispatch(request, *args, **kwargs)

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model()._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist, UnicodeDecodeError):
            user = None
        return user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user # Passar user para o form se ele precisar
        return kwargs

    def form_valid(self, form):
        form.save() # O SetPasswordForm padrão já faz user.set_password e user.save()
        messages.success(self.request, "Senha redefinida com sucesso! Você já pode fazer login.")
        return super().form_valid(form)

    def form_invalid(self, form):
         messages.error(self.request, "Não foi possível redefinir a senha. Verifique os erros abaixo.")
         return super().form_invalid(form)

    # O post padrão do FormView chama form_valid/form_invalid


class MeuPerfilView(TemplateView): # Adicionar LoginRequiredMixin?
    # from django.contrib.auth.mixins import LoginRequiredMixin
    # class MeuPerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'login/perfil.html'
    # Não precisa do model aqui se o contexto vem de processadores ou get_context_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = "Meu Perfil" # Adicionar título
        # Buscar perfil e empresa aqui é mais explícito que context processor
        try:
            context['perfil_usuario'] = Usuario.objects.get(user=self.request.user)
        except Usuario.DoesNotExist:
            context['perfil_usuario'] = None
        try:
             context['minha_empresa_obj'] = MinhaEmpresa.objects.select_related('m_empresa').get(m_usuario=context['perfil_usuario'])
             context['user_empresa'] = context['minha_empresa_obj'].m_empresa # Para consistência com base.html
        except (MinhaEmpresa.DoesNotExist, TypeError): # TypeError se perfil for None
             context['minha_empresa_obj'] = None
             context['user_empresa'] = None
        return context

class EditarPerfilView(SuccessMessageMixin, UpdateView): # Adicionar LoginRequiredMixin?
    # from django.contrib.auth.mixins import LoginRequiredMixin
    # class EditarPerfilView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Usuario # O UpdateView edita o Perfil Usuario
    form_class = PerfilUsuarioForm # Form para o Perfil
    template_name = 'login/editar_perfil.html'
    success_url = reverse_lazy('login:perfilview')
    success_message = "Perfil editado com sucesso."

    def get_object(self, queryset=None):
        # Busca ou cria o perfil para o usuário logado
        obj, created = Usuario.objects.get_or_create(user=self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        context = super(EditarPerfilView, self).get_context_data(**kwargs)
        context['title_complete'] = "Editar Perfil"
        context['return_url'] = self.success_url
        if 'minha_empresa_form' not in kwargs:
            try:
                # Tenta pegar a instância de MinhaEmpresa existente
                empresa_instance = MinhaEmpresa.objects.get(m_usuario=self.object)
                context['minha_empresa_form'] = MinhaEmpresaForm(prefix='m_empresa_form', instance=empresa_instance)
            except MinhaEmpresa.DoesNotExist:
                # Se não existe, cria um form vazio
                context['minha_empresa_form'] = MinhaEmpresaForm(prefix='m_empresa_form')
        else:
             # Passa o form com erro vindo do form_invalid
             context['minha_empresa_form'] = kwargs['minha_empresa_form']

        # Passar dados do User para edição (se o PerfilUsuarioForm não os incluir diretamente)
        context['user_data'] = {
            'first_name': self.request.user.first_name,
            'last_name': self.request.user.last_name,
            'username': self.request.user.username,
            'email': self.request.user.email,
        }
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() # Objeto Perfil Usuario
        form = self.get_form() # Form do Perfil Usuario

        # Instanciar o form da empresa
        try:
            empresa_instance = MinhaEmpresa.objects.get(m_usuario=self.object)
            minha_empresa_form = MinhaEmpresaForm(request.POST, prefix='m_empresa_form', instance=empresa_instance)
        except MinhaEmpresa.DoesNotExist:
            minha_empresa_form = MinhaEmpresaForm(request.POST, prefix='m_empresa_form')

        # Validar ambos os forms
        if form.is_valid() and minha_empresa_form.is_valid():
            # Atualizar dados do User padrão (exemplo, idealmente seria um form separado ou no PerfilUsuarioForm)
            user = request.user # Ou self.object.user
            user.first_name = request.POST.get("first_name", user.first_name) # Pega do POST se existir
            user.last_name = request.POST.get("last_name", user.last_name)
            # user.username = request.POST.get("username", user.username) # Cuidado ao mudar username
            user.email = request.POST.get("email", user.email)
            try:
                user.full_clean()
                user.save()
            except ValidationError as e:
                 # Adicionar erros do User ao form principal (ou um form específico do User)
                 form.add_error(None, e)
                 return self.form_invalid(form=form, minha_empresa_form=minha_empresa_form)

            # Salvar o Perfil Usuario (o form.save() do UpdateView já faz isso)
            perfil = form.save()

            # Salvar MinhaEmpresa
            minha_empresa = minha_empresa_form.save(commit=False)
            minha_empresa.m_usuario = perfil # Garante a ligação correta
            minha_empresa.save()

            return self.form_valid(form)
        else:
            # Se algum form for inválido
            return self.form_invalid(form=form, minha_empresa_form=minha_empresa_form)

    def form_valid(self, form):
        # O success_message já é tratado pelo SuccessMessageMixin
        return super().form_valid(form)

    def form_invalid(self, form, minha_empresa_form):
        # Passa ambos os forms (um pode estar válido, outro inválido) para o contexto
        messages.error(self.request, "Por favor, corrija os erros abaixo.")
        return self.render_to_response(self.get_context_data(form=form, minha_empresa_form=minha_empresa_form))

# Esta view é para o popup que não está funcionando.
# A lógica da view parece OK, o problema deve ser front-end (JS/HTML).
# Considerar adicionar LoginRequiredMixin.
class SelecionarMinhaEmpresaView(SuccessMessageMixin, FormView):
    form_class = MinhaEmpresaForm
    template_name = "login/selecionar_minha_empresa.html" # Template do conteúdo do popup/modal
    success_url = reverse_lazy('login:perfilview') # Redireciona para o perfil após salvar
    success_message = "Empresa vinculada com sucesso!"

    def get_object(self):
        # Busca ou cria o perfil do usuário logado
        perfil, created = Usuario.objects.get_or_create(user=self.request.user)
        return perfil

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_complete'] = "Selecionar Minha Empresa"
        return context

    def get_initial(self):
        # Tenta preencher o form com a empresa já vinculada, se existir
        initial = super().get_initial()
        perfil = self.get_object()
        try:
            minha_empresa_obj = MinhaEmpresa.objects.get(m_usuario=perfil)
            initial['m_empresa'] = minha_empresa_obj.m_empresa
        except MinhaEmpresa.DoesNotExist:
            pass
        return initial

    def form_valid(self, form):
        perfil = self.get_object()
        empresa_selecionada = form.cleaned_data['m_empresa']
        # Usar update_or_create para lidar com adição ou edição
        MinhaEmpresa.objects.update_or_create(
            m_usuario=perfil,
            defaults={'m_empresa': empresa_selecionada}
        )
        # A mensagem de sucesso é tratada pelo SuccessMessageMixin
        # Verificar se o popup precisa de uma resposta especial (ex: fechar modal via JS)
        # Por enquanto, redireciona para success_url
        return super().form_valid(form)

    def form_invalid(self, form):
         messages.error(self.request, "Erro ao selecionar empresa.")
         # Re-renderizar o template do popup com o erro
         return super().form_invalid(form)


# Views de Gerenciamento de Usuários (requerem SuperUser)
class UsuariosListView(SuperUserRequiredMixin, ListView):
    template_name = 'login/lista_users.html'
    model = get_user_model() # Usar get_user_model
    context_object_name = 'all_users'
    paginate_by = 10 # Adicionar paginação

    def get_context_data(self, **kwargs):
         context = super().get_context_data(**kwargs)
         context['title_complete'] = "Gerenciar Usuários"
         context['add_url'] = reverse_lazy('login:registrarview') # Link para registrar
         return context

    # Manter a exclusão via POST por segurança, mas idealmente com confirmação
    def post(self, request, *args, **kwargs):
        # Melhor usar um campo hidden ou valor específico em vez de 'on'
        # Ex: <input type="checkbox" name="delete_user" value="{{ user.pk }}">
        deleted_count = 0
        pks_to_delete = request.POST.getlist('delete_user') # Assumindo name="delete_user" value="{{user.pk}}"
        if pks_to_delete:
             # Nunca deletar o próprio superusuário logado
             queryset = self.get_queryset().exclude(pk=request.user.pk).filter(pk__in=pks_to_delete)
             deleted_count = queryset.count()
             queryset.delete()

        if deleted_count > 0:
             messages.success(request, f"{deleted_count} usuário(s) excluído(s) com sucesso.")
        else:
             messages.warning(request, "Nenhum usuário selecionado ou tentativa de excluir a si mesmo.")

        return redirect(reverse_lazy('login:usuariosview'))


class UsuarioDetailView(SuperUserRequiredMixin, TemplateView):
    template_name = 'login/detalhe_users.html'

    def get_context_data(self, **kwargs):
        context = super(UsuarioDetailView, self).get_context_data(**kwargs)
        user_pk = self.kwargs.get('pk')
        user_obj = get_object_or_404(get_user_model(), pk=user_pk) # Usar get_object_or_404

        context['user_match'] = user_obj
        context['title_complete'] = f"Detalhes: {user_obj.username}"
        context['return_url'] = reverse_lazy('login:usuariosview')

        # Buscar foto do perfil relacionado
        try:
            # Usar related_name 'usuario' (padrão se não definido em OneToOneField) ou o nome do campo 'user'
            # profile = Usuario.objects.get(user=user_obj) # Assumindo OneToOneField 'user' em Usuario
            # Vamos tentar o related_name padrão que é o nome da classe em minúsculo
            profile = getattr(user_obj, 'usuario', None) # Tenta acessar via related_name reverso
            if profile:
                 context['user_foto'] = profile.user_foto
            else: # Tenta buscar pelo campo direto se Usuario for o user model
                 if isinstance(user_obj, Usuario): context['user_foto'] = user_obj.user_foto
                 else: context['user_foto'] = None # Não achou perfil ou não é o modelo de perfil
        except ObjectDoesNotExist: # Captura DoesNotExist de Usuario (perfil)
             context['user_foto'] = None # Perfil não existe
             context['profile_error'] = "Perfil associado (login.Usuario) não encontrado."
        except Exception as e:
             print(f"Erro ao buscar foto em UsuarioDetailView: {e}")
             context['user_foto'] = None
             context['profile_error'] = "Erro ao buscar perfil."

        return context


class DeletarUsuarioView(SuperUserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = get_user_model() # Usar get_user_model
    template_name = 'login/user_confirm_delete.html' # Usar template de confirmação padrão
    success_url = reverse_lazy('login:usuariosview')
    success_message = "Usuário excluído com sucesso."

    def post(self, request, *args, **kwargs):
        # Impedir exclusão do próprio usuário logado
        if str(self.get_object().pk) == str(request.user.pk):
            messages.error(request, "Você não pode excluir sua própria conta de superusuário.")
            return redirect(self.success_url)
        # Impedir exclusão do último superusuário? (Lógica adicional necessária)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
         context = super().get_context_data(**kwargs)
         context['title_complete'] = f"Confirmar Exclusão: {self.object.username}"
         context['return_url'] = reverse_lazy('login:usuariodetailview', kwargs={'pk': self.object.pk})
         return context


class EditarPermissoesUsuarioView(SuperUserRequiredMixin, TemplateView):
    template_name = 'login/editar_permissoes_user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_pk = self.kwargs.get('pk')
        target_user = get_object_or_404(get_user_model(), pk=user_pk)
        context['target_user'] = target_user # Renomear para evitar conflito com request.user
        context['title_complete'] = f"Editar Permissões: {target_user.username}"
        context['return_url'] = reverse_lazy('login:usuariodetailview', kwargs={'pk': target_user.pk})

        # Lógica para buscar permissões (parece OK, mas depende das constantes)
        # Seria melhor usar contenttypes para buscar modelos dinamicamente?
        # Mas para um conjunto fixo, a lista funciona.
        try:
             q_objects = [Q(codename__icontains=prefix) for prefix in ['add_', 'change_', 'view_', 'delete_']]
             condition = reduce(operator.or_, q_objects)
             context['default_permissions'] = Permission.objects.filter(
                 condition, content_type__model__in=DEFAULT_PERMISSION_MODELS).select_related('content_type')
             context['custom_permissions'] = Permission.objects.filter(
                 codename__in=CUSTOM_PERMISSIONS).select_related('content_type')
        except Exception as e:
             print(f"Erro ao buscar permissões: {e}")
             messages.error(self.request, "Erro ao carregar lista de permissões.")
             context['default_permissions'] = None
             context['custom_permissions'] = None

        return context

    def post(self, request, *args, **kwargs):
        user_pk = self.kwargs.get('pk')
        target_user = get_object_or_404(get_user_model(), pk=user_pk)

        # Superusuário sempre tem todas as permissões
        if target_user.is_superuser:
            messages.warning(request, "Não é possível alterar permissões de um Superusuário.")
            return redirect(reverse_lazy('login:usuariodetailview', kwargs={'pk': target_user.pk}))

        # Limpar permissões atuais e adicionar as selecionadas
        try:
            selected_perms_codenames = request.POST.getlist('select_permissoes')
            all_possible_perms = Permission.objects.filter(
                 Q(codename__in=selected_perms_codenames) | # Permissões selecionadas
                 (Q(content_type__model__in=DEFAULT_PERMISSION_MODELS) & reduce(operator.or_, [Q(codename__icontains=p) for p in ['add_','change_','delete_','view_']])) | # Permissões padrão consideradas
                 Q(codename__in=CUSTOM_PERMISSIONS) # Permissões customizadas consideradas
            ).distinct()

            selected_perms_set = set()
            for p in all_possible_perms:
                 if p.codename in selected_perms_codenames:
                     selected_perms_set.add(p)

            target_user.user_permissions.set(selected_perms_set) # Usar set() é mais eficiente

            messages.success(request, f'Permissões do usuário <b>{target_user.username}</b> atualizadas com sucesso.')
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao salvar as permissões: {e}")

        return redirect(reverse_lazy('login:usuariodetailview', kwargs={'pk': target_user.pk}))
