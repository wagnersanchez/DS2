# djangosige/apps/fiscal/compat.py
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

# --- Valores Padrão (caso as importações da nfelib falhem) ---
_ImportedTnfe, _ImportedTenderEmi, _ImportedTendereco, _ImportedTipi = None, None, None, None
_ImportedIdeTpNf, _ImportedIdeIdDest, _ImportedIdeTpImp, _ImportedIdeTpEmis, _ImportedTfinNfe = (None,) * 5
_ImportedIdeIndFinal, _ImportedIdeIndPres, _ImportedTprocEmi_lib, _ImportedEmitCrt, _ImportedDestIndIedest = (None,) * 5 # Mantido _lib para o importado
_ImportedTorig, _ImportedProdIndTot = None, None
_ImportedTamb, _ImportedTmod, _ImportedTcodUfIbge, _ImportedTufEmi, _ImportedTuf = (None,) * 5

_ImportedTenviNfe, _ImportedTconsReciNfe, _ImportedTretEnviNfe = None, None, None
_ImportedTProtNfe, _ImportedTnfeProc, _ImportedTinfRespTec = None, None, None

_TConsCad, _TUfCons, _TRetConsCad = None, None, None
_XmlSerializer, _SerializerConfig, _XMLParser = None, None, None
_XMLSerializerConfigInstance, _XMLSerializerInstance = None, None

# --- Tenta importar os bindings da NF-e v4.00 ---
try:
    from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import (
        Tnfe as _ImportedTnfe,
        TenderEmi as _ImportedTenderEmi,
        Tendereco as _ImportedTendereco,
        Tipi as _ImportedTipi,
        IdeTpNf as _ImportedIdeTpNf,
        IdeIdDest as _ImportedIdeIdDest,
        IdeTpImp as _ImportedIdeTpImp,
        IdeTpEmis as _ImportedIdeTpEmis,
        TfinNfe as _ImportedTfinNfe,
        IdeIndFinal as _ImportedIdeIndFinal,
        IdeIndPres as _ImportedIdeIndPres,  
        TprocEmi as _ImportedTprocEmi_lib,    # CORRIGIDO: Importar TprocEmi (com T e p minúsculo)
        EmitCrt as _ImportedEmitCrt,
        DestIndIedest as _ImportedDestIndIedest, 
        Torig as _ImportedTorig,            
        ProdIndTot as _ImportedProdIndTot,  
        TenviNfe as _ImportedTenviNfe,      
        TconsReciNfe as _ImportedTconsReciNfe, 
        TretEnviNfe as _ImportedTretEnviNfe,   
        #TProtNfe as _ImportedTProtNfe, 
        TnfeProc as _ImportedTnfeProc,
        TinfRespTec as _ImportedTinfRespTec
    )
    from nfelib.nfe.bindings.v4_0.tipos_basico_v4_00 import (
        Tamb as _ImportedTamb,
        Tmod as _ImportedTmod,
        TcodUfIbge as _ImportedTcodUfIbge,
        TufEmi as _ImportedTufEmi,
        Tuf as _ImportedTuf

    )
    logger.info("Compat: Bindings da NF-e v4.00 carregados de nfelib.nfe.bindings.v4_0.*")
except ImportError as e_nfe_bindings:
    logger.error(f"Compat: Falha ao importar um ou mais bindings da NF-e v4.00. Erro: {e_nfe_bindings}")

''' # --- Bindings da Consulta Cadastro v2.00 (para services.py) ---
try:
    from nfelib.nfe_cons.bindings.v2_0.cons_cad_v2_00 import ( 
        TConsCad as _TConsCad, 
        TUf as _TUfCons 
    )
    from nfelib.nfe_cons.bindings.v2_0.ret_cons_cad_v2_00 import TRetConsCad as _TRetConsCad
    logger.info("Compat: Bindings de Consulta Cadastro (nfelib.nfe_cons.bindings.v2_0) carregados.")
except ImportError:
    logger.warning("Compat: Bindings para Consulta Cadastro (cons_cad_v2_00) não encontrados na nfelib.") '''

# --- xsdata (usado pela nfelib) ---
try:
    from xsdata.formats.dataclass.serializers import XmlSerializer as _XmlSerializer
    from xsdata.formats.dataclass.serializers.config import SerializerConfig as _SerializerConfig
    from xsdata.formats.dataclass.parsers import XmlParser as _XMLParser
    
    XmlSerializer = _XmlSerializer
    SerializerConfig = _SerializerConfig
    XMLParser = _XMLParser
    logger.info("Compat: xsdata Serializer/Parser carregados.")
except ImportError as e_xsdata:
    logger.warning(f"Compat: Aviso - Erro ao importar xsdata: {str(e_xsdata)}.")

# --- Mapeamento de Aliases para o código DjangoSIGE ---
NFe = _ImportedTnfe 
Tnfe = _ImportedTnfe 
TenderEmi = _ImportedTenderEmi
Tendereco = _ImportedTendereco
TIpi = _ImportedTipi 

TpNF = _ImportedIdeTpNf 
IdDest = _ImportedIdeIdDest 
TpImp = _ImportedIdeTpImp
TpEmis = _ImportedIdeTpEmis
FinNFe = _ImportedTfinNfe       
IndFinal = _ImportedIdeIndFinal
IndPres = _ImportedIdeIndPres
ProcEmi = _ImportedTprocEmi_lib # CORRIGIDO: Usar o nome da variável importada
CRT = _ImportedEmitCrt
IndIEDest = _ImportedDestIndIedest
Torig = _ImportedTorig
ProdIndTot = _ImportedProdIndTot

Tamb = _ImportedTamb
Tmod = _ImportedTmod
TcodUfIbge = _ImportedTcodUfIbge
TufEmi = _ImportedTufEmi
Tuf = _ImportedTuf

TEnder = Tendereco 

TEnviNfe = _ImportedTenviNfe
TConsReciNfe = _ImportedTconsReciNfe 
TRetEnviNfe = _ImportedTretEnviNfe   
TProtNfe = _ImportedTProtNfe 
TnfeProc = _ImportedTnfeProc
TinfRespTec = _ImportedTinfRespTec

TConsCadNfelib = _TConsCad
TUfConsNfelib = _TUfCons
TRetConsCadNfelib = _TRetConsCad

XmlSerializerNfelib = XmlSerializer 
SerializerConfigNfelib = SerializerConfig 
XML_PARSER_Nfelib = XMLParser 

XMLSerializerInstance = None
if XmlSerializerNfelib and SerializerConfigNfelib:
    XMLSerializerConfigInstance = SerializerConfigNfelib(pretty_print=True, xml_declaration=False) 
    XMLSerializerInstance = XmlSerializerNfelib(config=XMLSerializerConfigInstance)

XML_SERIALIZER_Nfelib_local = XMLSerializerInstance

# Componentes da erpbrasil.edoc são importados diretamente no services.py
# Não há necessidade de reexportá-los aqui se o services.py os importa diretamente.
