import os
#from decouple import config, Csv
from dj_database_url import parse as dburl
from .configs import DEFAULT_DATABASE_URL, DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_PORT, EMAIL_USE_TLS

import os
from pathlib import Path
from django.urls import reverse_lazy

# settings.py - Adições para NFe ERPBrasil
from django.core.exceptions import ImproperlyConfigured
import os

# Adicione isto logo após os imports
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def config(key, default=None):
    return os.environ.get(key, default)

def Csv(value):
    return [item.strip() for item in value.split(',')] if value else []

APP_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
print(f"DEBUG: APP_ROOT é: {APP_ROOT}")
TEMPLATE_DIR_PATH = os.path.join(APP_ROOT, 'templates')
print(f"DEBUG: Django vai procurar templates em: {TEMPLATE_DIR_PATH}")

PROJECT_ROOT = os.path.abspath(os.path.dirname(APP_ROOT))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-k#z@p!b2q&y(c)e*r+t-u=i!o%p[a]s&d(f)g@h' 

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = config('DEBUG', default='False') == 'True'
DEBUG = True  # Force True para depuração

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

if not DEFAULT_DATABASE_URL:
    DEFAULT_DATABASE_URL = 'sqlite:///' + os.path.join(APP_ROOT, 'db.sqlite3')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # djangosige apps:
    'djangosige.apps.base',
    'djangosige.apps.login',
    'djangosige.apps.fiscal',
    'djangosige.apps.cadastro',
    'djangosige.apps.vendas',
    'djangosige.apps.compras',
   
    'djangosige.apps.financeiro',
    'djangosige.apps.estoque',

     # Apps de terceiros
    'widget_tweaks',  
    
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middleware para paginas que exigem login
    'djangosige.middleware.LoginRequiredMiddleware',
]

ROOT_URLCONF = 'djangosige.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(APP_ROOT, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # contexto para a versao do sige
                'djangosige.apps.base.context_version.sige_version',
                # contexto para a foto de perfil do usuario
                'djangosige.apps.login.context_user.foto_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'djangosige.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'pt-br'

#TIME_ZONE = 'UTC'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(APP_ROOT, 'static'),
]

FIXTURE_DIRS = [
    os.path.join(APP_ROOT, 'fixtures'),
]

MEDIA_ROOT = os.path.join(APP_ROOT, 'media/')
MEDIA_URL = 'media/'

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

LOGIN_NOT_REQUIRED = (
    '/login/',
    '/login/esqueceu/',
    '/login/trocarsenha/',
    '/logout/',
)

STATIC_URL = '/static/'

LOGOUT_REDIRECT_URL = reverse_lazy('login:loginview') # Ou apenas '/login/'

# Configurações do erpbrasil.edoc

def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = f"Defina a variável de ambiente {var_name}"
        raise ImproperlyConfigured(error_msg)

# ERPBRASIL = {
#     'CERTIFICADO': {
#         'arquivo': os.path.join(BASE_DIR, 'certs/certificado.pfx'),
#         'senha': get_env_variable('CERTIFICADO_SENHA'),
#     },
#     'NFE': {
#         'AMBIENTE': 2 if DEBUG else 1,  # 1=Produção, 2=Homologação
#         'VERSAO': '4.00',
#         'UF': get_env_variable('UF_EMITENTE'),
#         'CIDADE_CODIGO': get_env_variable('CIDADE_CODIGO_IBGE'),
#     },
#     'WEBSERVICES': {
#         'TIMEOUT': 30,
#         'PROXY': os.environ.get('HTTP_PROXY'),
#     }
# }

# LOGGING = {
#     'version': 1,
#     'handlers': {
#         'erpbrasil_file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'filename': os.path.join(BASE_DIR, 'logs/erpbrasil.log'),
#         },
#     },
#     'loggers': {
#         'erpbrasil': {
#             'handlers': ['erpbrasil_file'],
#             'level': 'DEBUG',
#         },
#     },
# } 