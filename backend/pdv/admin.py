from django.contrib import admin
from .models import Category, Product, Batch, Inventory, PaymentMethod, Sale, SaleItem

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'barcode')
    list_filter = ('category',)
    search_fields = ('name', 'barcode')
    raw_id_fields = ('category',)

class BatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'inclusion_date', 'expiration_date')
    list_filter = ('inclusion_date', 'expiration_date')
    search_fields = ('product__name',)
    date_hierarchy = 'inclusion_date'

class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch', 'quantity')
    list_filter = ('product__category',)
    search_fields = ('product__name', 'batch__id')

class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    raw_id_fields = ('product',)

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale_datetime', 'total_amount', 'payment_method', 'user')
    list_filter = ('sale_datetime', 'payment_method')
    search_fields = ('user__name', 'id')
    date_hierarchy = 'sale_datetime'
    inlines = [SaleItemInline]

# Registre todos os modelos
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(Sale, SaleAdmin)