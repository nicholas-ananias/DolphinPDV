# backend/pdv/middleware.py
import json
from django.http import JsonResponse
from .models import User

class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Se já tem usuário autenticado (via session), não faz nada
        if hasattr(request, 'user') and request.user.is_authenticated:
            return self.get_response(request)
        
        # Verifica o token Bearer apenas para rotas API
        if request.path.startswith('/api/'):
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    request.user = User.objects.get(auth_token=token)
                    request.user.backend = 'django.contrib.auth.backends.ModelBackend'
                    return self.get_response(request)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Token inválido'
                    }, status=401)
        
        return self.get_response(request)