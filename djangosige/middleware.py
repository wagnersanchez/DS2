# -*- coding: utf-8 -*-

import re
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse # Usar reverse para evitar hardcoding

# Assumindo que LOGIN_NOT_REQUIRED está acessível (verificar caminho do import)
try:
    # Tentar caminho relativo se middleware.py estiver no mesmo nível que configs/
    from .configs.settings import LOGIN_NOT_REQUIRED
except ImportError:
    # Tentar caminho absoluto se middleware.py estiver em outro lugar
    try:
         from djangosige.configs.settings import LOGIN_NOT_REQUIRED
    except ImportError:
         # Definir um padrão vazio se não encontrar, mas isso quebrará a lógica
         print("ERRO CRÍTICO: Não foi possível importar LOGIN_NOT_REQUIRED no middleware.")
         LOGIN_NOT_REQUIRED = ()

class LoginRequiredMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        # Compilar as URLs isentas (usar re.fullmatch se quiser correspondência exata?)
        # Garantir que as URLs em LOGIN_NOT_REQUIRED estejam corretas (ex: '/login/$' para exato)
        # Usar match por enquanto, assumindo que são prefixos ou caminhos exatos começando com /
        self.exceptions = [re.compile(url) for url in LOGIN_NOT_REQUIRED]
        # Adicionar URL de login explicitamente às exceções para evitar loops
        try:
             # Resolver o nome da URL de login uma vez
             self.login_url = reverse('login:loginview')
             # Compilar a URL de login também, se não estiver já em LOGIN_NOT_REQUIRED
             if not any(pattern.pattern == f"^{re.escape(self.login_url)}$" for pattern in self.exceptions):
                  self.exceptions.append(re.compile(f"^{re.escape(self.login_url)}$"))
        except Exception as e:
             print(f"AVISO: Não foi possível resolver 'login:loginview' no middleware: {e}. Use a URL fixa.")
             self.login_url = '/login/' # Fallback para URL fixa
             if not any(pattern.pattern == '^/login/$' for pattern in self.exceptions):
                   self.exceptions.append(re.compile('^/login/$'))


    def process_view(self, request, view_func, view_args, view_kwargs):
        assert hasattr(request, 'user'), (
            "O LoginRequiredMiddleware requer que o middleware de autenticação "
            "esteja instalado. Verifique sua configuração MIDDLEWARE."
        )

        # 1. Verificar se a URL acessada é uma das isentas
        path = request.path_info # Usar path_info que não inclui script_name
        for url_pattern in self.exceptions:
            if url_pattern.match(path):
                # É uma URL isenta, permitir acesso para qualquer um
                return None # Continua para a view

        # 2. A URL não é isenta (requer login). Verificar se o usuário está logado.
        if request.user.is_authenticated:
            # Usuário logado acessando página protegida, permitir acesso
            return None # Continua para a view
        else:
            # Usuário NÃO logado tentando acessar página protegida.
            # Redirecionar para o login, adicionando ?next= para voltar depois
            # Garantir que não estamos redirecionando para a própria página de login (safety net)
            if path != self.login_url:
                from django.contrib.auth.views import redirect_to_login
                # Usa a função padrão do Django que lida com o parâmetro 'next'
                return redirect_to_login(path, self.login_url)
            else:
                 # Se, por algum motivo, chegou aqui tentando acessar /login/ sem estar isento, permite
                 return None
