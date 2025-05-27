from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class TributoPIS(models.Model):
    CST_CHOICES = [
        ('01', '01 - Operação Tributável com Alíquota Básica'),
        ('02', '02 - Operação Tributável com Alíquota Diferenciada'),
        ('03', '03 - Operação Tributável com Alíquota por Unidade de Medida'),
        ('04', '04 - Operação Tributável Monofásica - Revenda a Alíquota Zero'),
        ('05', '05 - Operação Tributável por Substituição Tributária'),
        ('06', '06 - Operação Tributável a Alíquota Zero'),
        ('07', '07 - Operação Isenta da Contribuição'),
        ('08', '08 - Operação sem Incidência da Contribuição'),
        ('09', '09 - Operação com Suspensão da Contribuição'),
        ('49', '49 - Outras Operações de Saída'),
        ('50', '50 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
        ('51', '51 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Não Tributada no Mercado Interno'),
        ('52', '52 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita de Exportação'),
        ('53', '53 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
        ('54', '54 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
        ('55', '55 - Operação com Direito a Crédito - Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação'),
        ('56', '56 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação'),
        ('60', '60 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
        ('61', '61 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno'),
        ('62', '62 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação'),
        ('63', '63 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
        ('64', '64 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
        ('65', '65 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação'),
        ('66', '66 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação'),
        ('67', '67 - Crédito Presumido - Outras Operações'),
        ('70', '70 - Operação de Aquisição sem Direito a Crédito'),
        ('71', '71 - Operação de Aquisição com Isenção'),
        ('72', '72 - Operação de Aquisição com Suspensão'),
        ('73', '73 - Operação de Aquisição a Alíquota Zero'),
        ('74', '74 - Operação de Aquisição sem Incidência da Contribuição'),
        ('75', '75 - Operação de Aquisição por Substituição Tributária'),
        ('98', '98 - Operação de Aquisição sem Incidência da Contribuição'),
        ('99', '99 - Outras Operações'),
    ]
    
    item = models.ForeignKey(
        'fiscal.ItemNotaFiscal',
        verbose_name='Item da Nota',
        on_delete=models.CASCADE,
        related_name='pis'
    )
    cst = models.CharField(
        'CST',
        max_length=2,
        choices=CST_CHOICES
    )
    valor_bc = models.DecimalField(
        'Valor BC',
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    aliquota = models.DecimalField(
        'Alíquota (%)',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    valor_pis = models.DecimalField(
        'Valor PIS',
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    
    class Meta:
        verbose_name = "Tributo PIS"
        verbose_name_plural = "Tributos PIS"
    
    def clean(self):
        """Validações específicas por CST"""
        errors = {}
        
        if self.cst in ['01', '02']:
            if not self.aliquota:
                errors['aliquota'] = "Alíquota é obrigatória para este CST"
            if not self.valor_bc:
                errors['valor_bc'] = "Base de cálculo é obrigatória para este CST"
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Calcula valor_pis automaticamente"""
        if self.aliquota and self.valor_bc:
            self.valor_pis = self.valor_bc * (self.aliquota / 100)
        
        super().save(*args, **kwargs)
    
    def to_edoc(self):
        """Converte para formato do erpbrasil.edoc"""
        pis = {
            'CST': self.cst,
            'vPIS': str(self.valor_pis)
        }
        
        if self.valor_bc:
            pis['vBC'] = str(self.valor_bc)
        
        if self.aliquota:
            pis['pPIS'] = str(self.aliquota)
        
        return {
            'PIS': {
                'PIS'+self.cst: pis
            }
        }