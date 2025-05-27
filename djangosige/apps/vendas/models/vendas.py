# -*- coding: utf-8 -*-

from django.db import models
from django.template.defaultfilters import date
from django.core.validators import MinValueValidator
from django.urls import reverse_lazy

from decimal import Decimal

from djangosige.apps.fiscal.models import TributoPIS, TributoCOFINS
from djangosige.apps.estoque.models import DEFAULT_LOCAL_ID

import locale
# É mais seguro definir explicitamente. Descomente a linha apropriada ou use ''
# locale.setlocale(locale.LC_ALL, '') # Linha original comentada
try:
    # Tenta configurar para Português do Brasil com UTF-8 (comum em Linux/Mac)
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        # Tenta configurar para Português do Brasil (comum em Windows)
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252') # Ou 'Portuguese'
    except locale.Error:
        print("Aviso: Locale 'pt_BR' não pôde ser definido. Usando padrão do sistema.")
        try:
            locale.setlocale(locale.LC_ALL, '') # Fallback para padrão do sistema
        except locale.Error:
            print("Erro: Não foi possível definir nenhum locale.")
            # locale = None # Ou outra forma de indicar que locale falhou


STATUS_ORCAMENTO_ESCOLHAS = (
    (u'0', u'Aberto'),
    (u'1', u'Baixado'),
    (u'2', u'Cancelado'),
)

STATUS_PEDIDO_VENDA_ESCOLHAS = (
    (u'0', u'Aberto'),
    (u'1', u'Faturado'),
    (u'2', u'Cancelado'),
    (u'3', u'Importado por XML'),
)

TIPOS_DESCONTO_ESCOLHAS = (
    (u'0', u'Valor'),
    (u'1', u'Percentual'),
)

MOD_FRETE_ESCOLHAS = (
    (u'0', u'Por conta do emitente'),
    (u'1', u'Por conta do destinatário/remetente'),
    (u'2', u'Por conta de terceiros'),
    (u'9', u'Sem frete'),
)


