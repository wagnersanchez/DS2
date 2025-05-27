# -*- coding: utf-8 -*-

from django.db import models
from decimal import Decimal
import re # Adicione esta linha se não existir no topo do arquivo cliente.py

from .base import Pessoa, PessoaFisica, PessoaJuridica # Importe PessoaFisica/Juridica se necessário

INDICADOR_IE_DEST = [
    ('1', 'Contribuinte ICMS'),
    ('2', 'Contribuinte isento de Inscrição'),
    ('9', 'Não Contribuinte'),
]


class Cliente(Pessoa):
    limite_de_credito = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    indicador_ie = models.CharField(
        max_length=1, choices=INDICADOR_IE_DEST, default='9')
    id_estrangeiro = models.CharField(max_length=20, null=True, blank=True)

    # --- INÍCIO DA CORREÇÃO/ADIÇÃO ---
    def format_cpf_cnpj(self):
        """
        Formata o CPF ou CNPJ para exibição.
        Busca a informação nos modelos relacionados PessoaFisica ou PessoaJuridica.
        """
        try:
            if self.tipo_pessoa == 'PJ':
                # Verifica se a relação pessoa_jur_info existe e tem o atributo cnpj
                if hasattr(self, 'pessoa_jur_info') and hasattr(self.pessoa_jur_info, 'cnpj') and self.pessoa_jur_info.cnpj:
                    cnpj_val = re.sub(r'[^0-9]', '', self.pessoa_jur_info.cnpj) # Garante apenas dígitos
                    if len(cnpj_val) == 14:
                        return f'{cnpj_val[:2]}.{cnpj_val[2:5]}.{cnpj_val[5:8]}/{cnpj_val[8:12]}-{cnpj_val[12:]}'
                    else:
                        return self.pessoa_jur_info.cnpj # Retorna sem formatação se o tamanho for inesperado
                else:
                    return "(CNPJ não informado)"

            elif self.tipo_pessoa == 'PF':
                 # Verifica se a relação pessoa_fis_info existe e tem o atributo cpf
                if hasattr(self, 'pessoa_fis_info') and hasattr(self.pessoa_fis_info, 'cpf') and self.pessoa_fis_info.cpf:
                    cpf_val = re.sub(r'[^0-9]', '', self.pessoa_fis_info.cpf) # Garante apenas dígitos
                    if len(cpf_val) == 11:
                        return f'{cpf_val[:3]}.{cpf_val[3:6]}.{cpf_val[6:9]}-{cpf_val[9:]}'
                    else:
                         return self.pessoa_fis_info.cpf # Retorna sem formatação se o tamanho for inesperado
                else:
                    return "(CPF não informado)"

            else:
                return "(Tipo de pessoa inválido)"

        except (AttributeError, PessoaFisica.DoesNotExist, PessoaJuridica.DoesNotExist):
            # Captura erros caso a relação não exista ou não esteja carregada
            # (AttributeError é mais provável se a relação não foi criada no banco)
             return "(Erro ao acessar CPF/CNPJ)"
        except Exception:
            # Captura outros erros inesperados
            return "(Erro na formatação CPF/CNPJ)"
    # --- FIM DA CORREÇÃO/ADIÇÃO ---

    class Meta:
        verbose_name = "Cliente"