# -*- coding: utf-8 -*-

from .natureza_operacao import NaturezaOperacaoForm
from .tributos import (
    GrupoFiscalForm, 
    ICMSForm, 
    TributoICMSSNForm,       # Assegure que este nome corresponde à classe em tributos.py
    TributoICMSUFDestForm,   # Assegure que este nome corresponde à classe em tributos.py
    IPIForm, 
    PISForm, 
    COFINSForm
)
from .nota_fiscal import (
    NotaFiscalFormBase, 
    NotaFiscalOperacaoForm, 
    EmissaoNotaFiscalForm,
    CancelamentoNotaFiscalForm,
    ConsultarCadastroForm,
    InutilizarNotasForm,
    ConsultarNotaForm,
    BaixarNotaForm,
    ManifestacaoDestinatarioForm,
)

__all__ = [
    'NaturezaOperacaoForm',
    'GrupoFiscalForm',
    'ICMSForm',
    'TributoICMSSNForm',     # Assegure que este nome corresponde à classe em tributos.py
    'TributoICMSUFDestForm', # Assegure que este nome corresponde à classe em tributos.py
    'IPIForm',
    'PISForm',
    'COFINSForm',
    'NotaFiscalFormBase',
    'NotaFiscalOperacaoForm',
    'EmissaoNotaFiscalForm',
    'CancelamentoNotaFiscalForm',
    'ConsultarCadastroForm',
    'InutilizarNotasForm',
    'ConsultarNotaForm',
    'BaixarNotaForm',
    'ManifestacaoDestinatarioForm',
]
