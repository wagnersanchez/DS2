# djangosige/apps/fiscal/views/processador_nf.py
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
#from pynfe.entidades import (Destinatario, Emitente, NotaFiscal as NFePy,
#                             NotaFiscalProduto, Produto as ProdutoNFe,
#                             Transportadora)
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.comunicacao import ComunicacaoSefaz
from pynfe.processamento.serializacao import SerializacaoXML
#from pynfe.utils import danfe
#from pynfe.entidades.destinatario import Destinatario
from pynfe.entidades.emitente import Emitente
from pynfe.entidades.notafiscal import NotaFiscal as NFePy
from pynfe.entidades.notafiscal import NotaFiscalProduto
from pynfe.entidades.produto import Produto as ProdutoNFe
from pynfe.entidades.transportadora import Transportadora


from pynfe.entidades.cliente import Cliente as Destinatario








from brazilfiscalreport.danfe import Danfe
from pynfe.utils.flags import (CODIGO_BRASIL, CODIGOS_ESTADOS, NAMESPACE_NFE,
                              TIPOS_DOCUMENTO, VERSAO_PADRAO, VERSAO_QRCODE)
from pynfe.utils.flags import CODIGO_BRASIL

from pynfe.processamento.comunicacao import ComunicacaoSefaz
#Importar entidades de seus submódulos específicos
#from pynfe.entidades.nota import NotaFiscal as NFePy, NotaFiscalProduto, Totalizacao, Imposto # Exemplo
#from pynfe.entidades.pessoa import Emitente, Destinatario # Importa Emitente e Destinatario de pessoa
#from pynfe.entidades.produto import Produto as ProdutoNFe # Produto de produto


from djangosige.apps.cadastro.models import Cliente, Empresa, Fornecedor, Produto
from djangosige.apps.fiscal.models import (ConfiguracaoNotaFiscal,
                                          ErrosValidacaoNotaFiscal,
                                          NotaFiscalEntrada, NotaFiscalSaida,
                                          #ParcelaNotaFiscal,
                                          RespostaSefazNotaFiscal)

try:
    # Importa Pagamento de Vendas e renomeia para evitar conflito
    from djangosige.apps.vendas.models import PedidoVenda, ItensVenda, CondicaoPagamento, Pagamento as PagamentoVenda
except ImportError:
    print("AVISO: Modelos de Vendas não encontrados.")
    PedidoVenda = None; ItensVenda = None; CondicaoPagamento = None; PagamentoVenda = None

try:
    # Importa Pagamento de Compras e renomeia
    from djangosige.apps.compras.models import PedidoCompra, ItensCompra, Pagamento as PagamentoCompra
except ImportError:
    print("AVISO: Modelos de Compras não encontrados.")
    PedidoCompra = None; ItensCompra = None; PagamentoCompra = None
# --- Fim Imports Models ---

logger = logging.getLogger(__name__)


