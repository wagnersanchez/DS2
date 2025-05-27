# djangosige/apps/fiscal/services.py
# -*- coding: utf-8 -*-

import logging
from django.conf import settings 
from datetime import datetime, timedelta 
import re 

logger = logging.getLogger(__name__)

# --- Importações para erpbrasil.edoc ---
NFeServiceERPBrasil = None 
# ConfiguracaoEdocERPBrasil não é mais necessária se passarmos os parâmetros diretamente
# TransmissaoSOAPERPBrasil também não é instanciada separadamente se NFeServiceERPBrasil lida com isso

try:
    from erpbrasil.edoc.nfe import NFe as NFeServiceERPBrasil 
    logger.info("Componente NFe de erpbrasil.edoc importado com sucesso.")
except ImportError as e_erp:
    logger.error(f"Erro CRÍTICO ao importar NFe de erpbrasil.edoc: {str(e_erp)}. Funcionalidades de NF-e podem ser afetadas.")
    NFeServiceERPBrasil = None 

# --- Importações dos Bindings da nfelib e xsdata via fiscal.compat ---
# Usado para parsear a resposta XML se erpbrasil.edoc não fornecer um JSON estruturado completo,
# ou para montar o XML de envio para log/debug, se os bindings estiverem disponíveis.
TRetConsCad = None
XML_PARSER = None
TConsCad = None    
TUfCons = None     
XML_SERIALIZER_local = None 

try:
    from .compat import ( 
        # Não precisamos mais de ConfiguracaoEdocERPBrasil daqui
        TRetConsCadNfelib as TRetConsCad, 
        XML_PARSER_Nfelib as XML_PARSER,   
        TConsCadNfelib as TConsCad,       
        TUfConsNfelib as TUfCons,         
        XML_SERIALIZER_Nfelib_local as XML_SERIALIZER_local 
    )
    if TConsCad: 
        logger.info("Bindings de Consulta Cadastro e Parser/Serializer XML importados via fiscal.compat.")
    else:
        logger.warning("Bindings TConsCadNfelib não foram carregados via fiscal.compat. Montagem manual do XML de consulta não será possível.")
    
except ImportError as e_compat_serv:
    logger.warning(f"Aviso: Erro ao importar componentes de fiscal.compat para Consulta Cadastro: {e_compat_serv}. O parsing/montagem manual do XML de retorno pode não funcionar.")


