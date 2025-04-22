from django.http import JsonResponse
from .models import User
from django.utils import timezone
from datetime import timedelta

class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rotas públicas
        public_paths = ['/api/login/', '/admin/', '/api/logout/']
        if any(request.path.startswith(path) for path in public_paths):
            return self.get_response(request)
            
        # Verificação do token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'status': 'error', 'message': 'Token não fornecido'}, status=401)
            
        token = auth_header.split(' ')[1]
        
        try:
            user = User.objects.get(auth_token=token)
            
            if user.token_expires < timezone.now():
                return JsonResponse({'status': 'error', 'message': 'Token expirado'}, status=401)
                
            # Renovação automática (a cada requisição válida)
            user.token_expires = timezone.now() + timedelta(hours=8)
            user.save()
            
            request.user = user
            response = self.get_response(request)
            
            # Adiciona header com novo tempo de expiração
            response['X-Token-Expires'] = user.token_expires.isoformat()
            return response
            
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Token inválido'}, status=401)