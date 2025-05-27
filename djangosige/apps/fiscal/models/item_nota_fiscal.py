from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal

# Importe a classe Tnfe e Enums relevantes da nfelib
# Estas são as classes de DADOS que representam a estrutura do XML da NFe.
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import (
    Tnfe, 
    ProdIndTot # Enum para o campo indTot (0 ou 1)
    # Adicione outros Enums específicos do produto se necessário, como:
    # ProdIndEscala, Torig (se for usar diretamente aqui, embora Torig seja mais comum em ICMS)
)
# Se precisar de tipos básicos como Torig para origem do produto (se não for um Enum direto em leiaute_nfe)
# from nfelib.nfe.bindings.v4_0.tipos_basico_v4_00 import Torig 

# O modelo 'Produto' do seu app de estoque ('estoque.Produto') será referenciado via ForeignKey.

class ItemNotaFiscal(models.Model):
    nota_fiscal = models.ForeignKey(
        'fiscal.NotaFiscal', # Usando string para evitar import circular
        verbose_name='Nota Fiscal',
        on_delete=models.CASCADE,
        related_name='itens' # Permite acessar itens a partir de uma instância de NotaFiscal
    )
    # Link para o seu produto do estoque
    produto = models.ForeignKey( 
        'cadastro.Produto', # Substitua 'estoque.Produto' pelo caminho real do seu modelo de produto
        verbose_name='Produto do Estoque',
        on_delete=models.PROTECT # Evita exclusão de produto se estiver em um item de nota
    )
    ordem = models.PositiveIntegerField(
        'Ordem do Item', 
        validators=[MinValueValidator(1)],
        help_text="Número sequencial do item na nota fiscal (1, 2, 3...)"
    )
    quantidade = models.DecimalField(
        'Quantidade Comercial',
        max_digits=15, # Total de dígitos incluindo casas decimais
        decimal_places=4, # A NFe aceita até 4 casas decimais para qCom/qTrib
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Quantidade do produto comercializada"
    )
    valor_unitario = models.DecimalField(
        'Valor Unitário Comercial',
        max_digits=21, # Total de dígitos
        decimal_places=10, # A NFe aceita até 10 casas decimais para vUnCom/vUnTrib
        validators=[MinValueValidator(Decimal('0.0000000001'))],
        help_text="Valor unitário do produto para comercialização"
    )
    valor_total = models.DecimalField(
        'Valor Total do Item',
        max_digits=15, # Total de dígitos
        decimal_places=2, # vProd é com 2 casas decimais
        editable=False, # Calculado automaticamente
        help_text="Valor total do item (Quantidade * Valor Unitário)"
    )
    cfop = models.CharField(
        'CFOP', 
        max_length=4,
        help_text="Código Fiscal de Operações e Prestações"
    )
    informacoes_adicionais = models.TextField(
        'Informações Adicionais do Item', 
        blank=True, 
        null=True,
        help_text="Informações adicionais específicas deste item para a NF-e"
    )
    
    # --- Campos Opcionais para Valores que podem ser parte do Produto na NFe ---
    # Estes podem ser preenchidos se forem específicos do item e não da nota como um todo.
    # Se forem da nota toda, devem estar no modelo NotaFiscal.
    valor_frete_item = models.DecimalField(
        'Valor do Frete do Item', 
        max_digits=15, decimal_places=2, default=Decimal('0.00'), 
        blank=True, null=True, help_text="Valor do frete atribuído a este item"
    )
    valor_seguro_item = models.DecimalField(
        'Valor do Seguro do Item', 
        max_digits=15, decimal_places=2, default=Decimal('0.00'), 
        blank=True, null=True, help_text="Valor do seguro atribuído a este item"
    )
    valor_desconto_item = models.DecimalField(
        'Valor do Desconto do Item', 
        max_digits=15, decimal_places=2, default=Decimal('0.00'), 
        blank=True, null=True, help_text="Valor do desconto concedido para este item"
    )
    outras_despesas_item = models.DecimalField(
        'Outras Despesas Acessórias do Item', 
        max_digits=15, decimal_places=2, default=Decimal('0.00'), 
        blank=True, null=True, help_text="Outras despesas acessórias atribuídas a este item"
    )

    class Meta:
        verbose_name = "Item de Nota Fiscal"
        verbose_name_plural = "Itens de Nota Fiscal"
        ordering = ['nota_fiscal', 'ordem'] # Ordenação padrão
        unique_together = ('nota_fiscal', 'ordem') # Garante que a ordem do item é única por nota
    
    def __str__(self):
        # Tenta obter o número e série da nota fiscal de forma segura
        nf_info = f"NF {self.nota_fiscal.numero}/{self.nota_fiscal.serie}" if self.nota_fiscal else "NF não associada"
        produto_desc = self.produto.descricao if self.produto else "Produto não associado"
        return f"Item {self.ordem} - {nf_info} - {produto_desc}"
    
    def clean(self):
        """Validações adicionais para o modelo."""
        super().clean() 
        if self.quantidade is not None and self.quantidade <= Decimal('0'): 
            raise ValidationError({'quantidade': 'A quantidade comercial deve ser maior que zero.'})
        if self.valor_unitario is not None and self.valor_unitario <= Decimal('0'): 
            raise ValidationError({'valor_unitario': 'O valor unitário comercial deve ser maior que zero.'})
        # Adicionar outras validações se necessário
    
    def save(self, *args, **kwargs):
        """Calcula valor_total automaticamente antes de salvar e chama clean."""
        if self.quantidade is not None and self.valor_unitario is not None:
            # Garante que são Decimais para o cálculo
            qtde = Decimal(str(self.quantidade))
            v_unit = Decimal(str(self.valor_unitario))
            self.valor_total = (qtde * v_unit).quantize(Decimal('0.01')) # Arredonda para 2 casas
        
        self.full_clean() # Executa todas as validações do modelo e dos campos
        super().save(*args, **kwargs)
    
    def to_edoc(self):
        """
        Constrói e retorna o objeto Tnfe.InfNfe.Det.Prod da nfelib,
        representando os dados deste item de nota fiscal para a tag <prod>.
        Os impostos (ICMS, PIS, COFINS, IPI) NÃO são adicionados aqui;
        eles são construídos separadamente e adicionados ao objeto Tnfe.InfNfe.Det.Imposto
        no método NotaFiscal.to_nfelib() após chamar este método.
        """
        # A classe para <prod> é uma classe aninhada dentro de Tnfe.InfNfe.Det
        produto_nfelib = Tnfe.InfNfe.Det.Prod()

        # --- Campos obrigatórios e comuns de <prod> ---
        # Ajuste os nomes dos campos de self.produto para corresponder ao seu modelo de Produto do estoque
        # Ex: self.produto.codigo_interno, self.produto.gtin, self.produto.nome_fiscal, etc.
        produto_nfelib.cProd = self.produto.codigo_produto_erp # Código interno do produto no seu ERP
        produto_nfelib.cEAN = self.produto.codigo_barras_ean or "SEM GTIN" # GTIN (antigo EAN)
        produto_nfelib.xProd = self.produto.descricao_fiscal or self.produto.descricao # Descrição do produto
        produto_nfelib.NCM = self.produto.ncm # Código NCM (string de 8 ou 2 dígitos)
        produto_nfelib.CFOP = self.cfop # CFOP do item
        produto_nfelib.uCom = self.produto.unidade_medida_comercial # Unidade comercial (ex: 'UN', 'PC', 'KG')
        produto_nfelib.qCom = f"{self.quantidade:.4f}" # Quantidade comercial (até 4 casas decimais)
        produto_nfelib.vUnCom = f"{self.valor_unitario:.10f}" # Valor unitário comercial (até 10 casas decimais)
        produto_nfelib.vProd = f"{self.valor_total:.2f}" # Valor total do produto (2 casas decimais)
        
        # --- Unidade tributável - geralmente igual à comercial, mas pode diferir ---
        # Adapte se seu modelo ProdutoEstoque tiver campos separados para unidade tributável.
        produto_nfelib.cEANTrib = self.produto.codigo_barras_ean_tributavel or produto_nfelib.cEAN # GTIN da unidade tributável
        produto_nfelib.uTrib = self.produto.unidade_medida_tributavel or produto_nfelib.uCom # Unidade tributável
        produto_nfelib.qTrib = f"{self.quantidade:.4f}" # Quantidade na unidade tributável
        produto_nfelib.vUnTrib = f"{self.valor_unitario:.10f}" # Valor unitário na unidade tributável

        # indTot: Indica se o valor do item (vProd) compõe o valor total da NF-e (vNF).
        # 1 = Sim (valor do item compõe o valor total da NF-e)
        # 0 = Não (valor do item não compõe o valor total da NF-e - ex: brinde com valor zerado)
        produto_nfelib.indTot = ProdIndTot.VALUE_1 # Geralmente é 1, a menos que seja um item que não soma no total

        # --- Informações adicionais do produto (se houver) ---
        if self.informacoes_adicionais:
            produto_nfelib.infAdProd = self.informacoes_adicionais
        
        # --- Campos opcionais de <prod> que podem vir do ItemNotaFiscal ou do ProdutoEstoque ---
        if self.valor_frete_item is not None and self.valor_frete_item > Decimal('0.00'):
            produto_nfelib.vFrete = f"{self.valor_frete_item:.2f}"
        if self.valor_seguro_item is not None and self.valor_seguro_item > Decimal('0.00'):
            produto_nfelib.vSeg = f"{self.valor_seguro_item:.2f}"
        if self.valor_desconto_item is not None and self.valor_desconto_item > Decimal('0.00'):
            produto_nfelib.vDesc = f"{self.valor_desconto_item:.2f}"
        if self.outras_despesas_item is not None and self.outras_despesas_item > Decimal('0.00'):
            produto_nfelib.vOutro = f"{self.outras_despesas_item:.2f}"
        
        # Outros campos opcionais de <prod> (exemplos, adapte conforme seu modelo Produto)
        # if self.produto.cest:
        #     produto_nfelib.CEST = self.produto.cest
        # if self.produto.extipi:
        #     produto_nfelib.EXTIPI = self.produto.extipi
        # if self.produto.nfci: # Número de Controle da FCI
        #     produto_nfelib.nFCI = self.produto.nfci
        # if self.produto.indEscala: # 'S' ou 'N'
        #     produto_nfelib.indEscala = ProdIndEscala(self.produto.indEscala.upper())
        # if self.produto.cnpj_fabricante and produto_nfelib.indEscala == ProdIndEscala.S: # Obrigatório para escala relevante
        #     produto_nfelib.CNPJFab = self.produto.cnpj_fabricante
        # if self.produto.codigo_beneficio_fiscal_uf:
        #     produto_nfelib.cBenef = self.produto.codigo_beneficio_fiscal_uf

        # Adicionar outros grupos dentro de <prod> se necessário:
        # DI (Declaração de Importação), detExport, veicProd, med, arma, comb, etc.
        # Exemplo (muito simplificado) para DI:
        # if self.produto.is_importado and hasattr(self.produto, 'declaracoes_importacao'):
        #     produto_nfelib.DI = []
        #     for di_model in self.produto.declaracoes_importacao.all():
        #         di_nfelib = Tnfe.InfNfe.Det.Prod.Di()
        #         di_nfelib.nDI = di_model.numero_di
        #         di_nfelib.dDI = di_model.data_di.strftime('%Y-%m-%d')
        #         # ... preencher outros campos da DI ...
        #         produto_nfelib.DI.append(di_nfelib)
        
        return produto_nfelib
