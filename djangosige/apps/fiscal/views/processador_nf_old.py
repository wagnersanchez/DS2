# -*- coding: utf-8 -*-

# Imports Django e Modelos
from decimal import Decimal, InvalidOperation
import os
import re
import traceback # Importar para usar print_exc

from django.utils.dateparse import parse_datetime, parse_date
from django.contrib.auth import get_user_model # Para buscar User padrão se necessário
from django.conf import settings # Para verificar USE_TZ se necessário

# Modelos Fiscais (ajustar import se NotaFiscal for base)
from djangosige.apps.fiscal.models import (
    NotaFiscalSaida, NotaFiscalEntrada, NotaFiscal,
    ConfiguracaoNotaFiscal, AutXML, ErrosValidacaoNotaFiscal,
    RespostaSefazNotaFiscal, NaturezaOperacao, GrupoFiscal,
    ICMS, ICMSUFDest, ICMSSN, IPI, PIS, COFINS
)
# Modelos Cadastro
from djangosige.apps.cadastro.models import (
    COD_UF, PessoaJuridica, PessoaFisica, Fornecedor, Cliente, Empresa, MinhaEmpresa,
    Transportadora, Endereco, Telefone, Produto, Unidade, Pessoa # Adicionado Pessoa se necessário
)
# Modelos Compras e Vendas
from djangosige.apps.compras.models import PedidoCompra, ItensCompra, Pagamento as PagamentoCompra # Verificar Pagamento
from djangosige.apps.vendas.models import PedidoVenda, ItensVenda, Pagamento as PagamentoVenda # Verificar Pagamento

# Modelo de Perfil
from djangosige.apps.login.models import Usuario as UsuarioProfile

# Configurações (se ainda for usado)
# from djangosige.configs.settings import MEDIA_ROOT # Comentado pois não parece usado aqui

# Biblioteca XML
try:
    from lxml import etree
except ImportError:
    print("ERRO CRÍTICO: Biblioteca lxml não encontrada. Instale com: pip install lxml")
    etree = None # Definir como None para evitar erros posteriores se a importação falhar

# Define o namespace padrão da NF-e
NFE_NAMESPACE = 'http://www.portalfiscal.inf.br/nfe'
NSMAP = {'ns': NFE_NAMESPACE} # Usado nas buscas XPath

# --- Funções Auxiliares para Extração com lxml ---

def _get_text(element, xpath_query):
    """Busca um elemento/atributo pelo xpath e retorna seu conteúdo textual (.text ou o próprio valor)."""
    if element is None: return None
    try:
        result = element.xpath(xpath_query, namespaces=NSMAP)
        if result:
            item = result[0]
            if hasattr(item, 'text') and item.text is not None:
                return item.text.strip()
            elif isinstance(item, str):
                return item.strip()
            else:
                return str(item).strip()
    except (IndexError, AttributeError, TypeError): pass
    return None

def _get_decimal(element, xpath_query, default=Decimal('0.00')):
    """Busca texto, converte para Decimal, tratando erros."""
    text = _get_text(element, xpath_query)
    if text:
        try:
            cleaned_text = text.replace('.', '').replace(',', '.')
            value = Decimal(cleaned_text)
            return value.quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError): pass
    return default

def _get_date(element, xpath_query):
    """Busca texto e converte para Date."""
    text = _get_text(element, xpath_query)
    if text:
        try: return parse_date(text.strip())
        except (ValueError, TypeError):
             try: return datetime.strptime(text.strip(), '%d/%m/%Y').date()
             except (ValueError, TypeError): pass
    return None

def _get_datetime(element, xpath_query):
    """Busca texto e converte para Datetime."""
    text = _get_text(element, xpath_query)
    if text:
        try:
            dt = parse_datetime(text.strip())
            return dt
        except (ValueError, TypeError): pass
    return None

def _limpar_numero(text):
     """Remove caracteres não numéricos."""
     if text: return re.sub(r'[^0-9]', '', text)
     return ''

# --- Fim das Funções Auxiliares ---


