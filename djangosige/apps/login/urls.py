from django.contrib.auth import views as auth_views
from django.urls import path, include, re_path
from . import views

app_name = 'login'
urlpatterns = [
    # login/
    path('', views.UserFormView.as_view(), name='loginview'),

    # login/registrar/
    path('registrar/', views.UserRegistrationFormView.as_view(),
        name='registrarview'),

    # login/esqueceu/:
    path('esqueceu/', views.ForgotPasswordView.as_view(), name='esqueceuview'),

    # login/trocarsenha/:
    re_path(r'^trocarsenha/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        views.PasswordResetConfirmView.as_view(), name='trocarsenhaview'),

    # logout
    #path('logout/', views.UserLogoutView.as_view(), name='logoutview'),
    path('logout/', auth_views.LogoutView.as_view(), name='logoutview'),

    # login/perfil/
    path('perfil/', views.MeuPerfilView.as_view(), name='perfilview'),

    # login/editarperfil/
    path('editarperfil/', views.EditarPerfilView.as_view(), name='editarperfilview'),

    # login/usuarios/
    path('usuarios/', views.UsuariosListView.as_view(), name='usuariosview'),

    # login/usuarios/(id_usuario)
    path('usuarios/<int:pk>/',
        views.UsuarioDetailView.as_view(), name='usuariodetailview'),

    # deletar usuario
    path('deletaruser/<int:pk>/',
        views.DeletarUsuarioView.as_view(), name='deletarusuarioview'),

    # permissoes usuario
    path('permissoesusuario/<int:pk>/',
        views.EditarPermissoesUsuarioView.as_view(), name='permissoesusuarioview'),

    # selecionar empresa
    path('selecionarempresa/', views.SelecionarMinhaEmpresaView.as_view(),
        name='selecionarempresaview'),
]
