from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
import pytz 
from datetime import datetime 
import random 
from django.utils import timezone 
import logging

logger = logging.getLogger(__name__)

# Importar os bindings da nfelib a partir do arquivo de compatibilidade
# fiscal.compat (compat.py dentro da pasta fiscal)
try:
    from ..compat import ( 
        Tnfe, 
        TenderEmi,
        Tendereco,
        TIpi, 
        TpNF, 
        IdDest, 
        TpImp, 
        TpEmis, 
        FinNFe, 
        IndFinal, 
        IndPres, 
        ProcEmi, 
        CRT, 
        IndIEDest,
        Torig, 
        ProdIndTot,
        Tamb, 
        Tmod, 
        TcodUfIbge, 
        TufEmi, 
        Tuf
    )
    logger.info("Bindings da nfelib importados com sucesso de fiscal.compat para models.nota_fiscal.")

except ImportError as e:
    logger.error(f"Falha CRÍTICA ao importar bindings da nfelib de fiscal.compat em models.nota_fiscal. Erro: {e}")
    # Definir como None para permitir que o Django carregue, mas a funcionalidade falhará.
    Tnfe, TenderEmi, Tendereco, TIpi = None, None, None, None
    TpNF, IdDest, TpImp, TpEmis, FinNFe, IndFinal, IndPres, ProcEmi = (None,) * 8
    CRT, IndIEDest, Torig, ProdIndTot = (None,) * 4
    Tamb, Tmod, TcodUfIbge, TUfEmi, TUf = None, None, None, None, None
    raise ImportError(f"Não foi possível importar os bindings da nfelib de fiscal.compat. Verifique o arquivo compat.py e a instalação da nfelib. Erro original: {e}")


def arquivo_proc_path(instance, filename):
    return f'fiscal/arquivos_processados_obsoletos/{filename}'

