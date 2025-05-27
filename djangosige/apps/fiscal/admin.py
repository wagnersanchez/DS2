from django.contrib import admin
from .models import (
    NaturezaOperacao,
    NotaFiscal,
    ItemNotaFiscal,
    TributoICMS,
    TributoIPI,
    TributoPIS,
    TributoCOFINS
)

class ItemNotaFiscalInline(admin.TabularInline):
    model = ItemNotaFiscal
    extra = 1
    fields = ('ordem', 'produto', 'quantidade', 'valor_unitario', 'valor_total')
    readonly_fields = ('valor_total',)

class TributoICMSInline(admin.TabularInline):
    model = TributoICMS
    extra = 1

class TributoIPIInline(admin.TabularInline):
    model = TributoIPI
    extra = 1

class TributoPISInline(admin.TabularInline):
    model = TributoPIS
    extra = 1

class TributoCOFINSInline(admin.TabularInline):
    model = TributoCOFINS
    extra = 1

class ItemNotaFiscalAdmin(admin.ModelAdmin):
    inlines = [
        TributoICMSInline,
        TributoIPIInline,
        TributoPISInline,
        TributoCOFINSInline,
    ]
    list_display = ('nota_fiscal', 'ordem', 'produto', 'quantidade', 'valor_unitario', 'valor_total')
    list_filter = ('nota_fiscal',)

class NotaFiscalAdmin(admin.ModelAdmin):
    inlines = [ItemNotaFiscalInline]
    list_display = ('numero', 'serie', 'emitente', 'destinatario', 'status', 'valor_total_nota')
    list_filter = ('status', 'emitente', 'data_emissao')
    search_fields = ('numero', 'serie', 'chave', 'protocolo')
    readonly_fields = ('valor_total_nota', 'valor_total_produtos', 'valor_icms', 'valor_ipi', 'valor_pis', 'valor_cofins')

admin.site.register(NaturezaOperacao)
admin.site.register(NotaFiscal, NotaFiscalAdmin)
admin.site.register(ItemNotaFiscal, ItemNotaFiscalAdmin)
admin.site.register(TributoICMS)
admin.site.register(TributoIPI)
admin.site.register(TributoPIS)
admin.site.register(TributoCOFINS)