class ProcessadorNotaFiscal(object):

    def __init__(self):
        self.message = ''
        self.erro = False
        # --- ATRIBUTOS ADICIONADOS PARA DEBUG ---
        self.last_dest_cnpj_xml = None
        self.last_my_comp_cnpj_db = None
        # --- FIM ADIÇÃO ---

    def salvar_mensagem(self, message, erro=False):
        """Salva a última mensagem e o status de erro."""
        print(f"ProcessadorNotaFiscal MSG (Erro={erro}): {message}") # Mantém print para debug
        self.erro = erro
        self.message = message

    # -- Métodos de EMISSÃO, etc. REMOVIDOS/COMENTADOS --

    def importar_xml(self, request):
        """Lê o tipo de NF do XML e chama a função de importação correta."""
        self.salvar_mensagem('')
        # Resetar valores de debug
        self.last_dest_cnpj_xml = None
        self.last_my_comp_cnpj_db = None

        try:
            if not etree: raise ImportError("Biblioteca lxml não está instalada.")
            arquivo_xml = request.FILES.get('arquivo_xml')
            if not arquivo_xml: raise ValueError("Nenhum arquivo XML enviado.")
            try:
                 original_pos = arquivo_xml.tell()
                 parser = etree.XMLParser(remove_blank_text=True)
                 xml_tree = etree.parse(arquivo_xml, parser); root = xml_tree.getroot()
                 arquivo_xml.seek(original_pos) # Volta ao início
            except etree.XMLSyntaxError as e: raise ValueError(f"Erro de sintaxe no XML: {e}")
            except Exception as e: raise ValueError(f"Erro ao ler/parsear XML para verificar tipo: {e}")

            nfe_element = None
            if root.tag == etree.QName(NFE_NAMESPACE, 'NFe'): nfe_element = root
            else: nfe_list = root.xpath('.//ns:NFe', namespaces=NSMAP); nfe_element = nfe_list[0] if nfe_list else None
            if nfe_element is None: raise ValueError("Elemento <NFe> não encontrado.")
            infNFe = nfe_element.xpath('./ns:infNFe', namespaces=NSMAP);
            if not infNFe: raise ValueError("Elemento <infNFe> não encontrado.");
            infNFe = infNFe[0]
            ide = infNFe.xpath('./ns:ide', namespaces=NSMAP)[0]

            tipo_nf = _get_text(ide, './ns:tpNF') # Busca o elemento
            print(f"DEBUG: Tipo de NF encontrado no XML: {tipo_nf}")

            if tipo_nf == '0': # Entrada
                print("DEBUG: Chamando importar_xml_fornecedor (Entrada)...")
                self.importar_xml_fornecedor(request)
            elif tipo_nf == '1': # Saída
                print("DEBUG: Chamando importar_xml_cliente (Saída)...")
                self.importar_xml_cliente(request)
            else: raise ValueError(f"Tipo de NF inválido ou não suportado no XML: {tipo_nf}")

            if not self.erro and not self.message:
                 self.salvar_mensagem("Importação XML concluída.")

        except ValueError as e: self.salvar_mensagem(message=str(e), erro=True)
        except ImportError as e: self.salvar_mensagem(message=str(e), erro=True)
        except Exception as e: traceback.print_exc(); self.salvar_mensagem(message=f"Erro inesperado na importação: {e}", erro=True)


    def importar_xml_cliente(self, request):
        """Importa NF-e de SAÍDA (tpNF=1)"""
        print("DEBUG: Iniciando importar_xml_cliente...")
        nota_saida = NotaFiscalSaida()
        venda = PedidoVenda()
        arquivo_xml = request.FILES.get('arquivo_xml');
        if not arquivo_xml: raise ValueError("Arquivo XML não encontrado no request (cliente).")
        try:
            arquivo_xml.seek(0); parser = etree.XMLParser(remove_blank_text=True)
            xml_tree = etree.parse(arquivo_xml, parser); root = xml_tree.getroot()
        except Exception as e: raise ValueError(f"Erro ao re-parsear XML (cliente): {e}")
        nfe_element = None
        if root.tag == etree.QName(NFE_NAMESPACE, 'NFe'): nfe_element = root
        else: nfe_list = root.xpath('.//ns:NFe', namespaces=NSMAP); nfe_element = nfe_list[0] if nfe_list else None
        if nfe_element is None: raise ValueError("Elemento <NFe> não encontrado (cliente).")
        infNFe = nfe_element.xpath('./ns:infNFe', namespaces=NSMAP)[0];
        ide = infNFe.xpath('./ns:ide', namespaces=NSMAP)[0]

        # --- Extração de Dados para Nota de Saída ---
        # Chave
        chave_tag_id = nfe_element.xpath('./@Id', namespaces=NSMAP)
        if chave_tag_id and 'NFe' in chave_tag_id[0]: nota_saida.chave = chave_tag_id[0].replace('NFe', '')
        else: nota_saida.chave = _get_text(root, './/ns:protNFe/ns:infProt/ns:chNFe')

        # Dados da <ide>
        nota_saida.n_nf_saida = _get_text(ide, './ns:nNF')
        nota_saida.serie = _get_text(ide, './ns:serie')
        if not nota_saida.n_nf_saida or not nota_saida.serie: raise ValueError("Número ou Série da NF-e não encontrados.")
        if NotaFiscalSaida.objects.filter(n_nf_saida=nota_saida.n_nf_saida, serie=nota_saida.serie).exists():
            raise ValueError(f'Nota Saída {nota_saida.n_nf_saida}/{nota_saida.serie} já existe.')
        # --- !!! COMPLETAR MAPEAMENTO DA TAG <ide> PARA nota_saida !!! ---
        nota_saida.natop = _get_text(ide, './ns:natOp')
        # ... etc ...

        # Cliente (destinatario) <dest>
        print("DEBUG Cliente: Processando Destinatário...")
        dest = infNFe.xpath('./ns:dest', namespaces=NSMAP)[0]
        dest_cnpj = _limpar_numero(_get_text(dest, './ns:CNPJ'))
        dest_cpf = _limpar_numero(_get_text(dest, './ns:CPF'))
        cliente_obj = None # Inicialização corrigida
        # ... (Lógica para buscar ou criar Cliente - como antes, com verificação de nome) ...
        extracted_name_cli = _get_text(dest, './ns:xNome')
        # ... (Busca cliente existente) ...
        if not cliente_obj:
             cliente_obj = Cliente() # Define aqui dentro
             if not extracted_name_cli or not extracted_name_cli.strip(): raise ValueError("Nome/Razão Social do destinatário não encontrado.")
             cliente_obj.nome_razao_social = extracted_name_cli
             # ... (Salva cliente e relacionados) ...
        nota_saida.dest_saida = cliente_obj
        venda.cliente = cliente_obj
        print(f"DEBUG Cliente: Cliente definido: {cliente_obj}")

        # Empresa (emitente) - Usar 'Minha Empresa'
        # ... (Lógica para buscar Minha Empresa) ...
        nota_saida.emit_saida = m_empresa.m_empresa

        # Dados gerais da Venda
        # --- !!! COMPLETAR MAPEAMENTO DOS TOTAIS, FRETE, ETC PARA 'venda' !!! ---
        venda.save()

        # Itens da Venda <det>
        # --- !!! COMPLETAR MAPEAMENTO DENTRO DO LOOP DE ITENS !!! ---
        # ...

        # Duplicatas <dup>
        # --- !!! COMPLETAR MAPEAMENTO DENTRO DO LOOP DE DUPLICATAS !!! ---
        # ...

        # Finalizar e salvar a nota fiscal
        nota_saida.venda = venda
        nota_saida.status_nfe = '3'
        nota_saida.save()
        print(f"DEBUG Cliente: Nota Fiscal Saída salva (ID: {nota_saida.pk}).")
        self.salvar_mensagem("Nota Fiscal de Saída importada com sucesso.")


    def importar_xml_fornecedor(self, request):
        """Importa NF-e de ENTRADA (tpNF=0)"""
        print("DEBUG: Iniciando importar_xml_fornecedor...")
        self.salvar_mensagem('')
        nota_entrada = NotaFiscalEntrada()
        compra = PedidoCompra()

        # Obter arquivo e parsear XML
        arquivo_xml = request.FILES.get('arquivo_xml');
        if not arquivo_xml: raise ValueError("Nenhum arquivo XML enviado.")
        try:
            arquivo_xml.seek(0)
            parser = etree.XMLParser(remove_blank_text=True)
            xml_tree = etree.parse(arquivo_xml, parser); root = xml_tree.getroot()
            print("DEBUG Fornecedor: XML parseado com sucesso.")
        except etree.XMLSyntaxError as e: raise ValueError(f"Erro de sintaxe no XML: {e}")
        except Exception as e: raise ValueError(f"Erro ao ler/parsear XML: {e}")

        nfe_element = None
        if root.tag == etree.QName(NFE_NAMESPACE, 'NFe'): nfe_element = root
        else: nfe_list = root.xpath('.//ns:NFe', namespaces=NSMAP); nfe_element = nfe_list[0] if nfe_list else None
        if nfe_element is None: raise ValueError("Elemento <NFe> não encontrado.")
        print(f"DEBUG Fornecedor: Elemento <NFe> encontrado: {nfe_element.tag}")
        infNFe = nfe_element.xpath('./ns:infNFe', namespaces=NSMAP);
        if not infNFe: raise ValueError("Elemento <infNFe> não encontrado.");
        infNFe = infNFe[0]
        print(f"DEBUG Fornecedor: <infNFe> encontrado: {infNFe.tag}")

        # --- Extração de Dados ---
        print("DEBUG Fornecedor: Tentando extrair Chave...")
        chave_tag_id = nfe_element.xpath('./@Id', namespaces=NSMAP)
        if chave_tag_id and 'NFe' in chave_tag_id[0]: nota_entrada.chave = chave_tag_id[0].replace('NFe', '')
        else: nota_entrada.chave = _get_text(root, './/ns:protNFe/ns:infProt/ns:chNFe')
        print(f"DEBUG Fornecedor: Chave extraída='{nota_entrada.chave}'")

        print("DEBUG Fornecedor: Tentando encontrar <ide>...")
        ide_list = infNFe.xpath('./ns:ide', namespaces=NSMAP)
        if not ide_list: raise ValueError("Elemento <ide> não encontrado.");
        ide = ide_list[0]
        print(f"DEBUG Fornecedor: <ide> encontrado: {ide.tag}")
        try:
             print("--- DEBUG Fornecedor: Conteúdo do elemento <ide> ---")
             print(etree.tostring(ide, pretty_print=True, encoding='unicode', xml_declaration=False))
             print("--- FIM DEBUG <ide> ---")
        except Exception as e_print: print(f"--- ERRO AO IMPRIMIR <ide>: {e_print} ---")

        print("DEBUG Fornecedor: Tentando extrair nNF e serie...")
        n_nf = _get_text(ide, './ns:nNF') # Busca o elemento
        serie = _get_text(ide, './ns:serie') # Busca o elemento
        print(f"DEBUG Fornecedor: nNF extraído='{n_nf}', serie extraída='{serie}'")
        if not n_nf or not serie: raise ValueError("Número ou Série da NF-e de entrada não encontrados.")
        nota_entrada.n_nf_entrada = n_nf
        nota_entrada.serie = serie
        print("DEBUG Fornecedor: nNF e Serie atribuídos a nota_entrada.")
        # --- !!! COMPLETAR MAPEAMENTO DA TAG <ide> PARA nota_entrada !!! ---
        nota_entrada.natop = _get_text(ide, './ns:natOp')
        nota_entrada.dhemi = _get_datetime(ide, './ns:dhEmi')
        nota_entrada.tpnf = '0' # ENTRADA
        # ... etc ...

        # Dados Adicionais <infAdic>
        # --- !!! COMPLETAR MAPEAMENTO DA TAG <infAdic> PARA nota_entrada !!! ---
        infAdic = infNFe.xpath('./ns:infAdic', namespaces=NSMAP)
        # ...

        # Fornecedor (emitente) <emit>
        print("DEBUG Fornecedor: Processando Emitente (Fornecedor)...")
        emit = infNFe.xpath('./ns:emit', namespaces=NSMAP)[0]
        emit_cnpj = _limpar_numero(_get_text(emit, './ns:CNPJ'))
        emit_cpf = _limpar_numero(_get_text(emit, './ns:CPF'))
        fornecedor_obj = None
        my_comp_emit_cnpj = None # CNPJ da Minha Empresa (será buscado ao validar destinatário)

        # Empresa (Destinatário) <dest> - Buscar ANTES de processar emitente
        print("DEBUG Fornecedor: Processando Destinatário (Minha Empresa)...")
        dest = infNFe.xpath('./ns:dest', namespaces=NSMAP)[0]
        dest_cnpj = _limpar_numero(_get_text(dest, './ns:CNPJ'))
        # --- GUARDA CNPJ DO XML (Destinatário) ---
        self.last_dest_cnpj_xml = dest_cnpj
        # --- FIM ---
        my_comp_db_cnpj = None
        self.last_my_comp_cnpj_db = None # Inicializa

        try:
             auth_user = get_user_model().objects.get(pk=request.user.id)
             usuario_profile = UsuarioProfile.objects.get(user=auth_user)
             m_empresa = MinhaEmpresa.objects.select_related('m_empresa__pessoa_jur_info').get(m_usuario=usuario_profile)
             nota_entrada.dest_entrada = m_empresa.m_empresa # Destinatário é Minha Empresa

             if hasattr(m_empresa.m_empresa, 'pessoa_jur_info') and m_empresa.m_empresa.pessoa_jur_info and hasattr(m_empresa.m_empresa.pessoa_jur_info, 'cnpj'):
                 my_comp_db_cnpj_raw = m_empresa.m_empresa.pessoa_jur_info.cnpj
                 my_comp_db_cnpj = _limpar_numero(my_comp_db_cnpj_raw)
                 # --- GUARDA CNPJ DO DB (Minha Empresa) ---
                 self.last_my_comp_cnpj_db = my_comp_db_cnpj
                 # --- FIM ---
                 print(f"DEBUG: CNPJ 'Minha Empresa' (DB, limpo): '{my_comp_db_cnpj}'")
             else: raise ValueError("CNPJ da 'Minha Empresa' não encontrado no cadastro.")

             # --- ADICIONADO DEBUG DE COMPARAÇÃO ---
             print(f"*** DEBUG CNPJ Destinatário (XML, limpo): '{dest_cnpj}' (Tipo: {type(dest_cnpj)})")
             print(f"*** DEBUG CNPJ Minha Empresa (DB, limpo): '{my_comp_db_cnpj}' (Tipo: {type(my_comp_db_cnpj)})")
             # --- FIM DEBUG ---

             # Validação do Destinatário
             if my_comp_db_cnpj != dest_cnpj:
                  print(f"DEBUG: Falha na validação do CNPJ do Destinatário!") # DEBUG
                  raise ValueError("CNPJ do destinatário no XML não confere com a 'Minha Empresa'.")
             print(f"DEBUG Fornecedor: Destinatário (Minha Empresa) validado: {nota_entrada.dest_entrada}")

        except (get_user_model().DoesNotExist, UsuarioProfile.DoesNotExist, MinhaEmpresa.DoesNotExist): raise ValueError("Empresa destinatária ('Minha Empresa') não configurada ou usuário/perfil inválido.")
        except AttributeError: raise ValueError("Não foi possível verificar o CNPJ da 'Minha Empresa'.")
        except ValueError as ve: raise ve # Repassa o ValueError da validação
        except Exception as e: print(f"Erro buscando MinhaEmpresa: {e}"); raise ValueError(f"Erro ao validar destinatário: {e}")

        # Agora processar o Fornecedor (Emitente) usando my_comp_db_cnpj que já buscamos
        if my_comp_db_cnpj and my_comp_db_cnpj == emit_cnpj: # Compara emitente XML com Minha Empresa DB
             print("DEBUG Fornecedor: Emitente é a própria empresa (Importação?).")
             fornecedor_obj = None
             nota_entrada.emit_entrada = nota_entrada.dest_entrada # Emitente = Destinatário
             if not Compra._meta.get_field('fornecedor').null:
                  try: fornecedor_obj = Fornecedor.objects.get(pessoa_jur_info__cnpj=my_comp_db_cnpj)
                  except Fornecedor.DoesNotExist: raise ValueError("Campo Fornecedor obrigatório. Crie um Fornecedor 'Emissão Própria' ou permita Nulo.")
        else:
            print(f"DEBUG Fornecedor: Emitente é terceiro ({emit_cnpj or emit_cpf}). Buscando/Criando Fornecedor...")
            # ... (Lógica original para buscar/criar Fornecedor terceiro, com verificação de nome) ...
            if emit_cnpj: fornecedores = [f for f in Fornecedor.objects.filter(tipo_pessoa='PJ') if hasattr(f,'cpf_cnpj_apenas_digitos') and f.cpf_cnpj_apenas_digitos == emit_cnpj]
            elif emit_cpf: fornecedores = [f for f in Fornecedor.objects.filter(tipo_pessoa='PF') if hasattr(f,'cpf_cnpj_apenas_digitos') and f.cpf_cnpj_apenas_digitos == emit_cpf]
            else: fornecedores = []
            if fornecedores: fornecedor_obj = fornecedores[0]
            else: # Criar
                fornecedor_obj = Fornecedor()
                extracted_name_forn = _get_text(emit, './ns:xNome')
                if not extracted_name_forn or not extracted_name_forn.strip(): raise ValueError("Nome/Razão Social do emitente não encontrado.")
                fornecedor_obj.nome_razao_social = extracted_name_forn
                if emit_cnpj: fornecedor_obj.tipo_pessoa = 'PJ'
                elif emit_cpf: fornecedor_obj.tipo_pessoa = 'PF'
                else: raise ValueError("Emitente sem CPF ou CNPJ.")
                fornecedor_obj.criado_por = request.user if request.user.is_authenticated else None
                fornecedor_obj.save() # Salva
                # ... (Salva relacionados PJ/PF, Endereco, Tel) ...
            nota_entrada.emit_entrada = fornecedor_obj # Fornecedor terceiro

        compra.fornecedor = fornecedor_obj # Associa fornecedor (pode ser None)
        print(f"DEBUG Fornecedor: Fornecedor definido/criado para Compra: {fornecedor_obj}")

        # Verificar duplicidade APÓS ter emit_entrada definido
        if nota_entrada.emit_entrada and NotaFiscalEntrada.objects.filter(n_nf_entrada=nota_entrada.n_nf_entrada, serie=nota_entrada.serie, emit_entrada=nota_entrada.emit_entrada).exists():
             raise ValueError(f'Nota Entrada {nota_entrada.n_nf_entrada}/{nota_entrada.serie} do emitente {nota_entrada.emit_entrada} já existe.')

        # Dados gerais da Compra
        print("DEBUG Fornecedor: Processando dados gerais da Compra...")
        # --- !!! COMPLETAR MAPEAMENTO DOS TOTAIS, FRETE, ETC PARA 'compra' !!! ---
        # ... (Atribui mod_frete, valor_total, etc., como antes) ...
        compra.save() # Salva a compra
        print(f"DEBUG Fornecedor: Compra salva (ID: {compra.pk}).")

        # Itens da Compra <det>
        itens_para_salvar_compra = []
        print("--- Iniciando loop de itens (Fornecedor) ---")
        # **** AINDA PRECISA COMPLETAR O MAPEAMENTO DENTRO DESTE LOOP ****
        for i, det_element in enumerate(infNFe.xpath('./ns:det', namespaces=NSMAP)):
            print(f"Processando item {i+1} (Fornecedor)...")
            # ... (Código para criar item_compra, buscar/criar produto, extrair qtd, vlunit, impostos) ...
            itens_para_salvar_compra.append(item_compra)
        print(f"--- Fim loop de itens (Fornecedor). {len(itens_para_salvar_compra)} itens preparados ---")
        for item in itens_para_salvar_compra: item.save()
        print("DEBUG Fornecedor: Itens salvos.")

        # Duplicatas <dup> (associar a contas a pagar?)
        # ... (Completar mapeamento se necessário) ...

        # Finalizar e salvar a nota fiscal de entrada
        nota_entrada.compra = compra
        nota_entrada.status_nfe = '9' # Importada
        nota_entrada.save()
        print(f"DEBUG Fornecedor: Nota Fiscal Entrada salva (ID: {nota_entrada.pk}).")

        self.salvar_mensagem("Nota Fiscal de Entrada importada com sucesso.")

        # excepts foram movidos para importar_xml