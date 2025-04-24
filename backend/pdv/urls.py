from django.urls import path
from . import views
from .views import logout_view, login

urlpatterns = [
    # Autenticação e token
    path('login/', login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/check/', views.check_token),
    
    # PDV
    path('products/', views.get_products),
    path('sales/create/', views.create_sale),
    
    # Estoque
    path('inventory/', views.get_inventory),
    path('batches/add/', views.add_batch),
    
    # Produtos
    path('products/manage/', views.manage_product),
    path('products/manage/<int:product_id>/', views.manage_product),
    path('products/barcode/', views.product_by_barcode),  # POST
    path('products/barcode/<str:barcode>/', views.product_by_barcode),  # GET, PUT, DELETE
    
    # Relatórios
    path('reports/sales/', views.sales_report),
    path('reports/inventory/', views.inventory_report),
    
    # Auxiliares
    # Categorias
    path('categories/', views.list_categories),
    path('categories/manage/', views.manage_category),  # POST
    path('categories/manage/<int:category_id>/', views.manage_category),  # GET, PUT, DELETE

    # Métodos de Pagamento
    path('payment-methods/', views.list_payment_methods),
    path('payment-methods/manage/', views.manage_payment_method),  # POST
    path('payment-methods/manage/<int:method_id>/', views.manage_payment_method),  # GET, PUT, DELETE
]