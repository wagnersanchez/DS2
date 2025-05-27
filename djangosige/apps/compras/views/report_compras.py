# -*- coding: utf-8 -*-
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Image, Frame, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from djangosige.apps.compras.models import ItensCompra, Pagamento
from django.conf import settings
import os

# Font configurations
REPORT_FONT = 'Helvetica'
REPORT_FONT_BOLD = 'Helvetica-Bold'

class CompraReport:
    def __init__(self, buffer=None, pagesize=A4):
        self.buffer = buffer if buffer else BytesIO()
        self.pagesize = pagesize
        self.width, self.height = self.pagesize
        self.styles = getSampleStyleSheet()
        
        # Custom styles configuration
        self._configure_styles()
        
    def _configure_styles(self):
        """Configure custom styles for the report"""
        self.styles.add(ParagraphStyle(
            name='Header1',
            fontName=REPORT_FONT_BOLD,
            fontSize=14,
            leading=15,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Header2',
            fontName=REPORT_FONT_BOLD,
            fontSize=12,
            leading=12,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='Normal',
            fontName=REPORT_FONT,
            fontSize=10,
            leading=12,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='Right',
            fontName=REPORT_FONT,
            fontSize=10,
            leading=12,
            alignment=TA_RIGHT,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='Bold',
            fontName=REPORT_FONT_BOLD,
            fontSize=10,
            leading=12,
            spaceAfter=6
        ))

    def generate_report(self, compra, user=None):
        """Generate the complete purchase report"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pagesize,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=20*mm,
            bottomMargin=15*mm
        )
        
        elements = []
        
        # Add header with company info
        elements += self._generate_header(compra, user)
        
        # Document title
        doc_title = "ORÇAMENTO DE COMPRA" if compra.__class__.__name__ == 'OrcamentoCompra' else "PEDIDO DE COMPRA"
        elements.append(Paragraph(doc_title, self.styles['Header1']))
        
        # Document info (number and dates)
        elements += self._generate_document_info(compra)
        elements.append(Spacer(1, 10*mm))
        
        # Supplier information
        elements += self._generate_fornecedor_section(compra)
        elements.append(Spacer(1, 5*mm))
        
        # Products table
        elements += self._generate_produtos_section(compra)
        elements.append(Spacer(1, 5*mm))
        
        # Payment conditions
        elements += self._generate_payment_conditions(compra)
        elements.append(Spacer(1, 5*mm))
        
        # Payment schedule
        elements += self._generate_pagamentos_section(compra)
        elements.append(Spacer(1, 5*mm))
        
        # Totals summary
        elements += self._generate_totals_section(compra)
        elements.append(Spacer(1, 10*mm))
        
        # Observations
        elements += self._generate_observations(compra)
        
        # Footer
        elements += self._generate_footer()
        
        doc.build(elements, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf

    def _generate_header(self, compra, user):
        """Generate header with company logo and info"""
        section = []
        
        try:
            if user and hasattr(user, 'm_empresa') and user.m_empresa.m_empresa.logo_file:
                logo_path = os.path.join(settings.MEDIA_ROOT, str(user.m_empresa.m_empresa.logo_file))
                if os.path.exists(logo_path):
                    logo = Image(logo_path, width=50*mm, height=20*mm)
                    logo.hAlign = 'CENTER'
                    section.append(logo)
                    section.append(Spacer(1, 5*mm))
            
            if user and hasattr(user, 'm_empresa'):
                empresa = user.m_empresa.m_empresa
                section.append(Paragraph(empresa.nome_razao_social, self.styles['Header2']))
                
                if hasattr(empresa, 'endereco_padrao'):
                    endereco = empresa.endereco_padrao
                    section.append(Paragraph(endereco.format_endereco_completo, self.styles['Normal']))
                
                if hasattr(empresa, 'telefone_padrao'):
                    section.append(Paragraph(f"Telefone: {empresa.telefone_padrao.telefone}", self.styles['Normal']))
                
                if hasattr(empresa, 'email_padrao'):
                    section.append(Paragraph(f"Email: {empresa.email_padrao.email}", self.styles['Normal']))
                
                section.append(Spacer(1, 5*mm))
        except:
            pass
            
        return section

    def _generate_document_info(self, compra):
        """Generate document number and dates section"""
        section = []
        
        data = [
            ['Número:', str(compra.id), 'Emissão:', compra.data_emissao.strftime('%d/%m/%Y')]
        ]
        
        if hasattr(compra, 'data_vencimento'):
            data[0].extend(['Validade:', compra.data_vencimento.strftime('%d/%m/%Y')])
        elif hasattr(compra, 'data_entrega'):
            data[0].extend(['Entrega:', compra.data_entrega.strftime('%d/%m/%Y') if compra.data_entrega else ''])
        
        table = Table(data, colWidths=[20*mm, 30*mm, 20*mm, 30*mm, 20*mm, 30*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), REPORT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        section.append(table)
        return section

    def _generate_fornecedor_section(self, compra):
        """Generate supplier information section"""
        section = []
        fornecedor = compra.fornecedor
        
        section.append(Paragraph('FORNECEDOR', self.styles['Header2']))
        
        # Basic info table
        data = [
            ['Nome/Razão Social:', fornecedor.nome_razao_social]
        ]
        
        # Document info
        if hasattr(fornecedor, 'pessoa_jur_info'):
            doc_info = fornecedor.pessoa_jur_info
            data.append(['CNPJ:', doc_info.format_cnpj()])
            if doc_info.inscricao_estadual:
                data.append(['Inscrição Estadual:', doc_info.format_ie()])
        else:
            doc_info = fornecedor.pessoa_fis_info
            data.append(['CPF:', doc_info.format_cpf()])
            if hasattr(doc_info, 'rg'):
                data.append(['RG:', doc_info.format_rg()])
        
        # Contact info
        if hasattr(fornecedor, 'endereco_padrao'):
            endereco = fornecedor.endereco_padrao
            data.append(['Endereço:', endereco.format_endereco()])
            data.append(['Cidade/UF:', f"{endereco.municipio}/{endereco.uf}"])
            if endereco.cep:
                data.append(['CEP:', endereco.cep])
        
        if hasattr(fornecedor, 'telefone_padrao'):
            data.append(['Telefone:', fornecedor.telefone_padrao.telefone])
        
        if hasattr(fornecedor, 'email_padrao'):
            data.append(['Email:', fornecedor.email_padrao.email])
        
        table = Table(data, colWidths=[40*mm, 130*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), REPORT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        section.append(table)
        return section

    def _generate_produtos_section(self, compra):
        """Generate products table section"""
        section = []
        produtos = ItensCompra.objects.filter(compra_id=compra)
        
        section.append(Paragraph('PRODUTOS/SERVIÇOS', self.styles['Header2']))
        
        if not produtos.exists():
            section.append(Paragraph('Nenhum produto encontrado.', self.styles['Normal']))
            return section
        
        # Table header
        data = [
            [
                'Código', 'Descrição', 'Unid.', 'Quant.', 
                'Vl. Unit.', 'Desconto', 'Vl. Total'
            ]
        ]
        
        # Table rows
        for item in produtos:
            data.append([
                item.produto.codigo,
                item.produto.descricao,
                item.produto.unidade,
                str(item.quantidade),
                f'R$ {item.valor_unit:,.2f}',
                f'R$ {item.desconto:,.2f}' if item.desconto else '-',
                f'R$ {item.get_total():,.2f}'
            ])
        
        # Create table
        table = Table(data, colWidths=[20*mm, 50*mm, 15*mm, 15*mm, 20*mm, 20*mm, 20*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3A4F57')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), REPORT_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        section.append(table)
        return section

    def _generate_payment_conditions(self, compra):
        """Generate payment conditions section"""
        section = []
        
        if not compra.cond_pagamento:
            return section
            
        section.append(Paragraph('CONDIÇÕES DE PAGAMENTO', self.styles['Header2']))
        section.append(Paragraph(compra.cond_pagamento.descricao, self.styles['Normal']))
        
        return section

    def _generate_pagamentos_section(self, compra):
        """Generate payment schedule section"""
        section = []
        pagamentos = Pagamento.objects.filter(compra_id=compra).order_by('vencimento')
        
        if not pagamentos.exists():
            return section
            
        section.append(Paragraph('PAGAMENTOS', self.styles['Header2']))
        
        data = [
            ['Parcela', 'Vencimento', 'Valor', 'Status']
        ]
        
        for pagamento in pagamentos:
            data.append([
                str(pagamento.indice_parcela),
                pagamento.vencimento.strftime('%d/%m/%Y'),
                f'R$ {pagamento.valor:,.2f}',
                pagamento.get_status_display()
            ])
        
        table = Table(data, colWidths=[20*mm, 40*mm, 30*mm, 30*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3A4F57')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), REPORT_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        section.append(table)
        return section

    def _generate_totals_section(self, compra):
        """Generate totals summary section"""
        section = []
        
        data = [
            ['Subtotal:', f'R$ {compra.get_total_produtos():,.2f}'],
            ['Desconto:', f'R$ {compra.desconto:,.2f}' if compra.desconto else 'R$ 0,00'],
            ['Frete:', f'R$ {compra.frete:,.2f}' if compra.frete else 'R$ 0,00'],
            ['Despesas:', f'R$ {compra.despesas:,.2f}' if compra.despesas else 'R$ 0,00'],
            ['Seguro:', f'R$ {compra.seguro:,.2f}' if compra.seguro else 'R$ 0,00'],
            ['Total:', f'R$ {compra.valor_total:,.2f}']
        ]
        
        table = Table(data, colWidths=[30*mm, 30*mm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), REPORT_FONT),
            ('FONTNAME', (0, -1), (-1, -1), REPORT_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('SPAN', (0, -1), (-1, -1)),
        ]))
        
        section.append(table)
        return section

    def _generate_observations(self, compra):
        """Generate observations section"""
        section = []
        
        if not compra.observacoes:
            return section
            
        section.append(Paragraph('OBSERVAÇÕES', self.styles['Header2']))
        section.append(Paragraph(compra.observacoes, self.styles['Normal']))
        
        return section

    def _generate_footer(self):
        """Generate footer section"""
        section = []
        section.append(Spacer(1, 10*mm))
        section.append(Paragraph('_________________________________________', self.styles['Normal']))
        section.append(Paragraph('Assinatura', self.styles['Normal']))
        return section

    def _add_page_number(self, canvas, doc):
        """Add page number to each page"""
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.setFont(REPORT_FONT, 8)
        canvas.drawRightString(200*mm, 10*mm, text)