# djangosige/apps/fiscal/models/__init__.py
# -*- coding: utf-8 -*-

from .natureza_operacao import NaturezaOperacao
from .nota_fiscal import NotaFiscal
from .item_nota_fiscal import ItemNotaFiscal
from .grupo_fiscal import GrupoFiscal

# Importando os modelos de tributos com os nomes corretos (prefixo "Tributo")
# Certifique-se de que o arquivo 'tributos.py' (ou arquivos individuais se você os separou)
# definem as classes com estes nomes.
from .tributos import (
    TributoICMS, 
    TributoICMSUFDest, 
    TributoICMSSN, 
    TributoIPI, 
    TributoPIS, 
    TributoCOFINS
)

__all__ = [
    'NaturezaOperacao',
    'NotaFiscal',
    'ItemNotaFiscal',
    'GrupoFiscal',
    'TributoICMS', 
    'TributoICMSUFDest', 
    'TributoICMSSN', 
    'TributoIPI', 
    'TributoPIS', 
    'TributoCOFINS',
]