class ItensVenda(models.Model):
    produto = models.ForeignKey('cadastro.Produto', related_name="venda_produto",
                                on_delete=models.CASCADE, null=True, blank=True)
    venda_id = models.ForeignKey(
        'vendas.Venda', related_name="itens_venda", on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                     MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    valor_unit = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                     MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    tipo_desconto = models.CharField(
        max_length=1, choices=TIPOS_DESCONTO_ESCOLHAS, null=True, blank=True, default='0')
    desconto = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    inf_ad_prod = models.CharField(max_length=500, null=True, blank=True)

    # Rateio
    valor_rateio_frete = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                             MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    valor_rateio_despesas = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                                MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    valor_rateio_seguro = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                              MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))

    # Bases de calculo
    vbc_icms = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vbc_icms_st = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                      MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vbc_ipi = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                  MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))

    # Valores e aliquotas
    vicms = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vicms_st = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vipi = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                               MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vfcp = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                               MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vicmsufdest = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                      MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vicmsufremet = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                       MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vicms_deson = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                      MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    p_icms = models.DecimalField(max_digits=5, decimal_places=2, validators=[
                                 MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    p_icmsst = models.DecimalField(max_digits=5, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    p_ipi = models.DecimalField(max_digits=5, decimal_places=2, validators=[
                                MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))

    # Valores do PIS e COFINS
    vq_bcpis = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vq_bccofins = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                      MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vpis = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                               MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))
    vcofins = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                  MinValueValidator(Decimal('0.00'))], null=True, blank=True, default=Decimal('0.00'))

    # Opcoes
    icms_incluido_preco = models.BooleanField(default=False)
    icmsst_incluido_preco = models.BooleanField(default=False)
    ipi_incluido_preco = models.BooleanField(default=False)
    incluir_bc_icms = models.BooleanField(
        default=False)  # incluir IPI na BC do ICMS
    incluir_bc_icmsst = models.BooleanField(
        default=False)  # incluir IPI na BC do ICMS-ST
    auto_calcular_impostos = models.BooleanField(default=True)

    @property
    def vprod(self):
        # Garante que temos valores decimais para calcular
        qtd = self.quantidade if self.quantidade is not None else Decimal('0')
        unit = self.valor_unit if self.valor_unit is not None else Decimal('0.00')
        return (qtd * unit).quantize(Decimal('0.01'))

    @property
    def vbc_uf_dest(self):
        # Garante que temos valores decimais
        sub = self.subtotal if self.subtotal is not None else Decimal('0.00')
        ipi = self.vipi if self.vipi is not None else Decimal('0.00')
        return (sub + ipi).quantize(Decimal('0.01'))

    @property
    def vicms_cred_sn(self):
        try:
            # Garante que temos valor decimal
            sub = self.subtotal if self.subtotal is not None else Decimal('0.00')
            if sub > 0 and self.produto and self.produto.grupo_fiscal and self.produto.grupo_fiscal.icms_sn_padrao:
                icms_obj = self.produto.grupo_fiscal.icms_sn_padrao.get()
                if icms_obj.p_cred_sn is not None:
                    p_cred = Decimal(icms_obj.p_cred_sn)
                    return (sub * p_cred / Decimal('100')).quantize(Decimal('0.01'))
        except Exception: # Captura DoesNotExist e outros possíveis erros
            pass
        return Decimal('0.00') # Retorna Decimal zero em caso de erro ou falta de dados

    # --- INÍCIO MÉTODO ADICIONADO ---
    def get_total(self):
        """
        Calcula o valor total para este item da venda.
        Exemplo: Quantidade * Valor Unitário - Desconto (se aplicável)
        """
        try:
            # Use Decimal para cálculos monetários
            quantidade = self.quantidade if self.quantidade is not None else Decimal('0')
            valor_unit = self.valor_unit if self.valor_unit is not None else Decimal('0.00')
            desconto_calc = self.get_valor_desconto(format=False) # Pega o valor do desconto calculado

            subtotal_bruto = quantidade * valor_unit
            total = subtotal_bruto - desconto_calc
            # Arredonda para 2 casas decimais (padrão para moeda)
            return total.quantize(Decimal('0.01'))
        except Exception:
            # Em caso de erro (ex: campos nulos não esperados), retorna 0
            return Decimal('0.00')
    # --- FIM MÉTODO ADICIONADO ---

    def get_valor_desconto(self, decimais=2, format=True):
        try:
            # Garante que temos valores decimais
            desconto_field = self.desconto if self.desconto is not None else Decimal('0.00')
            subtotal_bruto = self.vprod # Usa a property vprod que já calcula qtd * valor_unit

            if self.tipo_desconto == '0': # Valor
                valor_desconto = desconto_field
            elif self.tipo_desconto == '1': # Percentual
                valor_desconto = subtotal_bruto * (desconto_field / Decimal('100'))
            else: # Sem desconto ou tipo inválido
                valor_desconto = Decimal('0.00')

            valor_final = valor_desconto.quantize(Decimal('0.01') if decimais == 2 else Decimal('0.0001')) # Ajuste precisão

            if format and locale:
                 # Usa format_string e garante que é float para formatação
                 return locale.format_string(u'%.*f' % (decimais, valor_final), valor_final, grouping=True)
            else:
                 return valor_final # Retorna Decimal se format=False

        except Exception:
             return Decimal('0.00') if not format else "0,00"


    # --- INÍCIO SUBSTITUIÇÃO locale.format ---
    def format_desconto(self):
        # Usa a própria função get_valor_desconto com format=True
        return self.get_valor_desconto(format=True)

    def format_quantidade(self):
        qtd = self.quantidade if self.quantidade is not None else Decimal('0')
        if locale:
            # Tenta formatar como float, pode precisar ajustar para outros formatos de qtd
            return locale.format_string(u'%.2f', float(qtd), grouping=True)
        return str(qtd)

    def format_valor_unit(self):
        val = self.valor_unit if self.valor_unit is not None else Decimal('0.00')
        if locale:
            return locale.format_string(u'%.2f', val, grouping=True)
        return str(val)

    def format_total(self):
        # Chama o novo método get_total e formata o resultado Decimal
        total = self.get_total()
        if locale:
            return locale.format_string(u'%.2f', total, grouping=True)
        return str(total)


    def format_vprod(self):
        vprod_val = self.vprod # Usa a property vprod
        if locale:
            return locale.format_string(u'%.2f', vprod_val, grouping=True)
        return str(vprod_val)
    # --- FIM SUBSTITUIÇÃO locale.format ---


    def get_total_sem_desconto(self):
        # Calcula Qtd * Vl Unitário
        return self.vprod

    def get_mot_deson_icms(self):
        try:
            if self.produto and self.produto.grupo_fiscal and self.produto.grupo_fiscal.icms_padrao:
                icms_obj = self.produto.grupo_fiscal.icms_padrao.get()
                if icms_obj.mot_des_icms:
                    return icms_obj.get_mot_des_icms_display()
        except Exception:
            pass
        return ''

    def get_total_impostos(self):
        # Soma os campos de impostos existentes, tratando None como 0
        vicms = self.vicms if self.vicms is not None else Decimal('0.00')
        vicms_st = self.vicms_st if self.vicms_st is not None else Decimal('0.00')
        vipi = self.vipi if self.vipi is not None else Decimal('0.00')
        vfcp = self.vfcp if self.vfcp is not None else Decimal('0.00')
        vicmsufdest = self.vicmsufdest if self.vicmsufdest is not None else Decimal('0.00')
        vicmsufremet = self.vicmsufremet if self.vicmsufremet is not None else Decimal('0.00')
        return (vicms + vicms_st + vipi + vfcp + vicmsufdest + vicmsufremet).quantize(Decimal('0.01'))

    # --- INÍCIO SUBSTITUIÇÃO locale.format ---
    def format_total_impostos(self):
        total_imp = self.get_total_impostos()
        if locale:
            return locale.format_string(u'%.2f', total_imp, grouping=True)
        return str(total_imp)
    # --- FIM SUBSTITUIÇÃO locale.format ---

    def get_total_com_impostos(self):
        # Usa o subtotal (que já considera o desconto do item) e soma os impostos
        subtotal_item = self.get_total() # Usa o novo método
        total_impostos_item = self.get_total_impostos()
        return (subtotal_item + total_impostos_item).quantize(Decimal('0.01'))

    # --- INÍCIO SUBSTITUIÇÃO locale.format ---
    def format_total_com_imposto(self):
        total_com_imp = self.get_total_com_impostos()
        if locale:
            return locale.format_string(u'%.2f', total_com_imp, grouping=True)
        return str(total_com_imp)

    def format_valor_attr(self, nome_attr):
        try:
            valor = getattr(self, nome_attr)
            if valor is not None and isinstance(valor, (Decimal, int, float)):
                 valor_decimal = Decimal(valor)
                 if locale:
                     return locale.format_string(u'%.2f', valor_decimal, grouping=True)
                 return str(valor_decimal.quantize(Decimal('0.01')))
            elif valor is not None:
                 return str(valor) # Retorna como string se não for numérico
        except AttributeError:
            pass
        return '' # Retorna vazio se atributo não existe ou é None
    # --- FIM SUBSTITUIÇÃO locale.format ---

    def get_aliquota_pis(self, format=True):
        valor = None
        try:
            if self.produto and self.produto.grupo_fiscal:
                 pis_padrao = PIS.objects.get(
                     grupo_fiscal=self.produto.grupo_fiscal)

                 if pis_padrao.valiq_pis is not None:
                     valor = Decimal(pis_padrao.valiq_pis)
                 elif pis_padrao.p_pis is not None:
                     valor = Decimal(pis_padrao.p_pis)

        except PIS.DoesNotExist:
            pass # Continua para retornar None ou valor formatado de None

        if valor is not None:
            if format and locale:
                # --- INÍCIO SUBSTITUIÇÃO locale.format ---
                return locale.format_string(u'%.2f', valor, grouping=True)
                # --- FIM SUBSTITUIÇÃO locale.format ---
            else:
                return valor.quantize(Decimal('0.01')) # Retorna Decimal
        else:
            return "0,00" if format else Decimal('0.00')


    def get_aliquota_cofins(self, format=True):
        valor = None
        try:
            if self.produto and self.produto.grupo_fiscal:
                 cofins_padrao = COFINS.objects.get(
                     grupo_fiscal=self.produto.grupo_fiscal)

                 if cofins_padrao.valiq_cofins is not None:
                      valor = Decimal(cofins_padrao.valiq_cofins)
                 elif cofins_padrao.p_cofins is not None:
                      valor = Decimal(cofins_padrao.p_cofins)

        except COFINS.DoesNotExist:
            pass # Continua para retornar None ou valor formatado de None

        if valor is not None:
            if format and locale:
                # --- INÍCIO SUBSTITUIÇÃO locale.format ---
                return locale.format_string(u'%.2f', valor, grouping=True)
                # --- FIM SUBSTITUIÇÃO locale.format ---
            else:
                 return valor.quantize(Decimal('0.01')) # Retorna Decimal
        else:
             return "0,00" if format else Decimal('0.00')


    def calcular_pis_cofins(self):
        # Garante que subtotal é Decimal
        subtotal_item = self.get_total() # Usa o total após desconto do item como base
        vbc = subtotal_item # Base de cálculo inicial

        # Adiciona despesas rateadas se existirem
        despesas_rateio = self.valor_rateio_despesas if self.valor_rateio_despesas is not None else Decimal('0.00')
        vbc += despesas_rateio

        if self.produto and self.produto.grupo_fiscal:
            try:
                pis_padrao = PIS.objects.get(grupo_fiscal=self.produto.grupo_fiscal)
                cofins_padrao = COFINS.objects.get(grupo_fiscal=self.produto.grupo_fiscal)

                # Calculo Vl. PIS
                if pis_padrao.valiq_pis is not None:
                    self.vq_bcpis = self.quantidade if self.quantidade is not None else Decimal('0')
                    self.vpis = (self.vq_bcpis * Decimal(pis_padrao.valiq_pis)).quantize(Decimal('0.01'))
                elif pis_padrao.p_pis is not None:
                    self.vq_bcpis = vbc.quantize(Decimal('0.01'))
                    self.vpis = (vbc * (Decimal(pis_padrao.p_pis) / Decimal('100'))).quantize(Decimal('0.01'))
                else:
                     self.vq_bcpis = Decimal('0.00')
                     self.vpis = Decimal('0.00')


                # Calculo Vl. COFINS
                if cofins_padrao.valiq_cofins is not None:
                    self.vq_bccofins = self.quantidade if self.quantidade is not None else Decimal('0')
                    self.vcofins = (self.vq_bccofins * Decimal(cofins_padrao.valiq_cofins)).quantize(Decimal('0.01'))
                elif cofins_padrao.p_cofins is not None:
                    self.vq_bccofins = vbc.quantize(Decimal('0.01'))
                    self.vcofins = (vbc * (Decimal(cofins_padrao.p_cofins) / Decimal('100'))).quantize(Decimal('0.01'))
                else:
                     self.vq_bccofins = Decimal('0.00')
                     self.vcofins = Decimal('0.00')


            except (PIS.DoesNotExist, COFINS.DoesNotExist):
                self.vq_bcpis = Decimal('0.00')
                self.vpis = Decimal('0.00')
                self.vq_bccofins = Decimal('0.00')
                self.vcofins = Decimal('0.00')
            except Exception: # Outros erros
                 self.vq_bcpis = Decimal('0.00')
                 self.vpis = Decimal('0.00')
                 self.vq_bccofins = Decimal('0.00')
                 self.vcofins = Decimal('0.00')
        else:
            # Se não há grupo fiscal, zera PIS/COFINS
            self.vq_bcpis = Decimal('0.00')
            self.vpis = Decimal('0.00')
            self.vq_bccofins = Decimal('0.00')
            self.vcofins = Decimal('0.00')

        # O save() deve ser chamado fora deste método, onde ele for invocado.