class EmissorNFeService:

    @staticmethod
    def _limpar_documento(doc):
        return re.sub(r'[^0-9]', '', str(doc or ''))

    @staticmethod
    def _preparar_config_direta_nfe(config_servico_dict): 
        """
        Prepara um dicionário de parâmetros para o construtor de NFe da erpbrasil.edoc.
        """
        if not config_servico_dict:
            config_servico_dict = {}
        
        cnpj_emitente = EmissorNFeService._limpar_documento(config_servico_dict.get('cnpj_empresa_emitente'))
        uf_emitente = config_servico_dict.get('uf_sigla_emitente')

        if not config_servico_dict.get('caminho_certificado_a1') or \
           not config_servico_dict.get('senha_certificado_a1') or \
           not uf_emitente:
            # cnpj_emitente é opcional no construtor de NFe se for apenas para consulta
            # mas é bom tê-lo para consistência e outros serviços.
            logger.error("Parâmetros essenciais de configuração do certificado ou UF do emitente em falta.")
            # Poderia levantar um ValueError aqui, mas vamos deixar o construtor de NFe lidar com isso.
        
        params = {
            'certificado_caminho': config_servico_dict.get('caminho_certificado_a1'),
            'certificado_senha': config_servico_dict.get('senha_certificado_a1'),
            'uf': uf_emitente, 
            'ambiente': int(config_servico_dict.get('ambiente_sefaz', 2)), 
        }
        if cnpj_emitente:
            params['empresa_cnpj'] = cnpj_emitente
        
        # Adicionar outros parâmetros opcionais se existirem em config_servico_dict
        # e forem aceites pelo construtor de NFe
        # Ex: 'empresa_razao_social', 'timeout', 'versao' (para o serviço, não o leiaute da NF-e)
        # A erpbrasil.edoc geralmente lida com a versão do serviço internamente.
        
        return params

    @staticmethod
    def consultar_cadastro(config_servico_dict, uf_consulta_sigla, documento):
        retorno = {
            'sucesso': False, 'xml_enviado': None, 'xml_recebido': None,
            'dados_processados': None, 'erro': 'Serviço de consulta não pôde ser inicializado ou NFeServiceERPBrasil não disponível.'
        }

        if not NFeServiceERPBrasil:
            logger.error("Classe NFe de erpbrasil.edoc não está disponível.")
            return retorno
        
        try:
            direct_config_params = EmissorNFeService._preparar_config_direta_nfe(config_servico_dict)
            nfe_service = NFeServiceERPBrasil(**direct_config_params)
            
            doc_limpo = EmissorNFeService._limpar_documento(documento)
            tipo_documento = None
            cnpj_consulta, cpf_consulta, ie_consulta = None, None, None
            
            if len(doc_limpo) == 14: tipo_documento = 'CNPJ'; cnpj_consulta = doc_limpo
            elif len(doc_limpo) == 11: tipo_documento = 'CPF'; cpf_consulta = doc_limpo
            elif 2 <= len(doc_limpo) <= 14: tipo_documento = 'IE'; ie_consulta = doc_limpo
            else:
                retorno['erro'] = "Documento inválido para consulta."
                return retorno

            logger.info(f"Enviando consulta de cadastro via erpbrasil.edoc: UF Consultada={uf_consulta_sigla}, Doc={doc_limpo}, Tipo={tipo_documento}")
            
            if TConsCad and TUfCons and XML_SERIALIZER_local:
                try:
                    dados_consulta_obj = TConsCad.InfCons(
                        xServ='CONS-CAD', 
                        UF=TUfCons(uf_consulta_sigla.upper()),
                        CNPJ=cnpj_consulta, CPF=cpf_consulta, IE=ie_consulta
                    )
                    consulta_obj_nfelib = TConsCad(versao="2.00", infCons=dados_consulta_obj)
                    xml_envio_str = XML_SERIALIZER_local.render(consulta_obj_nfelib)
                    retorno['xml_enviado'] = xml_envio_str
                    logger.info(f"XML de consulta cadastro (nfelib) montado para log: {xml_envio_str}")
                except Exception as e_xml_mont:
                    logger.warning(f"Não foi possível montar o XML de envio para log com nfelib: {e_xml_mont}")
                    retorno['xml_enviado'] = "Falha ao montar XML de envio com nfelib."
            else:
                 retorno['xml_enviado'] = "Bindings TConsCad ou Serializer da nfelib não disponíveis (via compat.py) para montar XML de envio."
                 logger.warning(retorno['xml_enviado'])

            resultado_erpbrasil = nfe_service.consultar_cadastro(
                uf_consulta=uf_consulta_sigla.upper(),
                tipo_documento=tipo_documento,
                documento=doc_limpo
            )
            
            retorno['xml_recebido'] = resultado_erpbrasil.text 
            
            if resultado_erpbrasil.ok and hasattr(resultado_erpbrasil, 'resposta_json') and resultado_erpbrasil.resposta_json:
                dados_retorno_sefaz = resultado_erpbrasil.resposta_json.get('retConsCad', {}).get('infCons', {})
                cStat = dados_retorno_sefaz.get('cStat')
                xMotivo = dados_retorno_sefaz.get('xMotivo')

                if str(cStat) in ['111', '112']: 
                    retorno['sucesso'] = True
                    infCad_list_original = dados_retorno_sefaz.get('infCad', [])
                    if not isinstance(infCad_list_original, list): 
                        infCad_list_original = [infCad_list_original] if infCad_list_original else []
                        
                    retorno['dados_processados'] = {
                        'cStat': cStat, 'xMotivo': xMotivo,
                        'UF': dados_retorno_sefaz.get('UF'), 'dhCons': dados_retorno_sefaz.get('dhCons'),
                        'infCad': infCad_list_original 
                    }
                else:
                    retorno['sucesso'] = False
                    retorno['erro'] = f"SEFAZ: {cStat} - {xMotivo}"
                    retorno['dados_processados'] = dados_retorno_sefaz 
            elif hasattr(resultado_erpbrasil, 'resposta_json'): 
                retorno['erro'] = resultado_erpbrasil.resposta_json.get('error', f'Erro na comunicação com a SEFAZ (status: {resultado_erpbrasil.status_code}).')
                retorno['dados_processados'] = resultado_erpbrasil.resposta_json
            else: 
                if resultado_erpbrasil.text and TRetConsCad and XML_PARSER:
                    try:
                        logger.info("Tentando parsear XML de retorno da consulta cadastro com nfelib (via compat)...")
                        resposta_sefaz_obj_nfelib = XML_PARSER.from_string(resultado_erpbrasil.text, TRetConsCad)
                        # Implementar lógica para extrair dados de resposta_sefaz_obj_nfelib para retorno['dados_processados']
                        # Exemplo:
                        # if hasattr(resposta_sefaz_obj_nfelib, 'infCons'):
                        #     inf_cons = resposta_sefaz_obj_nfelib.infCons
                        #     # ... (extrair cStat, xMotivo, infCad) ...
                        #     retorno['dados_processados'] = { ... }
                        #     if str(getattr(inf_cons, 'cStat', '')) in ['111', '112']:
                        #         retorno['sucesso'] = True
                        #     else:
                        #         retorno['erro'] = f"SEFAZ (nfelib): {getattr(inf_cons, 'cStat', '')} - {getattr(inf_cons, 'xMotivo', '')}"
                        logger.warning("Parsing com nfelib bem-sucedido, mas mapeamento para dados_processados não totalmente implementado.")

                    except Exception as e_parse:
                        logger.error(f"Erro ao parsear XML de resposta da consulta cadastro com nfelib: {e_parse}")
                if not retorno.get('sucesso') and not retorno.get('erro'): # Se ainda não houve sucesso nem erro definido
                     retorno['erro'] = f"Resposta da SEFAZ não pôde ser processada (sem JSON e parser nfelib indisponível/falhou, status: {resultado_erpbrasil.status_code})."
        
        except Exception as e:
            logger.error(f"Exceção ao consultar cadastro SEFAZ para {documento} na UF {uf_consulta_sigla}: {str(e)}", exc_info=True)
            retorno['sucesso'] = False
            retorno['erro'] = f"Erro de sistema durante a consulta: {str(e)}"
        return retorno

    @staticmethod
    def emitir(nota_fiscal_instance):
        logger.info(f"Tentando emitir NF {nota_fiscal_instance.numero} via erpbrasil.edoc")
        if not NFeServiceERPBrasil:
            logger.error("Componente NFeServiceERPBrasil não disponível para emissão.")
            return {'sucesso': False, 'erro': "Componente NFeServiceERPBrasil não disponível."}

        try:
            config_dict = nota_fiscal_instance.get_configuracao_servico()
            direct_config_params = EmissorNFeService._preparar_config_direta_nfe(config_dict)
            nfe_service = NFeServiceERPBrasil(**direct_config_params)
            
            nfe_data_obj_nfelib = nota_fiscal_instance.to_nfelib() 
            if not nfe_data_obj_nfelib:
                return {'sucesso': False, 'erro': 'Falha ao gerar objeto de dados da NF-e com nfelib.'}

            logger.info(f"Enviando NF-e {nota_fiscal_instance.numero} para SEFAZ...")
            resultado_emissao = nfe_service.enviar_documento(nfe_data_obj_nfelib) 
            
            if resultado_emissao.sucesso:
                nota_fiscal_instance.status = 'A' 
                nota_fiscal_instance.protocolo = resultado_emissao.protocolo
                nota_fiscal_instance.chave = resultado_emissao.chave_acesso 
                nota_fiscal_instance.xml_gerado = resultado_emissao.xml_proc_nfe 
                nota_fiscal_instance.motivo_erro = resultado_emissao.motivo 
                nota_fiscal_instance.save()
                return {
                    'sucesso': True, 'protocolo': nota_fiscal_instance.protocolo,
                    'chave': nota_fiscal_instance.chave, 'xml': nota_fiscal_instance.xml_gerado,
                    'motivo': resultado_emissao.motivo
                }
            else:
                nota_fiscal_instance.status = 'R' 
                nota_fiscal_instance.motivo_erro = resultado_emissao.motivo
                nota_fiscal_instance.save()
                return {
                    'sucesso': False, 
                    'erro': resultado_emissao.motivo, 
                    'xml_enviado': getattr(resultado_emissao, 'xml_enviado', None), 
                    'xml_recebido': resultado_emissao.text 
                }

        except Exception as e:
            logger.error(f"Exceção ao emitir NF-e {nota_fiscal_instance.numero}: {str(e)}", exc_info=True)
            nota_fiscal_instance.status = 'R'
            nota_fiscal_instance.motivo_erro = str(e)
            nota_fiscal_instance.save()
            return {'sucesso': False, 'erro': f"Erro de sistema durante a emissão: {str(e)}"}


    @staticmethod
    def consultar_status(chave_nfe, config_servico_dict): 
        logger.info(f"Consultando status da NF-e {chave_nfe} via erpbrasil.edoc")
        if not NFeServiceERPBrasil:
            return {'sucesso': False, 'erro': "Componente NFeServiceERPBrasil não disponível."}
        try:
            direct_config_params = EmissorNFeService._preparar_config_direta_nfe(config_servico_dict)
            nfe_service = NFeServiceERPBrasil(**direct_config_params)
            resultado = nfe_service.consultar_documento(chave_nfe)

            if resultado.ok and hasattr(resultado, 'resposta_json') and resultado.resposta_json:
                dados_retorno = resultado.resposta_json.get('retConsSitNFe', {}).get('protNFe', {}).get('infProt', {})
                if not isinstance(dados_retorno, dict): 
                    dados_retorno = dados_retorno[0] if dados_retorno else {}
                cStat = dados_retorno.get('cStat')
                xMotivo = dados_retorno.get('xMotivo')
                return {'sucesso': True, 'status': cStat, 'motivo': xMotivo, 'xml_recebido': resultado.text}
            else:
                erro_msg = "Resposta da SEFAZ em formato inesperado ou erro na consulta."
                if hasattr(resultado, 'resposta_json') and resultado.resposta_json:
                    erro_msg = resultado.resposta_json.get('error', erro_msg)
                return {'sucesso': False, 'erro': erro_msg, 'xml_recebido': resultado.text}
        except Exception as e:
            logger.error(f"Exceção ao consultar status da NF-e {chave_nfe}: {str(e)}", exc_info=True)
            return {'sucesso': False, 'erro': f"Erro de sistema: {str(e)}"}
            
    @staticmethod
    def cancelar(nota_fiscal_instance, justificativa, config_servico_dict): 
        logger.info(f"Tentando cancelar NF {nota_fiscal_instance.numero} via erpbrasil.edoc")
        if not NFeServiceERPBrasil:
            return {'sucesso': False, 'erro': "Componente NFeServiceERPBrasil não disponível."}
        try:
            direct_config_params = EmissorNFeService._preparar_config_direta_nfe(config_servico_dict)
            nfe_service = NFeServiceERPBrasil(**direct_config_params)

            resultado = nfe_service.cancelar_documento(
                chave=nota_fiscal_instance.chave,
                protocolo_autorizacao=nota_fiscal_instance.protocolo,
                justificativa=justificativa
            )

            if resultado.sucesso:
                nota_fiscal_instance.status = 'C' 
                nota_fiscal_instance.motivo_erro = resultado.motivo 
                nota_fiscal_instance.save()
                return {'sucesso': True, 'protocolo': resultado.protocolo, 'motivo': resultado.motivo, 'xml_recebido': resultado.text}
            else:
                return {'sucesso': False, 'erro': resultado.motivo, 'xml_recebido': resultado.text}

        except Exception as e:
            logger.error(f"Exceção ao cancelar NF-e {nota_fiscal_instance.numero}: {str(e)}", exc_info=True)
            return {'sucesso': False, 'erro': f"Erro de sistema: {str(e)}"}