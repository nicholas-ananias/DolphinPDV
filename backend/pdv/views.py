from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Sum, F, Count
from datetime import datetime, timedelta
from .models import *
import json
import secrets

# Autenticação
@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(username=username, password=password)
            
            if user:
                token = secrets.token_hex(20)
                expires = timezone.now() + timedelta(hours=8)
                
                user.auth_token = token
                user.token_expires = expires
                user.save()
                
                response = JsonResponse({
                    'status': 'success',
                    'token': token,
                    'expires': expires.isoformat(),
                    'user': {
                        'username': user.username,
                        'name': user.name,
                        'is_admin': user.is_admin
                    }
                })
                
                response['X-Token-Expires'] = expires.isoformat()
                return response
            
            return JsonResponse({'status': 'error', 'message': 'Credenciais inválidas'}, status=401)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
def logout(request):
    if request.method == 'POST':
        try:
            user = request.user
            user.auth_token = None
            user.token_expires = None
            user.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

@csrf_exempt
def check_token(request):
    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'token': request.user.auth_token,
            'expires': request.user.token_expires.isoformat(),
            'user': {
                'username': request.user.username,
                'name': request.user.name,
                'is_admin': request.user.is_admin
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

# Operações de PDV
@csrf_exempt
def get_products(request):
    search = request.GET.get('search', '')
    products = Product.objects.filter(
        name__icontains=search
    ).values('id', 'name', 'price', 'barcode', 'category__name')
    return JsonResponse(list(products), safe=False)

@csrf_exempt
@transaction.atomic
def create_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(username=data['username'])
            
            # Criar a venda
            sale = Sale.objects.create(
                user=user,
                payment_method=PaymentMethod.objects.get(id=data['payment_method_id']),
                discount=data.get('discount', 0),
                addition=data.get('addition', 0),
                total_amount=0  # Será calculado
            )
            
            total = 0
            # Processar cada item
            for item in data['items']:
                product = Product.objects.get(id=item['product_id'])
                unit_price = product.price
                quantity = item['quantity']
                item_total = unit_price * quantity
                
                # Registrar item da venda
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    units=quantity,
                    unit_price=unit_price,
                    total_price=item_total
                )
                
                # Atualizar estoque (FIFO)
                batches = Batch.objects.filter(
                    product=product
                ).order_by('inclusion_date')
                
                remaining = quantity
                for batch in batches:
                    inventory = Inventory.objects.get(product=product, batch=batch)
                    if inventory.quantity >= remaining:
                        inventory.quantity -= remaining
                        inventory.save()
                        break
                    else:
                        remaining -= inventory.quantity
                        inventory.quantity = 0
                        inventory.save()
                
                total += item_total
            
            # Atualizar total da venda
            sale.total_amount = total - sale.discount + sale.addition
            sale.save()
            
            return JsonResponse({
                'status': 'success',
                'sale_id': sale.id,
                'total': sale.total_amount
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

# Gestão de Estoque
@csrf_exempt
def add_batch(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product = Product.objects.get(id=data['product_id'])
            
            # Criar lote
            batch = Batch.objects.create(
                product=product,
                quantity=data['quantity'],
                expiration_date=data.get('expiration_date')
            )
            
            # Criar/atualizar inventário
            inventory, created = Inventory.objects.get_or_create(
                product=product,
                batch=batch,
                defaults={'quantity': data['quantity']}
            )
            
            if not created:
                inventory.quantity += data['quantity']
                inventory.save()
            
            return JsonResponse({'status': 'success', 'batch_id': batch.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

def get_inventory(request):
    product_id = request.GET.get('product_id')
    if product_id:
        inventory = Inventory.objects.filter(
            product_id=product_id,
            quantity__gt=0
        ).values(
            'batch__id',
            'batch__inclusion_date',
            'batch__expiration_date',
            'quantity'
        )
        return JsonResponse(list(inventory), safe=False)
    
    # Resumo geral
    inventory = Product.objects.annotate(
        total_quantity=Sum('inventory__quantity')
    ).filter(
        total_quantity__gt=0
    ).values('id', 'name', 'total_quantity')
    
    return JsonResponse(list(inventory), safe=False)

# Gestão de Produtos
@csrf_exempt
def manage_product(request, product_id=None):
    if request.method == 'GET':
        product = Product.objects.get(id=product_id)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'barcode': product.barcode,
            'category_id': product.category.id
        })
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        if product_id:  # Edição
            product = Product.objects.get(id=product_id)
            product.name = data['name']
            product.price = data['price']
            product.barcode = data.get('barcode')
            product.category_id = data['category_id']
            product.save()
        else:  # Criação
            product = Product.objects.create(
                name=data['name'],
                price=data['price'],
                barcode=data.get('barcode'),
                category_id=data['category_id']
            )
        return JsonResponse({'status': 'success', 'product_id': product.id})
    
    elif request.method == 'DELETE':
        product = Product.objects.get(id=product_id)
        product.delete()
        return JsonResponse({'status': 'success'})

# Relatórios
def sales_report(request):
    date_from = request.GET.get('from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    # Vendas por período
    sales = Sale.objects.filter(
        sale_datetime__date__gte=date_from,
        sale_datetime__date__lte=date_to
    ).values('sale_datetime__date').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('sale_datetime__date')
    
    # Métodos de pagamento
    payment_methods = Sale.objects.filter(
        sale_datetime__date__gte=date_from,
        sale_datetime__date__lte=date_to
    ).values('payment_method__name').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    # Produtos mais vendidos
    top_products = SaleItem.objects.filter(
        sale__sale_datetime__date__gte=date_from,
        sale__sale_datetime__date__lte=date_to
    ).values('product__name').annotate(
        total_units=Sum('units'),
        total_value=Sum('total_price')
    ).order_by('-total_value')[:10]
    
    return JsonResponse({
        'period': {'from': date_from, 'to': date_to},
        'sales_by_date': list(sales),
        'payment_methods': list(payment_methods),
        'top_products': list(top_products)
    })

def inventory_report(request):
    # Produtos com estoque baixo (menos de 10 unidades)
    low_stock = Inventory.objects.values(
        'product__name'
    ).annotate(
        total=Sum('quantity')
    ).filter(
        total__lt=10
    ).order_by('total')
    
    # Produtos próximos de vencer (7 dias)
    expiring = Batch.objects.filter(
        expiration_date__lte=datetime.now().date() + timedelta(days=7),
        expiration_date__gte=datetime.now().date()
    ).values(
        'product__name',
        'expiration_date'
    ).annotate(
        quantity=Sum('inventory__quantity')
    ).order_by('expiration_date')
    
    return JsonResponse({
        'low_stock': list(low_stock),
        'expiring_soon': list(expiring)
    })

# Dados auxiliares
@csrf_exempt
def manage_category(request, category_id=None):
    if request.method == 'GET':
        # Detalhes de uma categoria específica
        category = Category.objects.get(id=category_id)
        return JsonResponse({
            'id': category.id,
            'name': category.name
        })
    
    elif request.method == 'POST':
        # Criar nova categoria
        data = json.loads(request.body)
        category = Category.objects.create(name=data['name'])
        return JsonResponse({
            'status': 'success',
            'category_id': category.id
        })
    
    elif request.method == 'PUT':
        # Atualizar categoria existente
        data = json.loads(request.body)
        category = Category.objects.get(id=category_id)
        category.name = data['name']
        category.save()
        return JsonResponse({
            'status': 'success',
            'category_id': category.id
        })
    
    elif request.method == 'DELETE':
        # Remover categoria (com validação de produtos associados)
        category = Category.objects.get(id=category_id)
        
        if Product.objects.filter(category=category).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Não é possível excluir categoria com produtos associados'
            }, status=400)
            
        category.delete()
        return JsonResponse({'status': 'success'})

@csrf_exempt
def list_categories(request):
    # Listar todas as categorias
    categories = Category.objects.all().values('id', 'name')
    return JsonResponse(list(categories), safe=False)

@csrf_exempt
def manage_payment_method(request, method_id=None):
    if request.method == 'GET':
        # Detalhes de um método específico
        method = PaymentMethod.objects.get(id=method_id)
        return JsonResponse({
            'id': method.id,
            'name': method.name
        })
    
    elif request.method == 'POST':
        # Criar novo método
        data = json.loads(request.body)
        method = PaymentMethod.objects.create(name=data['name'])
        return JsonResponse({
            'status': 'success',
            'method_id': method.id
        })
    
    elif request.method == 'PUT':
        # Atualizar método existente
        data = json.loads(request.body)
        method = PaymentMethod.objects.get(id=method_id)
        method.name = data['name']
        method.save()
        return JsonResponse({
            'status': 'success',
            'method_id': method.id
        })
    
    elif request.method == 'DELETE':
        # Remover método (com validação de vendas associadas)
        method = PaymentMethod.objects.get(id=method_id)
        
        if Sale.objects.filter(payment_method=method).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Não é possível excluir método com vendas associadas'
            }, status=400)
            
        method.delete()
        return JsonResponse({'status': 'success'})

@csrf_exempt
def list_payment_methods(request):
    # Listar todos os métodos
    methods = PaymentMethod.objects.all().values('id', 'name')
    return JsonResponse(list(methods), safe=False)