class Venda(models.Model):
    # Cliente
    cliente = models.ForeignKey(
        'cadastro.Cliente', related_name="venda_cliente", on_delete=models.CASCADE)
    ind_final = models.BooleanField(default=False)
    # Transporte
    transportadora = models.ForeignKey(
        'cadastro.Transportadora', related_name="venda_transportadora", on_delete=models.CASCADE, null=True, blank=True)
    veiculo = models.ForeignKey('cadastro.Veiculo', related_name="venda_veiculo",
                                on_delete=models.SET_NULL, null=True, blank=True)
    mod_frete = models.CharField(
        max_length=1, choices=MOD_FRETE_ESCOLHAS, default='9')
    # Estoque
    local_orig = models.ForeignKey(
        'estoque.LocalEstoque', related_name="venda_local_estoque", default=DEFAULT_LOCAL_ID, on_delete=models.PROTECT)
    movimentar_estoque = models.BooleanField(default=True)
    # Info
    data_emissao = models.DateField(null=True, blank=True)
    vendedor = models.CharField(max_length=255, null=True, blank=True)
    valor_total = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                      MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    tipo_desconto = models.CharField(
        max_length=1, choices=TIPOS_DESCONTO_ESCOLHAS, default='0')
    desconto = models.DecimalField(max_digits=15, decimal_places=4, validators=[
                                   MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    despesas = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    frete = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    seguro = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                 MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    impostos = models.DecimalField(max_digits=13, decimal_places=2, validators=[
                                   MinValueValidator(Decimal('0.00'))], default=Decimal('0.00'))
    cond_pagamento = models.ForeignKey(
        'vendas.CondicaoPagamento', related_name="venda_pagamento", on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.CharField(max_length=1055, null=True, blank=True)

    def get_total_sem_imposto(self):
        # Garante que temos valores decimais
        total = self.valor_total if self.valor_total is not None else Decimal('0.00')
        imp = self.impostos if self.impostos is not None else Decimal('0.00')
        return (total - imp).quantize(Decimal('0.01'))

    def get_total_produtos(self):
        # Soma o vprod de cada item
        return sum(item.vprod for item in self.itens_venda.all() if item.vprod is not None)

    # --- INÍCIO MÉTODO ADICIONADO ---
    def get_total_impostos(self):
        """Soma o valor total de impostos de todos os itens da venda."""
        total_impostos_itens = sum(item.get_total_impostos() for item in self.itens_venda.all())
        # Se o campo 'impostos' na Venda for usado para algo adicional (ex: imposto global), some aqui.
        # Caso contrário, apenas retorne a soma dos itens.
        # imposto_venda = self.impostos if self.impostos is not None else Decimal('0.00')
        # return (total_impostos_itens + imposto_venda).quantize(Decimal('0.01'))
        return Decimal(total_impostos_itens).quantize(Decimal('0.01')) # Converte para Decimal antes
    # --- FIM MÉTODO ADICIONADO ---

    def get_total_produtos_estoque(self):
        itens = self.itens_venda.all()
        tot = Decimal('0.00')
        for it in itens:
            if it.produto and it.produto.controlar_estoque:
                tot += it.vprod # Usa a property vprod
        return tot.quantize(Decimal('0.01'))

    # --- INÍCIO SUBSTITUIÇÃO locale.format ---
    def format_total_produtos(self):
        total_prod = self.get_total_produtos()
        if locale:
            return locale.format_string(u'%.2f', total_prod, grouping=True)
        return str(total_prod)
    # --- FIM SUBSTITUIÇÃO locale.format ---

    @property
    def format_data_emissao(self):
        if self.data_emissao:
            return '%s' % date(self.data_emissao, "d/m/Y")
        return ''

    def get_valor_desconto_total(self, decimais=2):
        try:
            desconto_field = self.desconto if self.desconto is not None else Decimal('0.00')

            if self.tipo_desconto == '0': # Valor
                valor_desconto = desconto_field
            elif self.tipo_desconto == '1': # Percentual
                 # Base para percentual: soma dos subtotais dos itens (após desconto de item)
                 base_desconto = sum(item.get_total() for item in self.itens_venda.all())
                 valor_desconto = base_desconto * (desconto_field / Decimal('100'))
            else:
                 valor_desconto = Decimal('0.00')

            return valor_desconto.quantize(Decimal('0.01') if decimais == 2 else Decimal('0.0001'))
        except Exception:
             return Decimal('0.00')


    # --- INÍCIO SUBSTITUIÇÃO locale.format ---
    def format_valor_total(self):
        total = self.valor_total if self.valor_total is not None else Decimal('0.00')
        if locale:
            return locale.format_string(u'%.2f', total, grouping=True)
        return str(total)

    def format_frete(self):
        val = self.frete if self.frete is not None else Decimal('0.00')
        if locale:
            return locale.format_string(u'%.2f', val, grouping=True)
        return str(val)

    def format_impostos(self):
        # Usa o novo método para garantir consistência
        total_imp = self.get_total_impostos()
        if locale:
            return locale.format_string(u'%.2f', total_imp, grouping=True)
        return str(total_imp)

    def format_total_sem_imposto(self):
        total_sem_imp = self.get_total_sem_imposto()
        if locale:
            return locale.format_string(u'%.2f', total_sem_imp, grouping=True)
        return str(total_sem_imp)

    def format_desconto(self):
        # Usa a própria função get_valor_desconto_total com format=False e formata aqui
        desconto_calculado = self.get_valor_desconto_total(format=False)
        if locale:
            return locale.format_string(u'%.2f', desconto_calculado, grouping=True)
        return str(desconto_calculado)

    def format_seguro(self):
        val = self.seguro if self.seguro is not None else Decimal('0.00')
        if locale:
            return locale.format_string(u'%.2f', val, grouping=True)
        return str(val)

    def format_despesas(self):
        val = self.despesas if self.despesas is not None else Decimal('0.00')
        if locale:
            return locale.format_string(u'%.2f', val, grouping=True)
        return str(val)

    def format_total_sem_desconto(self):
         # Base para desconto percentual é a soma dos totais dos itens
         base = sum(item.get_total() for item in self.itens_venda.all())
         desconto_total = self.get_valor_desconto_total(format=False)
         total_sem_desconto_geral = base - desconto_total # Isso pode não ser o que o método originalmente queria dizer
                                                          # Se for simplesmente valor_total - desconto, use a linha abaixo
         # total_sem_desconto = (self.valor_total if self.valor_total is not None else Decimal('0.00')) - desconto_total
         # return locale.format_string(u'%.2f', total_sem_desconto.quantize(Decimal('0.01')), grouping=True) if locale else str(total_sem_desconto.quantize(Decimal('0.01')))

         # Vamos manter a lógica original (valor_total - desconto), mas usando o método calculado
         total_liquido = self.valor_total if self.valor_total is not None else Decimal('0.00')
         total_sem_desconto = total_liquido # Se o desconto já está embutido no valor_total, isso pode estar errado
                                            # Precisaria revisar como valor_total é calculado/salvo.
                                            # Por ora, apenas formatamos o valor_total - desconto calculado
         total_sem_desc = total_liquido - desconto_total
         if locale:
              return locale.format_string(u'%.2f', total_sem_desc.quantize(Decimal('0.01')), grouping=True)
         return str(total_sem_desc.quantize(Decimal('0.01')))

    # --- FIM SUBSTITUIÇÃO locale.format ---


    def get_forma_pagamento(self):
        if self.cond_pagamento:
            return self.cond_pagamento.get_forma_display()
        else:
            return ""

    def get_local_orig_id(self):
        if self.local_orig:
            return self.local_orig.id
        else:
            return ""

    def get_valor_total_attr(self, nome_attr):
        # Soma um atributo específico de todos os itens
        valor_total = Decimal('0.00')
        for item in self.itens_venda.all():
            v = getattr(item, nome_attr, Decimal('0.00')) # Pega o atributo, default 0
            if v is not None:
                try:
                    valor_total += Decimal(v) # Soma como Decimal
                except Exception: # Ignora se não puder converter
                    pass
        return valor_total.quantize(Decimal('0.01'))

    def get_child(self):
        # Determina se é um OrcamentoVenda ou PedidoVenda (usado por models antigos?)
        if hasattr(self, 'orcamentovenda'):
            return self.orcamentovenda
        elif hasattr(self, 'pedidovenda'):
            return self.pedidovenda
        else:
            # Tenta pela PK (pode ser ineficiente)
            try:
                return PedidoVenda.objects.get(pk=self.pk)
            except PedidoVenda.DoesNotExist:
                try:
                    return OrcamentoVenda.objects.get(pk=self.pk)
                except OrcamentoVenda.DoesNotExist:
                    return self # Retorna a instância base se não encontrar filhos
            except Exception:
                 return self # Fallback

    def __unicode__(self):
        # Mantido por compatibilidade se necessário, mas __str__ é o padrão
        s = u'Venda nº %s' % (self.id)
        return s

    def __str__(self):
        tipo = self.tipo_venda if hasattr(self, 'tipo_venda') else 'Venda'
        s = f'{tipo} nº {self.pk or "(Novo)"}'
        if hasattr(self, 'status'):
             s += f' ({self.get_status_display()})'
        return s


class OrcamentoVenda(Venda):
    data_vencimento = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=1, choices=STATUS_ORCAMENTO_ESCOLHAS, default='0')

    class Meta:
        verbose_name = "Orçamento de Venda"

    @property
    def format_data_vencimento(self):
        if self.data_vencimento:
            return '%s' % date(self.data_vencimento, "d/m/Y")
        return ''

    @property
    def tipo_venda(self):
        return 'Orçamento'

    def edit_url(self):
        return reverse_lazy('vendas:editarorcamentovendaview', kwargs={'pk': self.id})

    # __unicode__ e __str__ são herdados de Venda, mas podemos sobrescrever se necessário
    # def __str__(self):
    #    s = u'Orçamento de venda nº %s (%s)' % (self.id, self.get_status_display())
    #    return s


class PedidoVenda(Venda):
    orcamento = models.ForeignKey(
        'vendas.OrcamentoVenda', related_name="orcamento_pedido", on_delete=models.SET_NULL, null=True, blank=True)
    data_entrega = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=1, choices=STATUS_PEDIDO_VENDA_ESCOLHAS, default='0')

    class Meta:
        verbose_name = "Pedido de Venda"
        permissions = (
            ("faturar_pedidovenda", "Pode faturar Pedidos de Venda"),
        )

    @property
    def format_data_entrega(self):
        if self.data_entrega:
            return '%s' % date(self.data_entrega, "d/m/Y")
        return ''

    @property
    def tipo_venda(self):
        return 'Pedido'

    def edit_url(self):
        return reverse_lazy('vendas:editarpedidovendaview', kwargs={'pk': self.id})

    # __unicode__ e __str__ são herdados de Venda, podemos sobrescrever:
    # def __str__(self):
    #    s = u'Pedido de venda nº %s (%s)' % (self.id, self.get_status_display())
    #    return s