class NotaFiscal(models.Model):
    STATUS_CHOICES = [
        ('E', 'Em digitação'), ('V', 'Validada'), ('A', 'Autorizada'),
        ('C', 'Cancelada'), ('D', 'Denegada'), ('R', 'Erro'), 
    ]
    
    numero = models.IntegerField('Número da NF', null=True, blank=True) 
    serie = models.CharField('Série da NF', max_length=3, null=True, blank=True) 
    data_emissao = models.DateTimeField('Data de Emissão', default=timezone.now) 
    
    chave = models.CharField('Chave de Acesso', max_length=44, blank=True, null=True, editable=False)
    protocolo = models.CharField('Protocolo de Autorização', max_length=15, blank=True, null=True, editable=False)
    status = models.CharField('Status da NF', max_length=1, choices=STATUS_CHOICES, default='E')
    motivo_erro = models.TextField('Motivo do Erro de Processamento', blank=True, null=True)
    
    valor_bc_icms = models.DecimalField('Base de Cálculo ICMS', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_icms = models.DecimalField('Valor do ICMS', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_icms_desonerado = models.DecimalField('Valor ICMS Desonerado', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_fcp = models.DecimalField('Valor FCP (Não ST)', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_bc_st = models.DecimalField('Base de Cálculo ICMS ST', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_st = models.DecimalField('Valor do ICMS ST', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_fcp_st = models.DecimalField('Valor FCP ST', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_fcp_st_retido = models.DecimalField('Valor FCP ST Retido Ant.', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_frete = models.DecimalField('Valor do Frete', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_seguro = models.DecimalField('Valor do Seguro', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_desconto = models.DecimalField('Valor do Desconto', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_imposto_importacao = models.DecimalField('Valor Imposto de Importação (II)', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_ipi = models.DecimalField('Valor do IPI', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_ipi_devolvido = models.DecimalField('Valor IPI Devolvido', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_pis = models.DecimalField('Valor do PIS', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_cofins = models.DecimalField('Valor do COFINS', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_outros = models.DecimalField('Outras Despesas Acessórias', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_total_produtos = models.DecimalField('Valor Total dos Produtos/Serviços', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_total_nota = models.DecimalField('Valor Total da NF-e', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    valor_total_tributos_estimado = models.DecimalField('Valor Total Estimado de Tributos', max_digits=15, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)

    natureza_operacao = models.ForeignKey(
        'fiscal.NaturezaOperacao', 
        verbose_name='Natureza da Operação',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True  
    )
    emitente = models.ForeignKey(
        'cadastro.Empresa',
        verbose_name='Emitente',
        on_delete=models.SET_NULL, 
        related_name='notas_emitidas',
        null=True,  
        blank=True  
    )
    destinatario = models.ForeignKey(
        'cadastro.Cliente',
        verbose_name='Destinatário',
        on_delete=models.SET_NULL, 
        related_name='notas_recebidas',
        null=True,  
        blank=True  
    )
    
    INDICADOR_PAGAMENTO_CHOICES = [('0', 'Pagamento à vista'), ('1', 'Pagamento a prazo'), ('2', 'Outros')]
    indicador_pagamento = models.CharField('Indicador Pagamento', max_length=1, choices=INDICADOR_PAGAMENTO_CHOICES, default='0', null=True, blank=True)
    data_hora_saida_entrada = models.DateTimeField('Data/Hora Saída/Entrada', null=True, blank=True)
    FORMA_EMISSAO_CHOICES = [('1', 'Normal'), ('2', 'Contingência FS-IA'), ('4', 'Contingência DPEC'), ('5', 'Contingência FS-DA'), ('6', 'Contingência SVC-AN'), ('7', 'Contingência SVC-RS')]
    forma_emissao = models.CharField('Forma de Emissão', max_length=1, choices=FORMA_EMISSAO_CHOICES, default='1', null=True, blank=True)
    FINALIDADE_EMISSAO_CHOICES = [('1', 'NF-e normal'), ('2', 'NF-e complementar'), ('3', 'NF-e de ajuste'), ('4', 'Devolução de mercadoria')]
    finalidade_emissao = models.CharField('Finalidade da Emissão', max_length=1, choices=FINALIDADE_EMISSAO_CHOICES, default='1', null=True, blank=True)
    
    fatura_numero = models.CharField('Número da Fatura', max_length=60, null=True, blank=True)
    fatura_valor_original = models.DecimalField('Valor Original da Fatura', max_digits=15, decimal_places=2, null=True, blank=True)
    fatura_valor_desconto = models.DecimalField('Desconto da Fatura', max_digits=15, decimal_places=2, null=True, blank=True)
    fatura_valor_liquido = models.DecimalField('Valor Líquido da Fatura', max_digits=15, decimal_places=2, null=True, blank=True)

    xml_gerado = models.TextField('XML Gerado', blank=True, null=True) 
    
    informacoes_adicionais_fisco = models.TextField('Informações Adicionais de Interesse do Fisco', blank=True, null=True)
    informacoes_complementares = models.TextField('Informações Complementares de Interesse do Contribuinte', blank=True, null=True)

    class Meta:
        verbose_name = "Nota Fiscal Eletrônica"
        verbose_name_plural = "Notas Fiscais Eletrônicas"
        ordering = ['-data_emissao', '-numero']
    
    def __str__(self):
        nome_emitente = "Emitente não definido"
        if self.emitente:
            nome_emitente = self.emitente.nome_fantasia if self.emitente.nome_fantasia else self.emitente.razao_social
        return f"NF-e Série {self.serie or '?'} / Número {self.numero or '?'} ({nome_emitente}) - {self.get_status_display()}"
    
    def get_configuracao_servico(self):
        if not self.emitente:
            raise ValueError("Emitente não definido para a Nota Fiscal. Impossível obter configuração do serviço.")
        return {
            'caminho_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['arquivo'], 
            'senha_certificado_a1': settings.NFE_CONFIG['CERTIFICADO']['senha'],     
            'ambiente_sefaz': settings.NFE_CONFIG['AMBIENTE_NFE'],                 
            'cnpj_empresa_emitente': self.emitente.cnpj_apenas_numeros,        
            'uf_sigla_emitente': self.emitente.endereco.get('uf_sigla') if self.emitente.endereco else None, 
            'versao_leiaute': settings.NFE_CONFIG['VERSAO_LEIAUTE_NFE'], 
        }

    def _determinar_destino(self):
        id_dest = '1' 
        if not self.emitente or not self.destinatario:
            return id_dest, '0', '9' 

        emit_uf_sigla = self.emitente.endereco.get('uf_sigla') 
        dest_uf_sigla = self.destinatario.endereco.get('uf_sigla') if self.destinatario.endereco else None
        dest_pais_cod = self.destinatario.endereco.get('pais_codigo_bacen', '1058') if self.destinatario.endereco else '1058'

        if emit_uf_sigla and dest_uf_sigla:
            if emit_uf_sigla == dest_uf_sigla: id_dest = '1'
            elif dest_pais_cod == '1058': id_dest = '2' 
            else: id_dest = '3' 
        elif dest_pais_cod and dest_pais_cod != '1058': id_dest = '3'

        ind_final = '1' if self.destinatario.consumidor_final else '0'
        
        modalidade = getattr(self.destinatario, 'modalidade_presencial', '9')
        map_presenca = {'presencial': '1', 'internet': '2', 'teleatendimento': '3',
                        'entrega_domicilio_nfce': '4', 'presencial_fora_estabelecimento': '5',
                        'nao_se_aplica': '0', 'outros': '9'}
        ind_pres = map_presenca.get(modalidade, '9')
        return id_dest, ind_final, ind_pres

    def calcular_totais(self):
        from django.db.models import Sum
        itens_qs = self.itens.all()
        
        if not itens_qs.exists():
            for field_name in [f.name for f in self._meta.get_fields() if isinstance(f, models.DecimalField) and 'valor_' in f.name]:
                setattr(self, field_name, Decimal('0.00'))
        else:
            self.valor_total_produtos = itens_qs.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
            self.valor_bc_icms = sum(getattr(item.icms, 'valor_bc', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_icms = sum(getattr(item.icms, 'valor_icms', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_icms_desonerado = sum(getattr(item.icms, 'valor_icms_desonerado', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_fcp = sum(getattr(item.icms, 'valor_fcp', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_bc_st = sum(getattr(item.icms, 'valor_bc_st', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_st = sum(getattr(item.icms, 'valor_st', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_fcp_st = sum(getattr(item.icms, 'valor_fcp_st', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_fcp_st_retido = sum(getattr(item.icms, 'valor_fcp_st_retido', Decimal('0.00')) for item in itens_qs if hasattr(item, 'icms') and item.icms)
            self.valor_imposto_importacao = sum(getattr(item, 'imposto_importacao_valor_ii', Decimal('0.00')) for item in itens_qs)
            self.valor_ipi = sum(getattr(item.ipi, 'valor_ipi', Decimal('0.00')) for item in itens_qs if hasattr(item, 'ipi') and item.ipi)
            self.valor_ipi_devolvido = sum(getattr(item.ipi, 'valor_ipi_devolvido', Decimal('0.00')) for item in itens_qs if hasattr(item, 'ipi') and item.ipi)
            self.valor_pis = sum(getattr(item.pis, 'valor_pis', Decimal('0.00')) for item in itens_qs if hasattr(item, 'pis') and item.pis)
            self.valor_cofins = sum(getattr(item.cofins, 'valor_cofins', Decimal('0.00')) for item in itens_qs if hasattr(item, 'cofins') and item.cofins)
        
        self.valor_total_nota = (
            self.valor_total_produtos - 
            (self.valor_desconto or Decimal('0.00')) + 
            (self.valor_st or Decimal('0.00')) +
            (self.valor_frete or Decimal('0.00')) + 
            (self.valor_seguro or Decimal('0.00')) + 
            (self.valor_outros or Decimal('0.00')) +
            (self.valor_imposto_importacao or Decimal('0.00')) + 
            (self.valor_ipi or Decimal('0.00')) - 
            (self.valor_ipi_devolvido or Decimal('0.00')) +
            (self.valor_fcp or Decimal('0.00')) + 
            (self.valor_fcp_st or Decimal('0.00'))
        )

    def clean(self):
        super().clean()
        if self.status not in ['E', 'R']:
            if not self.emitente: 
                raise ValidationError({'emitente': "É necessário definir um emitente para a nota fiscal."})
            if not self.numero:
                raise ValidationError({'numero': "O número da nota fiscal é obrigatório."})
            if not self.serie:
                raise ValidationError({'serie': "A série da nota fiscal é obrigatória."})
            if not self.natureza_operacao:
                raise ValidationError({'natureza_operacao': "A natureza da operação é obrigatória."})
            if not self.destinatario:
                raise ValidationError({'destinatario': "O destinatário é obrigatório."})
            
            if self.pk and not self.itens.exists():
                 raise ValidationError({'itens': "Nota Fiscal deve ter pelo menos um item para ser validada."})
            if self.valor_total_nota < Decimal('0.00'):
                 raise ValidationError({'valor_total_nota': "Valor total da nota não pode ser negativo."})
        
        if self.numero and self.serie and self.emitente:
            qs = NotaFiscal.objects.filter(numero=self.numero, serie=self.serie, emitente=self.emitente)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'numero': f'Já existe uma Nota Fiscal com este número ({self.numero}), série ({self.serie}) para o emitente selecionado.'})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def _get_icms_nfelib(self, icms_model_instance, item_bc_icms=Decimal('0.00'), item_valor_icms=Decimal('0.00'), item_valor_fcp=Decimal('0.00'), item_bc_icms_st=Decimal('0.00'), item_valor_icms_st=Decimal('0.00'), item_valor_fcp_st=Decimal('0.00')):
        if not icms_model_instance or not Tnfe: return None 
        
        icms_group = Tnfe.InfNFe.Det.Imposto.Icms() 
        
        regime_emitente = '2' 
        if icms_model_instance.grupo_fiscal and icms_model_instance.grupo_fiscal.regime_trib:
            regime_emitente = icms_model_instance.grupo_fiscal.regime_trib
        
        cst_ou_csosn = icms_model_instance.csosn if regime_emitente == '0' else icms_model_instance.cst
        origem_mercadoria_valor = getattr(icms_model_instance, 'origem_mercadoria', '0')

        if cst_ou_csosn == '00':
            icms00 = Tnfe.InfNFe.Det.Imposto.Icms.Icms00()
            icms00.orig = Torig(origem_mercadoria_valor) if Torig else origem_mercadoria_valor
            icms00.CST = cst_ou_csosn 
            icms00.modBC = icms_model_instance.mod_bc 
            icms00.vBC = f"{item_bc_icms:.2f}"
            icms00.pICMS = f"{icms_model_instance.p_icms:.4f}"
            icms00.vICMS = f"{item_valor_icms:.2f}"
            if item_valor_fcp > 0: 
                icms00.vFCP = f"{item_valor_fcp:.2f}"
            icms_group.ICMS00 = icms00
        elif cst_ou_csosn == '101' and regime_emitente == '0': 
            icmssn101 = Tnfe.InfNFe.Det.Imposto.Icms.Icmssn101()
            icmssn101.orig = Torig(origem_mercadoria_valor) if Torig else origem_mercadoria_valor
            icmssn101.CSOSN = cst_ou_csosn 
            icmssn101.pCredSN = f"{icms_model_instance.p_cred_sn:.4f}"
            icmssn101.vCredICMSSN = f"{getattr(icms_model_instance, 'valor_credito_icms_sn', Decimal('0.00')):.2f}" 
            icms_group.ICMSSN101 = icmssn101
        elif cst_ou_csosn == '20':
            icms20 = Tnfe.InfNFe.Det.Imposto.Icms.Icms20()
            icms20.orig = Torig(origem_mercadoria_valor) if Torig else origem_mercadoria_valor
            icms20.CST = cst_ou_csosn 
            icms20.modBC = icms_model_instance.mod_bc 
            icms20.pRedBC = f"{icms_model_instance.p_red_bc:.4f}"
            icms20.vBC = f"{item_bc_icms:.2f}"
            icms20.pICMS = f"{icms_model_instance.p_icms:.4f}"
            icms20.vICMS = f"{item_valor_icms:.2f}"
            v_icms_deson = getattr(icms_model_instance, 'valor_icms_desonerado', Decimal('0.00'))
            if v_icms_deson > 0 :
                icms20.vICMSDeson = f"{v_icms_deson:.2f}"
                if icms_model_instance.mot_des_icms:
                    icms20.motDesICMS = icms_model_instance.mot_des_icms 
            icms_group.ICMS20 = icms20
        else: 
            logger.warning(f"CST/CSOSN {cst_ou_csosn} não tratado ou tipos nfelib não importados para ICMS.")
            pass 
            
        return icms_group 

    def _get_ipi_nfelib(self, ipi_model_instance, item_quantidade=Decimal('0.0000'), item_bc_ipi=Decimal('0.00'), item_valor_ipi=Decimal('0.00')):
        if not ipi_model_instance or not TIpi: return None
        
        ipi_obj = TIpi() 
        
        if ipi_model_instance.cl_enq: ipi_obj.clEnq = ipi_model_instance.cl_enq
        if ipi_model_instance.cnpj_prod: ipi_obj.CNPJProd = ipi_model_instance.get_cnpj_prod_apenas_digitos()
        ipi_obj.cEnq = ipi_model_instance.c_enq or "999"

        cst_ipi = ipi_model_instance.cst
        if cst_ipi in ['00', '49', '50', '99']:
            if hasattr(TIpi, 'Ipitrib'):
                ipitrib = TIpi.Ipitrib() 
            elif hasattr(Tnfe.InfNFe.Det.Imposto.Ipi, 'Ipitrib'): 
                ipitrib = Tnfe.InfNFe.Det.Imposto.Ipi.Ipitrib()
            else:
                logger.error("Não foi possível encontrar a classe Ipitrib para IPI.")
                return None
                
            ipitrib.CST = cst_ipi 
            if ipi_model_instance.tipo_ipi == '2' and ipi_model_instance.p_ipi is not None: 
                if item_valor_bc_ipi is not None: 
                    ipitrib.vBC = f"{item_valor_bc_ipi:.2f}"
                ipitrib.pIPI = f"{ipi_model_instance.p_ipi:.4f}"
            elif ipi_model_instance.tipo_ipi == '1' and ipi_model_instance.valor_fixo_ipi is not None: 
                if item_quantidade is not None: 
                    ipitrib.qUnid = f"{item_quantidade:.4f}" 
                ipitrib.vUnid = f"{ipi_model_instance.valor_fixo_ipi:.4f}"
            
            v_ipi_final = item_valor_ipi if item_valor_ipi is not None else getattr(ipi_model_instance, 'valor_ipi', Decimal('0.00'))
            ipitrib.vIPI = f"{v_ipi_final:.2f}"
            ipi_obj.IPITrib = ipitrib 
        elif cst_ipi in ['01', '02', '03', '04', '05', '51', '52', '53', '54', '55']:
            if hasattr(TIpi, 'Ipint'):
                ipint = TIpi.Ipint()
            elif hasattr(Tnfe.InfNFe.Det.Imposto.Ipi, 'Ipint'):
                ipint = Tnfe.InfNFe.Det.Imposto.Ipi.Ipint()
            else:
                logger.error("Não foi possível encontrar a classe Ipint para IPI.")
                return None
            ipint.CST = cst_ipi 
            ipi_obj.IPINT = ipint 
        else:
            logger.warning(f"CST IPI {cst_ipi} não tratado.")
        return ipi_obj

    def _get_pis_nfelib(self, pis_model_instance, item_bc_pis=Decimal('0.00'), item_qbc_prod_pis=Decimal('0.0000'), item_valor_pis=Decimal('0.00')):
        if not pis_model_instance or not Tnfe: return None
        
        pis_container = Tnfe.InfNFe.Det.Imposto.Pis()
        cst = pis_model_instance.cst
        v_pis_final = item_valor_pis if item_valor_pis is not None else getattr(pis_model_instance, 'valor_pis', Decimal('0.00'))

        if cst in ['01', '02']:
            pis_aliq = Tnfe.InfNFe.Det.Imposto.Pis.Pisaliq()
            pis_aliq.CST = cst 
            if item_bc_pis is not None:
                pis_aliq.vBC = f"{item_bc_pis:.2f}"
            pis_aliq.pPIS = f"{pis_model_instance.p_pis:.4f}"
            pis_aliq.vPIS = f"{v_pis_final:.2f}"
            pis_container.PISAliq = pis_aliq
        elif cst == '03':
            pis_qtde = Tnfe.InfNFe.Det.Imposto.Pis.Pisqtde()
            pis_qtde.CST = cst 
            if item_qbc_prod_pis is not None:
                pis_qtde.qBCProd = f"{item_qbc_prod_pis:.4f}"
            pis_qtde.vAliqProd = f"{pis_model_instance.valiq_pis:.4f}"
            pis_qtde.vPIS = f"{v_pis_final:.2f}"
            pis_container.PISQtde = pis_qtde
        elif cst in ['04', '05', '06', '07', '08', '09']:
            pis_nt = Tnfe.InfNFe.Det.Imposto.Pis.Pisnt()
            pis_nt.CST = cst 
            pis_container.PISNT = pis_nt
        elif cst >= '49': 
            pis_outr = Tnfe.InfNfe.Det.Imposto.Pis.Pisoutr()
            pis_outr.CST = cst 
            if pis_model_instance.p_pis is not None and pis_model_instance.p_pis > 0: 
                if item_bc_pis is not None:
                    pis_outr.vBC = f"{item_bc_pis:.2f}"
                pis_outr.pPIS = f"{pis_model_instance.p_pis:.4f}"
            elif pis_model_instance.valiq_pis is not None and pis_model_instance.valiq_pis > 0: 
                if item_qbc_prod_pis is not None:
                    pis_outr.qBCProd = f"{item_qbc_prod_pis:.4f}"
                pis_outr.vAliqProd = f"{pis_model_instance.valiq_pis:.4f}"
            pis_outr.vPIS = f"{v_pis_final:.2f}" 
            pis_container.PISOutr = pis_outr
        else:
            logger.warning(f"CST PIS {cst} não tratado.")
        return pis_container

    def _get_cofins_nfelib(self, cofins_model_instance, item_bc_cofins=Decimal('0.00'), item_qbc_prod_cofins=Decimal('0.0000'), item_valor_cofins=Decimal('0.00')):
        if not cofins_model_instance or not Tnfe: return None
        
        cofins_container = Tnfe.InfNFe.Det.Imposto.Cofins()
        cst = cofins_model_instance.cst
        v_cofins_final = item_valor_cofins if item_valor_cofins is not None else getattr(cofins_model_instance, 'valor_cofins', Decimal('0.00'))

        if cst in ['01', '02']:
            cofins_aliq = Tnfe.InfNFe.Det.Imposto.Cofins.Cofinsaliq()
            cofins_aliq.CST = cst 
            if item_bc_cofins is not None:
                cofins_aliq.vBC = f"{item_bc_cofins:.2f}"
            cofins_aliq.pCOFINS = f"{cofins_model_instance.p_cofins:.4f}"
            cofins_aliq.vCOFINS = f"{v_cofins_final:.2f}"
            cofins_container.COFINSAliq = cofins_aliq
        elif cst == '03':
            cofins_qtde = Tnfe.InfNFe.Det.Imposto.Cofins.Cofinsqtde()
            cofins_qtde.CST = cst 
            if item_qbc_prod_cofins is not None:
                cofins_qtde.qBCProd = f"{item_qbc_prod_cofins:.4f}"
            cofins_qtde.vAliqProd = f"{cofins_model_instance.valiq_cofins:.4f}"
            cofins_qtde.vCOFINS = f"{v_cofins_final:.2f}"
            cofins_container.COFINSQtde = cofins_qtde
        elif cst in ['04', '05', '06', '07', '08', '09']:
            cofins_nt = Tnfe.InfNFe.Det.Imposto.Cofins.Cofinsnt()
            cofins_nt.CST = cst 
            cofins_container.COFINSNT = cofins_nt
        elif cst >= '49': 
            cofins_outr = Tnfe.InfNfe.Det.Imposto.Cofins.Cofinsoutr()
            cofins_outr.CST = cst 
            if cofins_model_instance.p_cofins is not None and cofins_model_instance.p_cofins > 0:
                if item_bc_cofins is not None:
                    cofins_outr.vBC = f"{item_bc_cofins:.2f}"
                cofins_outr.pCOFINS = f"{cofins_model_instance.p_cofins:.4f}"
            elif cofins_model_instance.valiq_cofins is not None and cofins_model_instance.valiq_cofins > 0:
                if item_qbc_prod_cofins is not None:
                    cofins_outr.qBCProd = f"{item_qbc_prod_cofins:.4f}"
                cofins_outr.vAliqProd = f"{cofins_model_instance.valiq_cofins:.4f}"
            cofins_outr.vCOFINS = f"{v_cofins_final:.2f}" 
            cofins_container.COFINSOutr = cofins_outr
        else:
            logger.warning(f"CST COFINS {cst} não tratado.")
        return cofins_container

    def to_nfelib(self):
        if not Tnfe: 
            logger.error("Bindings da nfelib não estão disponíveis. Impossível gerar objeto NFe.")
            return None

        nfe_obj = Tnfe() 
        inf_nfe = Tnfe.InfNFe() 
        
        ide = Tnfe.InfNFe.Ide()
        if self.emitente: 
            ide.cUF = TcodUfIbge(self.emitente.codigo_uf_ibge) if TcodUfIbge else str(self.emitente.codigo_uf_ibge)
            ide.cMunFG = self.emitente.codigo_municipio_ibge
        else: 
            ide.cUF = TcodUfIbge("00") if TcodUfIbge else "00"
            ide.cMunFG = "0000000"  

        ide.cNF = str(random.randint(10000000, 99999999)).zfill(8)
        ide.natOp = self.natureza_operacao.descricao if self.natureza_operacao else "VENDA DE MERCADORIA" 
        ide.mod = Tmod.VALUE_55 if Tmod else "55" 
        ide.serie = self.serie or "1" 
        ide.nNF = str(self.numero or "1") 
        
        tz = pytz.timezone(settings.TIME_ZONE if hasattr(settings, 'TIME_ZONE') and settings.TIME_ZONE else 'America/Sao_Paulo')
        ide.dhEmi = self.data_emissao.astimezone(tz).isoformat(timespec='seconds') 
        if self.data_hora_saida_entrada:
            ide.dhSaiEnt = self.data_hora_saida_entrada.astimezone(tz).isoformat(timespec='seconds')
        
        tipo_nf_op = getattr(self.natureza_operacao, 'tipo_operacao', 'S') if self.natureza_operacao else 'S'
        if TpNF: ide.tpNF = TpNF.VALUE_1 if tipo_nf_op == 'S' else TpNF.VALUE_0 
        
        id_dest_val, ind_final_val, ind_pres_val = self._determinar_destino()
        if IdDest: ide.idDest = IdDest(id_dest_val) 
        if IndFinal: ide.indFinal = IndFinal(ind_final_val) 
        if IndPres: ide.indPres = IndPres(ind_pres_val) 

        if TpImp: ide.tpImp = TpImp.VALUE_1 
        if TpEmis: ide.tpEmis = TpEmis(self.forma_emissao or '1') 
        if Tamb: ide.tpAmb = Tamb(str(settings.NFE_CONFIG['AMBIENTE_NFE'])) 
        if FinNFe: ide.finNFe = FinNFe(self.finalidade_emissao or '1') 
        if ProcEmi: ide.procEmi = ProcEmi.VALUE_0 
        ide.verProc = 'DjangoSIGE-nfelib-2.1.1' 
        inf_nfe.ide = ide

        emit = Tnfe.InfNFe.Emit()
        if self.emitente: 
            emit.CNPJ = self.emitente.cnpj_apenas_numeros
            emit.xNome = self.emitente.razao_social
            if self.emitente.nome_fantasia:
                emit.xFant = self.emitente.nome_fantasia
            
            ender_emit_dict = self.emitente.endereco 
            if TenderEmi and TufEmi: 
                ender_emit = TenderEmi() 
                ender_emit.xLgr = ender_emit_dict.get('logradouro')
                ender_emit.nro = ender_emit_dict.get('numero')
                if ender_emit_dict.get('complemento'):
                    ender_emit.xCpl = ender_emit_dict.get('complemento')
                ender_emit.xBairro = ender_emit_dict.get('bairro')
                ender_emit.cMun = ender_emit_dict.get('codigo_municipio')
                ender_emit.xMun = ender_emit_dict.get('municipio')
                ender_emit.UF = TufEmi(ender_emit_dict.get('uf_sigla')) 
                ender_emit.CEP = ender_emit_dict.get('cep_numeros')
                ender_emit.cPais = "1058" 
                ender_emit.xPais = "BRASIL"
                if ender_emit_dict.get('telefone_numeros'):
                    ender_emit.fone = ender_emit_dict.get('telefone_numeros')
                emit.enderEmit = ender_emit
            
            emit.IE = self.emitente.inscricao_estadual_apenas_numeros
            if CRT: emit.CRT = CRT(self.emitente.crt_codigo) 
        inf_nfe.emit = emit

        dest = Tnfe.InfNFe.Dest()
        if self.destinatario: 
            if self.destinatario.cnpj_apenas_numeros: 
                dest.CNPJ = self.destinatario.cnpj_apenas_numeros
            elif self.destinatario.cpf_apenas_numeros: 
                dest.CPF = self.destinatario.cpf_apenas_numeros
            
            dest.xNome = self.destinatario.razao_social_ou_nome
            
            ie_dest_str = self.destinatario.inscricao_estadual_apenas_numeros or ''
            if IndIEDest: 
                if dest.CNPJ: 
                    if ie_dest_str and ie_dest_str.strip().upper() != 'ISENTO' and ie_dest_str.strip() != '':
                        dest.indIEDest = IndIEDest.VALUE_1
                        dest.IE = ie_dest_str.strip()
                    elif ie_dest_str and ie_dest_str.strip().upper() == 'ISENTO':
                         dest.indIEDest = IndIEDest.VALUE_2
                    else: 
                        dest.indIEDest = IndIEDest.VALUE_9
                else: 
                    if ie_dest_str and ie_dest_str.strip().upper() != 'ISENTO' and ie_dest_str.strip() != '':
                        dest.indIEDest = IndIEDest.VALUE_1 
                        dest.IE = ie_dest_str.strip()
                    else: 
                        dest.indIEDest = IndIEDest.VALUE_9 
            
            ender_dest_dict = self.destinatario.endereco
            if ender_dest_dict and Tendereco and Tuf: 
                ender_dest = Tendereco() 
                ender_dest.xLgr = ender_dest_dict.get('logradouro')
                ender_dest.nro = ender_dest_dict.get('numero')
                if ender_dest_dict.get('complemento'):
                    ender_dest.xCpl = ender_dest_dict.get('complemento')
                ender_dest.xBairro = ender_dest_dict.get('bairro')
                ender_dest.cMun = ender_dest_dict.get('codigo_municipio')
                ender_dest.xMun = ender_dest_dict.get('municipio')
                ender_dest.UF = Tuf(end_dest_dict.get('uf_sigla')) 
                ender_dest.CEP = ender_dest_dict.get('cep_numeros')
                
                pais_cod = ender_dest_dict.get('pais_codigo_bacen', '1058')
                ender_dest.cPais = pais_cod 
                ender_dest.xPais = "BRASIL" if pais_cod == "1058" else ender_dest_dict.get('pais_nome', 'EXTERIOR')
                
                if ender_dest_dict.get('telefone_numeros'):
                    ender_dest.fone = ender_dest_dict.get('telefone_numeros')
                dest.enderDest = ender_dest
        inf_nfe.dest = dest

        inf_nfe.det = []
        for index, item_model in enumerate(self.itens.all().order_by('ordem'), start=1): 
            det_nfelib_item = Tnfe.InfNFe.Det() 
            det_nfelib_item.nItem = str(index)
            
            produto_nfelib = item_model.to_edoc() 
            det_nfelib_item.prod = produto_nfelib
            
            imposto_nfelib_item = Tnfe.InfNFe.Det.Imposto()
            
            config_icms = getattr(item_model, 'icms', None) 
            config_ipi = getattr(item_model, 'ipi', None)   
            config_pis = getattr(item_model, 'pis', None)   
            config_cofins = getattr(item_model, 'cofins', None) 

            item_bc_icms_calc = getattr(config_icms, 'valor_bc', Decimal('0.00')) if config_icms else Decimal('0.00')
            item_valor_icms_calc = getattr(config_icms, 'valor_icms', Decimal('0.00')) if config_icms else Decimal('0.00')
            item_valor_fcp_calc = getattr(config_icms, 'valor_fcp', Decimal('0.00')) if config_icms else Decimal('0.00')

            item_bc_ipi_calc = getattr(config_ipi, 'valor_bc', Decimal('0.00')) if config_ipi else Decimal('0.00')
            item_valor_ipi_calc = getattr(config_ipi, 'valor_ipi', Decimal('0.00')) if config_ipi else Decimal('0.00')

            item_bc_pis_calc = getattr(config_pis, 'valor_bc', Decimal('0.00')) if config_pis else Decimal('0.00')
            item_valor_pis_calc = getattr(config_pis, 'valor_pis', Decimal('0.00')) if config_pis else Decimal('0.00')
            
            item_bc_cofins_calc = getattr(config_cofins, 'valor_bc', Decimal('0.00')) if config_cofins else Decimal('0.00')
            item_valor_cofins_calc = getattr(config_cofins, 'valor_cofins', Decimal('0.00')) if config_cofins else Decimal('0.00')

            if config_icms:
                imposto_nfelib_item.ICMS = self._get_icms_nfelib(
                    config_icms, 
                    item_bc_icms=item_bc_icms_calc,
                    item_valor_icms=item_valor_icms_calc,
                    item_valor_fcp=item_valor_fcp_calc
                )
            
            if config_ipi:
                imposto_nfelib_item.IPI = self._get_ipi_nfelib(
                    config_ipi,
                    item_quantidade=item_model.quantidade,
                    item_valor_bc_ipi=item_bc_ipi_calc,
                    item_valor_ipi=item_valor_ipi_calc
                )
            if config_pis:
                imposto_nfelib_item.PIS = self._get_pis_nfelib(
                    config_pis,
                    item_bc_pis=item_bc_pis_calc,
                    item_qbc_prod_pis=item_model.quantidade, 
                    item_valor_pis=item_valor_pis_calc
                )
            if config_cofins:
                imposto_nfelib_item.COFINS = self._get_cofins_nfelib(
                    config_cofins,
                    item_bc_cofins=item_bc_cofins_calc,
                    item_qbc_prod_cofins=item_model.quantidade,
                    item_valor_cofins=item_valor_cofins_calc
                )

            det_nfelib_item.imposto = imposto_nfelib_item
            inf_nfe.det.append(det_nfelib_item)

        total_nfelib = Tnfe.InfNFe.Total()
        icms_tot_nfelib = Tnfe.InfNFe.Total.Icmstot()
        
        icms_tot_nfelib.vBC = f"{self.valor_bc_icms:.2f}"
        icms_tot_nfelib.vICMS = f"{self.valor_icms:.2f}"
        icms_tot_nfelib.vICMSDeson = f"{self.valor_icms_desonerado:.2f}"
        icms_tot_nfelib.vFCP = f"{self.valor_fcp:.2f}"
        icms_tot_nfelib.vBCST = f"{self.valor_bc_st:.2f}"
        icms_tot_nfelib.vST = f"{self.valor_st:.2f}"
        icms_tot_nfelib.vFCPST = f"{self.valor_fcp_st:.2f}"
        icms_tot_nfelib.vFCPSTRet = f"{self.valor_fcp_st_retido:.2f}"
        icms_tot_nfelib.vProd = f"{self.valor_total_produtos:.2f}"
        icms_tot_nfelib.vFrete = f"{self.valor_frete:.2f}"
        icms_tot_nfelib.vSeg = f"{self.valor_seguro:.2f}"
        icms_tot_nfelib.vDesc = f"{self.valor_desconto:.2f}"
        icms_tot_nfelib.vII = f"{self.valor_imposto_importacao:.2f}"
        icms_tot_nfelib.vIPI = f"{self.valor_ipi:.2f}"
        icms_tot_nfelib.vIPIDevol = f"{self.valor_ipi_devolvido:.2f}"
        icms_tot_nfelib.vPIS = f"{self.valor_pis:.2f}"
        icms_tot_nfelib.vCOFINS = f"{self.valor_cofins:.2f}"
        icms_tot_nfelib.vOutro = f"{self.valor_outros:.2f}"
        icms_tot_nfelib.vNF = f"{self.valor_total_nota:.2f}"
        if self.valor_total_tributos_estimado is not None:
             icms_tot_nfelib.vTotTrib = f"{self.valor_total_tributos_estimado:.2f}"
        
        total_nfelib.ICMSTot = icms_tot_nfelib
        inf_nfe.total = total_nfelib

        if self.informacoes_adicionais_fisco or self.informacoes_complementares:
            infAdic = Tnfe.InfNFe.InfAdic() 
            if self.informacoes_adicionais_fisco:
                infAdic.infAdFisco = self.informacoes_adicionais_fisco
            if self.informacoes_complementares:
                infAdic.infCpl = self.informacoes_complementares
            inf_nfe.infAdic = infAdic
            
        nfe_obj.infNFe = inf_nfe 
        return nfe_obj