class ProcessadorNotaFiscal:
    """Classe completa para processamento de NF-e com PyNFe"""

    def __init__(self):
        self.conf_nfe = None
        self.certificado = None
        self.erros = []
        self.ultimo_protocolo = None

    def _carregar_configuracao(self):
        """Carrega a configuração de NF-e do banco de dados"""
        try:
            self.conf_nfe = ConfiguracaoNotaFiscal.objects.first()
            if not self.conf_nfe:
                raise ValidationError('Configuração de NF-e não encontrada')
            return True
        except Exception as e:
            self._adicionar_erro(f"Erro ao carregar configuração: {str(e)}")
            return False

    def _carregar_certificado(self):
        """Carrega o certificado digital A1"""
        try:
            if not self.conf_nfe or not self.conf_nfe.arquivo_certificado_a1:
                raise ValidationError('Certificado não configurado')

            cert_path = Path(self.conf_nfe.arquivo_certificado_a1.path)
            if not cert_path.exists():
                raise ValidationError('Arquivo do certificado não encontrado')

            with open(cert_path, 'rb') as cert_file:
                self.certificado = {
                    'cert': cert_file.read(),
                    'key': self.conf_nfe.senha_certificado,
                    'path': str(cert_path)
                }
            return True
        except Exception as e:
            self._adicionar_erro(f"Erro ao carregar certificado: {str(e)}")
            return False

    def _adicionar_erro(self, mensagem):
        """Registra um erro no processamento"""
        self.erros.append(mensagem)
        logger.error(mensagem)

    def _montar_emitente(self, nota: NotaFiscalSaida) -> Emitente:
        """Monta o objeto emitente para a NF-e"""
        empresa = nota.emit_saida
        endereco = empresa.endereco_padrao

        return Emitente(
            razao_social=empresa.nome_razao_social,
            cnpj=empresa.cpf_cnpj_apenas_digitos,
            inscricao_estadual=empresa.inscricao_estadual,
            inscricao_municipal=empresa.inscricao_municipal,
            cnae_fiscal=empresa.cnae,
            endereco_logradouro=endereco.logradouro,
            endereco_numero=endereco.numero,
            endereco_complemento=endereco.complemento,
            endereco_bairro=endereco.bairro,
            endereco_municipio=endereco.municipio,
            endereco_uf=endereco.uf,
            endereco_cep=endereco.cep,
            endereco_pais=CODIGOS_BRASIL,
            telefone=empresa.telefone_padrao,
        )

    def _montar_destinatario(self, nota: NotaFiscalSaida) -> Destinatario:
        """Monta o objeto destinatário para a NF-e"""
        cliente = nota.dest_saida
        endereco = cliente.endereco_padrao

        return Destinatario(
            razao_social=cliente.nome_razao_social,
            tipo_documento='CNPJ' if cliente.tipo_pessoa == 'PJ' else 'CPF',
            numero_documento=cliente.cpf_cnpj_apenas_digitos,
            inscricao_estadual=cliente.inscricao_estadual,
            endereco_logradouro=endereco.logradouro,
            endereco_numero=endereco.numero,
            endereco_complemento=endereco.complemento,
            endereco_bairro=endereco.bairro,
            endereco_municipio=endereco.municipio,
            endereco_uf=endereco.uf,
            endereco_cep=endereco.cep,
            endereco_pais=CODIGOS_BRASIL,
            telefone=cliente.telefone_padrao,
            email=cliente.email_padrao,
        )

    def _montar_produtos(self, nota: NotaFiscalSaida) -> list[NotaFiscalProduto]:
        """Monta os produtos da NF-e"""
        produtos = []
        for item in nota.itens.all():
            produto = item.produto
            produtos.append(NotaFiscalProduto(
                codigo=produto.codigo,
                descricao=produto.descricao,
                ncm=produto.ncm,
                cfop=item.cfop,
                unidade_comercial=produto.unidade.sigla,
                quantidade_comercial=item.quantidade,
                valor_unitario_comercial=item.valor_unitario,
                valor_total=item.valor_total,
                unidade_tributavel=produto.unidade.sigla,
                quantidade_tributavel=item.quantidade,
                valor_unitario_tributavel=item.valor_unitario,
                numero_pedido=nota.numero,
                numero_item=item.id,
            ))
        return produtos

    @transaction.atomic
    def emitir_nfe(self, nota: NotaFiscalSaida) -> bool:
        """
        Emite uma NF-e no ambiente da SEFAZ
        
        Args:
            nota: Instância de NotaFiscalSaida a ser emitida
            
        Returns:
            bool: True se a emissão foi bem-sucedida, False caso contrário
        """
        try:
            if not self._carregar_configuracao() or not self._carregar_certificado():
                return False

            if nota.status != NotaFiscalSaida.STATUS_EM_DIGITACAO:
                raise ValidationError('Nota fiscal não está em digitação')

            nfe_py = NFePy(
                emitente=self._montar_emitente(nota),
                destinatario=self._montar_destinatario(nota),
                produtos=self._montar_produtos(nota),
                uf=nota.emit_saida.endereco_padrao.uf,
                natureza_operacao=nota.natureza_operacao.descricao,
                forma_pagamento=nota.forma_pagamento,
                modelo='55' if nota.modelo == '55' else '65',
                serie=nota.serie,
                numero_nf=nota.numero,
                data_emissao=timezone.now(),
                data_saida_entrada=timezone.now(),
                tipo_documento='1',
                municipio=nota.emit_saida.endereco_padrao.municipio,
                tipo_impressao_danfe='1',
                forma_emissao='1',
                cliente_final='1' if nota.consumidor_final else '0',
                indicador_destino='1' if nota.indicador_destino else '0',
                indicador_presencial='1' if nota.presencial else '0',
                finalidade_emissao='1',
                processo_emissao='0',
            )

            serializador = SerializacaoXML(_schema='nfe_v4_00')
            xml = serializador.gerar(nfe_py)

            assinador = AssinaturaA1(self.certificado['path'], self.certificado['key'])
            xml_assinado = assinador.assinar(xml)

            uf = nota.emit_saida.endereco_padrao.uf
            homologacao = self.conf_nfe.ambiente == '2'
            con = ComunicacaoSefaz(uf, self.certificado['cert'], 
                                 self.certificado['key'], homologacao)
            
            envio = con.enviar(xml_assinado)

            if envio.resposta.cStat.valor == '100':
                nota.chave = envio.resposta.infRec.chNFe.valor
                nota.protocolo = envio.resposta.infRec.nProt.valor
                nota.status = NotaFiscalSaida.STATUS_AUTORIZADA
                nota.xml_assinado = xml_assinado
                nota.data_autorizacao = timezone.now()
                nota.save()
                self.ultimo_protocolo = nota.protocolo
                return True
            else:
                raise ValidationError(f"SEFAZ rejeitou a NF-e: {envio.resposta.xMotivo.valor}")

        except Exception as e:
            self._adicionar_erro(f"Erro ao emitir NF-e: {str(e)}")
            nota.status = NotaFiscalSaida.STATUS_ERRO_EMISSAO
            nota.save()
            return False

    @transaction.atomic
    def cancelar_nfe(self, nota: NotaFiscalSaida, justificativa: str) -> bool:
        """
        Cancela uma NF-e autorizada
        
        Args:
            nota: Instância de NotaFiscalSaida a ser cancelada
            justificativa: Texto com a justificativa do cancelamento
            
        Returns:
            bool: True se o cancelamento foi bem-sucedido, False caso contrário
        """
        try:
            if not self._carregar_configuracao() or not self._carregar_certificado():
                return False

            if nota.status != NotaFiscalSaida.STATUS_AUTORIZADA:
                raise ValidationError('Apenas notas autorizadas podem ser canceladas')

            if len(justificativa) < 15:
                raise ValidationError('Justificativa deve ter pelo menos 15 caracteres')

            uf = nota.emit_saida.endereco_padrao.uf
            homologacao = self.conf_nfe.ambiente == '2'
            con = ComunicacaoSefaz(uf, self.certificado['cert'], 
                                 self.certificado['key'], homologacao)
            
            cancelamento = con.cancelar_nota(
                chave=nota.chave,
                protocolo=nota.protocolo,
                justificativa=justificativa
            )

            if cancelamento.resposta.infEvento.cStat.valor == '135':
                nota.status = NotaFiscalSaida.STATUS_CANCELADA
                nota.justificativa_cancelamento = justificativa
                nota.data_cancelamento = timezone.now()
                nota.save()
                return True
            else:
                raise ValidationError(
                    f"SEFAZ rejeitou o cancelamento: {cancelamento.resposta.infEvento.xMotivo.valor}"
                )

        except Exception as e:
            self._adicionar_erro(f"Erro ao cancelar NF-e: {str(e)}")
            return False

    def gerar_danfe(self, nota: NotaFiscalSaida, output_path=None) -> bytes | None:
        """
        Gera o DANFE da NF-e
        
        Args:
            nota: Instância de NotaFiscalSaida
            output_path: Caminho opcional para salvar o PDF
            
        Returns:
            bytes: Conteúdo do PDF gerado ou None em caso de erro
        """
        try:
            if not nota.xml_assinado:
                raise ValidationError('NF-e não possui XML assinado')

            danfe_config = {
                'logo': None,
                'formato': 'A4',
                'papel': 'A4',
                'margem_esquerda': 5,
                'margem_direita': 5,
                'margem_superior': 5,
                'margem_inferior': 5,
                'resolucao': 72,
                'font_size': 8,
                'observacoes': '',
            }

            danfe_pdf = danfe.gerar_danfe(
                xml=nota.xml_assinado,
                **danfe_config
            )

            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(danfe_pdf)

            return danfe_pdf

        except Exception as e:
            self._adicionar_erro(f"Erro ao gerar DANFE: {str(e)}")
            return None

    def consultar_status_sefaz(self) -> dict:
        """
        Consulta o status do serviço da SEFAZ
        
        Returns:
            dict: Dicionário com o status do serviço
        """
        try:
            if not self._carregar_configuracao() or not self._carregar_certificado():
                return {'status': 'erro', 'mensagem': 'Configuração não carregada'}

            uf = self.conf_nfe.empresa.endereco_padrao.uf
            homologacao = self.conf_nfe.ambiente == '2'
            con = ComunicacaoSefaz(uf, self.certificado['cert'], 
                                 self.certificado['key'], homologacao)
            
            status = con.consultar_status_servico()
            return {
                'status': 'sucesso',
                'data': status.resposta.infRec.dhRecbto.valor,
                'mensagem': status.resposta.xMotivo.valor,
                'tempo_medio': status.resposta.infRec.tMed.valor if hasattr(status.resposta.infRec, 'tMed') else None,
            }

        except Exception as e:
            self._adicionar_erro(f"Erro ao consultar status SEFAZ: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

    def consultar_nota(self, chave: str) -> dict:
        """
        Consulta uma NF-e específica na SEFAZ
        
        Args:
            chave: Chave de acesso da NF-e (44 dígitos)
            
        Returns:
            dict: Dicionário com o status da nota
        """
        try:
            if not self._carregar_configuracao() or not self._carregar_certificado():
                return {'status': 'erro', 'mensagem': 'Configuração não carregada'}

            uf = chave[0:2]
            homologacao = self.conf_nfe.ambiente == '2'
            con = ComunicacaoSefaz(uf, self.certificado['cert'], 
                                 self.certificado['key'], homologacao)
            
            resultado = con.consultar_nota(chave)
            
            if resultado.resposta.cStat.valor == '100':
                return {
                    'status': 'autorizada',
                    'protocolo': resultado.resposta.protNFe.infProt.nProt.valor,
                    'data_autorizacao': resultado.resposta.protNFe.infProt.dhRecbto.valor,
                    'xml': ET.tostring(resultado.resposta.getchildren()[0], encoding='unicode')
                }
            elif resultado.resposta.cStat.valor == '101':
                return {
                    'status': 'cancelada',
                    'protocolo_cancelamento': resultado.resposta.retCancNFe.infCanc.nProt.valor,
                    'data_cancelamento': resultado.resposta.retCancNFe.infCanc.dhRecbto.valor
                }
            else:
                return {
                    'status': 'erro',
                    'mensagem': resultado.resposta.xMotivo.valor
                }

        except Exception as e:
            self._adicionar_erro(f"Erro ao consultar NF-e: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

    def _parse_decimal(self, element):
        """Converte elemento XML para Decimal seguro"""
        if element is not None and element.text:
            try:
                return Decimal(element.text)
            except:
                return Decimal('0.00')
        return Decimal('0.00')

    def _processar_impostos_completos(self, imp, ns, item):
        """Processa todos os impostos com tratamento completo"""
        # ICMS
        icms_node = imp.find('nfe:ICMS', ns)
        if icms_node is not None:
            for tipo in ['nfe:ICMS00', 'nfe:ICMS10', 'nfe:ICMS20', 'nfe:ICMS30',
                        'nfe:ICMS40', 'nfe:ICMS51', 'nfe:ICMS60', 'nfe:ICMS70',
                        'nfe:ICMS90', 'nfe:ICMSSN101', 'nfe:ICMSSN102', 'nfe:ICMSSN201',
                        'nfe:ICMSSN202', 'nfe:ICMSSN500', 'nfe:ICMSSN900']:
                
                icms = icms_node.find(tipo, ns)
                if icms is not None:
                    item.icms_cst = icms.find('nfe:CST', ns).text if icms.find('nfe:CST', ns) is not None else None
                    item.icms_csosn = icms.find('nfe:CSOSN', ns).text if icms.find('nfe:CSOSN', ns) is not None else None
                    item.icms_base = self._parse_decimal(icms.find('nfe:vBC', ns))
                    item.icms_valor = self._parse_decimal(icms.find('nfe:vICMS', ns))
                    item.icms_aliquota = self._parse_decimal(icms.find('nfe:pICMS', ns))
                    
                    if tipo in ['nfe:ICMS20', 'nfe:ICMS70']:
                        item.icms_valor_desconto = self._parse_decimal(icms.find('nfe:vICMSDeson', ns))
                        item.icms_motivo_desoneracao = icms.find('nfe:motDesICMS', ns).text if icms.find('nfe:motDesICMS', ns) is not None else None
                    
                    if tipo in ['nfe:ICMS10', 'nfe:ICMS30', 'nfe:ICMS70', 'nfe:ICMS90']:
                        item.icms_st_base = self._parse_decimal(icms.find('nfe:vBCST', ns))
                        item.icms_st_valor = self._parse_decimal(icms.find('nfe:vICMSST', ns))
                    
                    if tipo == 'nfe:ICMS60':
                        item.icms_st_valor_retido = self._parse_decimal(icms.find('nfe:vBCSTRet', ns))
                        item.icms_st_valor = self._parse_decimal(icms.find('nfe:vICMSSTRet', ns))
                    
                    break

        # IPI
        ipi_node = imp.find('nfe:IPI', ns)
        if ipi_node is not None:
            for tipo in ['nfe:IPITrib', 'nfe:IPINT']:
                ipi = ipi_node.find(tipo, ns)
                if ipi is not None:
                    item.ipi_cst = ipi.find('nfe:CST', ns).text if ipi.find('nfe:CST', ns) is not None else None
                    if tipo == 'nfe:IPITrib':
                        item.ipi_base = self._parse_decimal(ipi.find('nfe:vBC', ns))
                        item.ipi_valor = self._parse_decimal(ipi.find('nfe:vIPI', ns))
                        item.ipi_aliquota = self._parse_decimal(ipi.find('nfe:pIPI', ns))
                    break

        # PIS
        pis_node = imp.find('nfe:PIS', ns)
        if pis_node is not None:
            for tipo in ['nfe:PISAliq', 'nfe:PISQtde', 'nfe:PISNT', 'nfe:PISOutr']:
                pis = pis_node.find(tipo, ns)
                if pis is not None:
                    item.pis_cst = pis.find('nfe:CST', ns).text if pis.find('nfe:CST', ns) is not None else None
                    
                    if tipo == 'nfe:PISAliq':
                        item.pis_base = self._parse_decimal(pis.find('nfe:vBC', ns))
                        item.pis_valor = self._parse_decimal(pis.find('nfe:vPIS', ns))
                        item.pis_aliquota = self._parse_decimal(pis.find('nfe:pPIS', ns))
                    
                    elif tipo == 'nfe:PISQtde':
                        item.pis_quantidade = self._parse_decimal(pis.find('nfe:qBCProd', ns))
                        item.pis_valor = self._parse_decimal(pis.find('nfe:vPIS', ns))
                        item.pis_aliquota = self._parse_decimal(pis.find('nfe:vAliqProd', ns))
                    
                    elif tipo == 'nfe:PISOutr':
                        item.pis_base = self._parse_decimal(pis.find('nfe:vBC', ns))
                        item.pis_valor = self._parse_decimal(pis.find('nfe:vPIS', ns))
                        item.pis_aliquota = self._parse_decimal(pis.find('nfe:pPIS', ns))
                        item.pis_valor_reais = self._parse_decimal(pis.find('nfe:vPIS', ns))
                    
                    break

        # COFINS
        cofins_node = imp.find('nfe:COFINS', ns)
        if cofins_node is not None:
            for tipo in ['nfe:COFINSAliq', 'nfe:COFINSQtde', 'nfe:COFINSNT', 'nfe:COFINSOutr']:
                cofins = cofins_node.find(tipo, ns)
                if cofins is not None:
                    item.cofins_cst = cofins.find('nfe:CST', ns).text if cofins.find('nfe:CST', ns) is not None else None
                    
                    if tipo == 'nfe:COFINSAliq':
                        item.cofins_base = self._parse_decimal(cofins.find('nfe:vBC', ns))
                        item.cofins_valor = self._parse_decimal(cofins.find('nfe:vCOFINS', ns))
                        item.cofins_aliquota = self._parse_decimal(cofins.find('nfe:pCOFINS', ns))
                    
                    elif tipo == 'nfe:COFINSQtde':
                        item.cofins_quantidade = self._parse_decimal(cofins.find('nfe:qBCProd', ns))
                        item.cofins_valor = self._parse_decimal(cofins.find('nfe:vCOFINS', ns))
                        item.cofins_aliquota = self._parse_decimal(cofins.find('nfe:vAliqProd', ns))
                    
                    elif tipo == 'nfe:COFINSOutr':
                        item.cofins_base = self._parse_decimal(cofins.find('nfe:vBC', ns))
                        item.cofins_valor = self._parse_decimal(cofins.find('nfe:vCOFINS', ns))
                        item.cofins_aliquota = self._parse_decimal(cofins.find('nfe:pCOFINS', ns))
                        item.cofins_valor_reais = self._parse_decimal(cofins.find('nfe:vCOFINS', ns))
                    
                    break

        # II (Imposto de Importação)
        ii_node = imp.find('nfe:II', ns)
        if ii_node is not None:
            item.ii_base = self._parse_decimal(ii_node.find('nfe:vBC', ns))
            item.ii_valor = self._parse_decimal(ii_node.find('nfe:vII', ns))
            item.ii_desp_aduaneira = self._parse_decimal(ii_node.find('nfe:vDespAdu', ns))
            item.ii_iof = self._parse_decimal(ii_node.find('nfe:vIOF', ns))

        # DIFAL (para operações interestaduais)
        icms_uf_dest = imp.find('nfe:ICMSUFDest', ns)
        if icms_uf_dest is not None:
            item.difal_base = self._parse_decimal(icms_uf_dest.find('nfe:vBCUFDest', ns))
            item.difal_valor = self._parse_decimal(icms_uf_dest.find('nfe:vICMSUFDest', ns))
            item.difal_valor_origem = self._parse_decimal(icms_uf_dest.find('nfe:vICMSUFRemet', ns))

        # FCP (Fundo de Combate à Pobreza)
        fcp_node = imp.find('nfe:FCP', ns)
        if fcp_node is not None:
            item.fcp_valor = self._parse_decimal(fcp_node.find('nfe:vFCP', ns))

    def importar_xml(self, arquivo_xml, tipo='entrada'):
        """
        Importa uma NF-e a partir de XML
        
        Args:
            arquivo_xml: Caminho do arquivo XML ou objeto file-like
            tipo: 'entrada' ou 'saida'
            
        Returns:
            NotaFiscal: Instância da nota importada
            
        Raises:
            ValidationError: Em caso de erro na importação
        """
        try:
            tree = ET.parse(arquivo_xml)
            root = tree.getroot()
            ns = {'nfe': NAMESPACE_NFE}
            inf_nfe = root.find('nfe:infNFe', ns)
            
            if not inf_nfe:
                raise ValidationError('Arquivo XML não é uma NF-e válida')

            chave = inf_nfe.get('Id')[3:]
            
            if tipo == 'entrada':
                if NotaFiscalEntrada.objects.filter(chave=chave).exists():
                    raise ValidationError('NF-e de entrada já importada')
                return self._importar_nota_entrada(root, inf_nfe, ns)
            else:
                if NotaFiscalSaida.objects.filter(chave=chave).exists():
                    raise ValidationError('NF-e de saída já emitida')
                return self._importar_nota_saida(root, inf_nfe, ns)
                
        except Exception as e:
            self._adicionar_erro(f"Erro ao importar XML: {str(e)}")
            raise

    def _importar_nota_entrada(self, root, inf_nfe, ns):
        """Processa nota fiscal de entrada"""
        nota = NotaFiscalEntrada()
        
        # Extrai dados do emitente (fornecedor)
        emitente = inf_nfe.find('nfe:emit', ns)
        cnpj_emitente = emitente.find('nfe:CNPJ', ns).text
        
        fornecedor = Fornecedor.objects.filter(cpf_cnpj_apenas_digitos=cnpj_emitente).first()
        if not fornecedor:
            raise ValidationError('Emitente do XML não corresponde a nenhum fornecedor cadastrado')

        # Extrai dados do destinatário (nossa empresa)
        dest = inf_nfe.find('nfe:dest', ns)
        cnpj_dest = dest.find('nfe:CNPJ', ns).text
        
        empresa = Empresa.objects.filter(cpf_cnpj_apenas_digitos=cnpj_dest).first()
        if not empresa:
            raise ValidationError('Destinatário do XML não corresponde a nenhuma empresa cadastrada')

        # Extrai dados básicos
        ide = inf_nfe.find('nfe:ide', ns)
        total = inf_nfe.find('nfe:total', ns)
        cobr = inf_nfe.find('nfe:cobr', ns)

        # Preenche dados da nota
        nota.emit_entrada = fornecedor
        nota.dest_entrada = empresa
        nota.modelo = ide.find('nfe:mod', ns).text
        nota.serie = ide.find('nfe:serie', ns).text
        nota.numero = ide.find('nfe:nNF', ns).text
        nota.chave = inf_nfe.get('Id')[3:]
        nota.data_emissao = datetime.strptime(ide.find('nfe:dhEmi', ns).text, '%Y-%m-%dT%H:%M:%S%z')
        nota.status = NotaFiscalEntrada.STATUS_AUTORIZADA
        nota.xml_assinado = ET.tostring(root, encoding='unicode')
        nota.valor_total = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vNF', ns))
        nota.valor_desconto = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vDesc', ns))
        nota.valor_frete = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vFrete', ns))
        nota.valor_seguro = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vSeg', ns))
        nota.valor_outros = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vOutro', ns))
        
        # Salva a nota
        nota.save()
        
        # Processa formas de pagamento
        if cobr is not None:
            fatura = cobr.find('nfe:fat', ns)
            if fatura is not None:
                nota.valor_fatura = self._parse_decimal(fatura.find('nfe:vLiq', ns))
                nota.numero_fatura = fatura.find('nfe:nFat', ns).text
            
            for dup in cobr.findall('nfe:dup', ns):
                ParcelaNotaFiscal.objects.create(
                    nota=nota,
                    numero=dup.find('nfe:nDup', ns).text,
                    vencimento=datetime.strptime(dup.find('nfe:dVenc', ns).text, '%Y-%m-%d').date(),
                    valor=self._parse_decimal(dup.find('nfe:vDup', ns)),
                    forma_pagamento='99'  # 99=Outros
                )

        # Processa produtos e impostos
        dets = inf_nfe.findall('nfe:det', ns)
        for det in dets:
            prod = det.find('nfe:prod', ns)
            imp = det.find('nfe:imposto', ns)
            
            cod_prod = prod.find('nfe:cProd', ns).text
            produto = Produto.objects.filter(codigo=cod_prod).first()
            
            if not produto:
                produto = Produto.objects.create(
                    codigo=cod_prod,
                    descricao=prod.find('nfe:xProd', ns).text,
                    ncm=prod.find('nfe:NCM', ns).text,
                    unidade=prod.find('nfe:uCom', ns).text,
                    valor_unitario=self._parse_decimal(prod.find('nfe:vUnCom', ns)),
                )
            
            item = nota.itens.create(
                produto=produto,
                quantidade=self._parse_decimal(prod.find('nfe:qCom', ns)),
                valor_unitario=self._parse_decimal(prod.find('nfe:vUnCom', ns)),
                valor_total=self._parse_decimal(prod.find('nfe:vProd', ns)),
                cfop=prod.find('nfe:CFOP', ns).text,
                informacoes_adicionais=prod.find('nfe:xProd', ns).text,
            )
            
            if imp is not None:
                self._processar_impostos_completos(imp, ns, item)
        
        return nota

    def _importar_nota_saida(self, root, inf_nfe, ns):
        """Processa nota fiscal de saída"""
        nota = NotaFiscalSaida()
        
        # Extrai dados do emitente (nossa empresa)
        emitente = inf_nfe.find('nfe:emit', ns)
        cnpj_emitente = emitente.find('nfe:CNPJ', ns).text
        
        empresa = Empresa.objects.filter(cpf_cnpj_apenas_digitos=cnpj_emitente).first()
        if not empresa:
            raise ValidationError('Emitente do XML não corresponde a nenhuma empresa cadastrada')

        # Extrai dados do destinatário (cliente)
        dest = inf_nfe.find('nfe:dest', ns)
        cnpj_dest = dest.find('nfe:CNPJ', ns).text if dest.find('nfe:CNPJ', ns) is not None else None
        cpf_dest = dest.find('nfe:CPF', ns).text if dest.find('nfe:CPF', ns) is not None else None
        
        cliente = None
        if cnpj_dest:
            cliente = Cliente.objects.filter(cpf_cnpj_apenas_digitos=cnpj_dest).first()
        elif cpf_dest:
            cliente = Cliente.objects.filter(cpf_cnpj_apenas_digitos=cpf_dest).first()
        
        if not cliente:
            raise ValidationError('Destinatário do XML não corresponde a nenhum cliente cadastrado')

        # Extrai dados básicos
        ide = inf_nfe.find('nfe:ide', ns)
        total = inf_nfe.find('nfe:total', ns)
        cobr = inf_nfe.find('nfe:cobr', ns)

        # Preenche dados da nota
        nota.emit_saida = empresa
        nota.dest_saida = cliente
        nota.modelo = ide.find('nfe:mod', ns).text
        nota.serie = ide.find('nfe:serie', ns).text
        nota.numero = ide.find('nfe:nNF', ns).text
        nota.chave = inf_nfe.get('Id')[3:]
        nota.data_emissao = datetime.strptime(ide.find('nfe:dhEmi', ns).text, '%Y-%m-%dT%H:%M:%S%z')
        nota.status = NotaFiscalSaida.STATUS_AUTORIZADA
        nota.xml_assinado = ET.tostring(root, encoding='unicode')
        nota.valor_total = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vNF', ns))
        nota.valor_desconto = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vDesc', ns))
        nota.valor_frete = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vFrete', ns))
        nota.valor_seguro = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vSeg', ns))
        nota.valor_outros = self._parse_decimal(total.find('nfe:ICMSTot/nfe:vOutro', ns))
        
        # Salva a nota
        nota.save()
        
        # Processa formas de pagamento
        if cobr is not None:
            fatura = cobr.find('nfe:fat', ns)
            if fatura is not None:
                nota.valor_fatura = self._parse_decimal(fatura.find('nfe:vLiq', ns))
                nota.numero_fatura = fatura.find('nfe:nFat', ns).text
            
            for dup in cobr.findall('nfe:dup', ns):
                ParcelaNotaFiscal.objects.create(
                    nota=nota,
                    numero=dup.find('nfe:nDup', ns).text,
                    vencimento=datetime.strptime(dup.find('nfe:dVenc', ns).text, '%Y-%m-%d').date(),
                    valor=self._parse_decimal(dup.find('nfe:vDup', ns)),
                    forma_pagamento='99'  # 99=Outros
                )

        # Processa produtos e impostos
        dets = inf_nfe.findall('nfe:det', ns)
        for det in dets:
            prod = det.find('nfe:prod', ns)
            imp = det.find('nfe:imposto', ns)
            
            cod_prod = prod.find('nfe:cProd', ns).text
            produto = Produto.objects.filter(codigo=cod_prod).first()
            
            if not produto:
                produto = Produto.objects.create(
                    codigo=cod_prod,
                    descricao=prod.find('nfe:xProd', ns).text,
                    ncm=prod.find('nfe:NCM', ns).text,
                    unidade=prod.find('nfe:uCom', ns).text,
                    valor_unitario=self._parse_decimal(prod.find('nfe:vUnCom', ns)),
                )
            
            item = nota.itens.create(
                produto=produto,
                quantidade=self._parse_decimal(prod.find('nfe:qCom', ns)),
                valor_unitario=self._parse_decimal(prod.find('nfe:vUnCom', ns)),
                valor_total=self._parse_decimal(prod.find('nfe:vProd', ns)),
                cfop=prod.find('nfe:CFOP', ns).text,
                informacoes_adicionais=prod.find('nfe:xProd', ns).text,
            )
            
            if imp is not None:
                self._processar_impostos_completos(imp, ns, item)
        
        return nota